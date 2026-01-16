import time
import json
import os
import logging
import re
from collections import deque
from urllib.parse import urlparse, urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NortalScraper:
    def __init__(self, start_url="https://nortal.com/", max_pages=10, max_depth=2, output_dir="data"):
        self.start_url = start_url
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.output_dir = output_dir
        self.visited = set()
        self.queue = deque([(start_url, 0)])  # (url, depth)
        self.data = []
        
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
            # Use webdriver_manager to automatically handle driver installation
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def is_valid_url(self, url):
        parsed = urlparse(url)
        return parsed.netloc == "nortal.com" and not "#" in url and not url.lower().endswith(('.pdf', '.jpg', '.png', '.css', '.js'))

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

    def scrape(self):
        if not self.driver:
            self._init_driver()
            
        try:
            pages_scraped = 0
            while self.queue and pages_scraped < self.max_pages:
                current_url, depth = self.queue.popleft()
                
                # Normalize URL (strip trailing slash)
                current_url = current_url.rstrip('/')
                
                if current_url in self.visited:
                    continue
                
                # Check depth early
                if depth > self.max_depth:
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
                            "content": content
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
                            full_url = urljoin(current_url, href).rstrip('/')
                            
                            if self.is_valid_url(full_url) and full_url not in self.visited:
                                self.queue.append((full_url, depth + 1))
                                links_found += 1
                        logging.info(f"Found {links_found} new links on {current_url}")
                                
                except Exception as e:
                    logging.error(f"Failed to scrape {current_url}: {e}")
                    
        finally:
            if self.driver:
                self.driver.quit()
        
        self.save_data()

    def save_data(self):
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, "scraped_data.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        logging.info(f"Scraping complete. Saved {len(self.data)} pages to {output_path}")

if __name__ == "__main__":
    # Production run with more comprehensive scraping
    scraper = NortalScraper(max_pages=50, max_depth=2)
    scraper.scrape()
