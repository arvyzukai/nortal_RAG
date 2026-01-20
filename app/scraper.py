import time
import json
import os
import logging
import re
import requests
from collections import deque
from urllib.parse import urlparse, urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from bs4 import BeautifulSoup

try:
    import fitz  # PyMuPDF
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    logging.warning("PyMuPDF not installed. PDF scraping will be disabled.")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class NortalScraper:
    def __init__(self, start_url="https://nortal.com/", max_pages=10, max_depth=2, 
                 output_dir="data", pdf_output_dir="data/scraped_pdfs", scrape_pdfs=True):
        self.start_url = start_url
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.output_dir = output_dir
        self.pdf_output_dir = pdf_output_dir
        self.scrape_pdfs = scrape_pdfs and PDF_SUPPORT
        self.visited = set()
        self.queue = deque([(start_url, 0)])  # (url, depth)
        self.data = []
        self.pdf_urls = set()  # Track discovered PDF URLs
        
        self.driver = None

    def _init_driver(self):
        selenium_url = os.environ.get('SELENIUM_URL')
        if selenium_url:
            logging.info(f"Connecting to remote Selenium at {selenium_url}")
            options = Options()
            options.add_argument("--headless")
            self.driver = webdriver.Remote(
                command_executor=selenium_url,
                options=options
            )
        else:
            logging.info("Starting local Selenium driver")
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            
            # Use native Selenium Manager (cleaner and more robust)
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
            except Exception as e:
                logging.error(f"Failed to initialize local driver: {e}")
                raise

    def is_valid_url(self, url):
        """Check if URL is a valid nortal.com URL."""
        parsed = urlparse(url)
        return parsed.netloc == "nortal.com" and "#" not in url

    def is_html_url(self, url):
        """Check if URL is an HTML page (not a binary asset)."""
        return not url.lower().endswith(('.jpg', '.png', '.css', '.js', '.gif', '.ico', '.svg', '.woff', '.woff2'))

    def is_pdf_url(self, url):
        """Check if URL is a PDF file."""
        return url.lower().endswith('.pdf')

    def clean_text(self, text):
        """Remove extra whitespace and basic cleanup."""
        if not text:
            return ""
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def extract_content(self, soup):
        """
        Extract content focusing on the 'main' content areas to avoid header/footer/nav.
        """
        # Remove common non-content elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'noscript', 'iframe', 'form', 'button', 'input', 'select', 'textarea']):
            element.decompose()

        # Remove specific noisy classes/ids often found
        for element in soup.find_all(attrs={"class": re.compile(r'cookie|banner|popup|modal|newsletter|subscribe|login|signup')}):
            element.decompose()

        # Try to find the main content article or div
        # Setup specific selectors usually found in modern WP/CMS sites
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|post'))
        
        if main_content:
            text = main_content.get_text(separator=' ')
        else:
            # Fallback to body if no main found
            text = soup.body.get_text(separator=' ') if soup.body else ""
            
        return self.clean_text(text)

    def download_pdf(self, url):
        """
        Download PDF from URL and save to disk.
        
        Returns:
            str: Path to downloaded PDF file, or None if download failed.
        """
        try:
            # Create PDF output directory if needed
            os.makedirs(self.pdf_output_dir, exist_ok=True)
            
            # Generate filename from URL
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path)
            if not filename.endswith('.pdf'):
                filename = f"{hash(url)}.pdf"
            
            # Sanitize filename
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            pdf_path = os.path.join(self.pdf_output_dir, filename)
            
            # Skip if already downloaded
            if os.path.exists(pdf_path):
                logging.info(f"PDF already exists: {pdf_path}")
                return pdf_path
            
            logging.info(f"Downloading PDF: {url}")
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            # Verify it's actually a PDF
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower() and not response.content[:4] == b'%PDF':
                logging.warning(f"URL does not return PDF content: {url}")
                return None
            
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            
            logging.info(f"Downloaded PDF to: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logging.error(f"Failed to download PDF {url}: {e}")
            return None

    def extract_pdf_content(self, pdf_path):
        """
        Extract text content from a PDF file using PyMuPDF.
        
        Returns:
            tuple: (title, content) extracted from the PDF.
        """
        if not PDF_SUPPORT:
            return None, ""
        
        try:
            doc = fitz.open(pdf_path)
            
            # Try to get title from metadata or first heading
            title = doc.metadata.get('title', '')
            if not title:
                # Use filename as fallback
                title = os.path.splitext(os.path.basename(pdf_path))[0]
                title = title.replace('_', ' ').replace('-', ' ').title()
            
            # Extract text from all pages
            text_parts = []
            for page in doc:
                text = page.get_text()
                if text:
                    text_parts.append(text)
            
            doc.close()
            
            content = self.clean_text(' '.join(text_parts))
            return title, content
            
        except Exception as e:
            logging.error(f"Failed to extract content from PDF {pdf_path}: {e}")
            return None, ""

    def scrape(self):
        if not self.driver:
            self._init_driver()
            
        try:
            pages_scraped = 0
            while self.queue and pages_scraped < self.max_pages:
                current_url, depth = self.queue.popleft()
                
                # Normalize URL (strip trailing slash for HTML pages)
                if not self.is_pdf_url(current_url):
                    current_url = current_url.rstrip('/')
                
                if current_url in self.visited:
                    continue
                
                # Check depth early
                if depth > self.max_depth:
                    continue
                
                # Handle PDF URLs separately
                if self.is_pdf_url(current_url):
                    if self.scrape_pdfs:
                        self._process_pdf(current_url)
                    self.visited.add(current_url)
                    continue
                
                # Skip non-HTML URLs
                if not self.is_html_url(current_url):
                    self.visited.add(current_url)
                    continue
                
                logging.info(f"Scraping: {current_url} (Depth: {depth})")
                
                try:
                    self.driver.get(current_url)
                    time.sleep(2) # Basic wait
                    
                    page_source = self.driver.page_source
                    soup = BeautifulSoup(page_source, 'html.parser')
                    
                    content = self.extract_content(soup)
                    title = soup.title.string.strip() if soup.title else current_url
                    
                    # Only save if we found substantial content
                    if len(content) > 100:
                        self.data.append({
                            "url": current_url,
                            "title": title,
                            "content": content,
                            "source_type": "html"
                        })
                        pages_scraped += 1
                    else:
                        logging.warning(f"Skipping {current_url}: Insufficient content found.")

                    self.visited.add(current_url)
                    
                    # Find links for BFS
                    if depth < self.max_depth:
                        links_found = 0
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            full_url = urljoin(current_url, href)
                            
                            # Handle PDF links differently
                            if self.is_pdf_url(full_url):
                                full_url_normalized = full_url  # Don't strip trailing slash for PDFs
                            else:
                                full_url_normalized = full_url.rstrip('/')
                            
                            if self.is_valid_url(full_url_normalized) and full_url_normalized not in self.visited:
                                # Add PDF URLs to a separate set for tracking
                                if self.is_pdf_url(full_url_normalized):
                                    self.pdf_urls.add(full_url_normalized)
                                self.queue.append((full_url_normalized, depth + 1))
                                links_found += 1
                        logging.info(f"Found {links_found} new links on {current_url}")
                                
                except Exception as e:
                    logging.error(f"Failed to scrape {current_url}: {e}")
                    
        finally:
            if self.driver:
                self.driver.quit()
        
        # Log PDF discovery summary
        if self.pdf_urls:
            logging.info(f"Discovered {len(self.pdf_urls)} PDF URLs during crawl")
        
        self.save_data()

    def _process_pdf(self, url):
        """Process a single PDF URL: download and extract content."""
        logging.info(f"Processing PDF: {url}")
        
        pdf_path = self.download_pdf(url)
        if not pdf_path:
            return
        
        title, content = self.extract_pdf_content(pdf_path)
        
        if content and len(content) > 100:
            self.data.append({
                "url": url,
                "title": title or os.path.basename(pdf_path),
                "content": content,
                "source_type": "pdf"
            })
            logging.info(f"Successfully extracted content from PDF: {title}")
        else:
            logging.warning(f"PDF has insufficient content: {url}")

    def save_data(self):
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, "scraped_data.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        
        # Count by source type
        html_count = sum(1 for d in self.data if d.get('source_type') == 'html')
        pdf_count = sum(1 for d in self.data if d.get('source_type') == 'pdf')
        
        logging.info(f"Scraping complete. Saved {len(self.data)} items ({html_count} HTML, {pdf_count} PDF) to {output_path}")


if __name__ == "__main__":
    # Production run with more comprehensive scraping
    scraper = NortalScraper(max_pages=50, max_depth=2)
    scraper.scrape()
