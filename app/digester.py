"""
LLM-based content digestion using LangChain with Pydantic structured output.
Appends summary and key facts to original content.
"""

import json
import logging
from pathlib import Path

import tiktoken
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MAX_CHUNK_TOKENS = 500
ENCODING = tiktoken.encoding_for_model("gpt-4o")


class DigestedContent(BaseModel):
    """Structured output from LLM digestion."""
    summary: str = Field(description="2-3 sentence summary of the content")
    key_facts: list[str] = Field(description="3-5 single-sentence factual claims")
    topics: list[str] = Field(description="2-5 topic tags (1-3 words each)")


def count_tokens(text: str) -> int:
    return len(ENCODING.encode(text))


def chunk_text(text: str, max_tokens: int = MAX_CHUNK_TOKENS) -> list[str]:
    """Split text into chunks at sentence boundaries."""
    if count_tokens(text) <= max_tokens:
        return [text]
    
    sentences = text.replace('\n', ' ').split('. ')
    chunks, current, tokens = [], [], 0
    
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        s = s if s.endswith('.') else s + '.'
        s_tokens = count_tokens(s)
        
        if tokens + s_tokens > max_tokens and current:
            chunks.append(' '.join(current))
            current, tokens = [s], s_tokens
        else:
            current.append(s)
            tokens += s_tokens
    
    if current:
        chunks.append(' '.join(current))
    return chunks


def create_digester():
    """Create LangChain digester with structured output."""
    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Extract a summary and key facts from the content. Be concise:
- Summary: exactly 2-3 sentences
- Key facts: 3-5 single-sentence facts with specific details
- Topics: 2-5 tags, each 2-3 words"""),
        ("user", "Content from {source_type}:\nTitle: {title}\n\n{content}")
    ])
    
    return prompt | llm.with_structured_output(DigestedContent)


def format_digest(digest: DigestedContent) -> str:
    """Format digest as markdown to append to content."""
    facts = '\n'.join(f"- {f}" for f in digest.key_facts[:5])
    topics = ', '.join(digest.topics[:5])
    return f"\n\n---\n## Summary\n{digest.summary}\n\n## Key Facts\n{facts}\n\n## Topics\n{topics}"


def sample_data(data: list, html_count: int = 20, pdf_count: int = 5) -> tuple[list, dict]:
    """
    Sample data: first N HTML pages and first M PDF pages.
    Returns (sampled_data, sample_info).
    """
    html_pages = [d for d in data if d.get("source_type") == "html"]
    pdf_pages = [d for d in data if d.get("source_type") == "pdf"]
    
    sampled_html = html_pages[:html_count]
    sampled_pdf = pdf_pages[:pdf_count]
    
    sample_info = {
        "total_html": len(html_pages),
        "total_pdf": len(pdf_pages),
        "sampled_html": len(sampled_html),
        "sampled_pdf": len(sampled_pdf),
        "html_urls": [d["url"] for d in sampled_html],
        "pdf_urls": [d["url"] for d in sampled_pdf]
    }
    
    return sampled_html + sampled_pdf, sample_info


def digest_data(
    input_path: str = "data/scraped_data.json",
    output_path: str = "data/llm_digested_data.json",
    sample_html: int | None = None,
    sample_pdf: int | None = None
):
    """Process scraped data: split if needed, digest with LLM, append to original."""
    digester = create_digester()
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Apply sampling if specified
    sample_info = None
    if sample_html is not None or sample_pdf is not None:
        data, sample_info = sample_data(
            data, 
            html_count=sample_html or 0, 
            pdf_count=sample_pdf or 0
        )
        logging.info(f"Sampled {sample_info['sampled_html']} HTML + {sample_info['sampled_pdf']} PDF pages")
        
        # Save sample info
        sample_path = Path(output_path).parent / "sample_info.json"
        with open(sample_path, 'w', encoding='utf-8') as f:
            json.dump(sample_info, f, ensure_ascii=False, indent=2)
        logging.info(f"Sample info saved to {sample_path}")
    
    output = []
    
    for entry in tqdm(data, desc="Digesting"):
        url, title = entry.get("url", ""), entry.get("title", "")
        content, source_type = entry.get("content", ""), entry.get("source_type", "html")
        
        if len(content) < 100:
            continue
        
        chunks = chunk_text(content)
        
        for i, chunk in enumerate(chunks):
            try:
                digest = digester.invoke({
                    "content": chunk,
                    "title": title,
                    "source_type": source_type
                })
                enriched_content = chunk + format_digest(digest)
                
                output.append({
                    "url": url,
                    "title": title,
                    "content": enriched_content,
                    "source_type": source_type
                })
            except Exception as e:
                logging.error(f"Failed to digest {url} chunk {i}: {e}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    logging.info(f"Created {len(output)} digested chunks → {output_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/scraped_data.json")
    parser.add_argument("--output", default="data/llm_digested_data.json")
    parser.add_argument("--sample-html", type=int, default=None, help="Sample N HTML pages")
    parser.add_argument("--sample-pdf", type=int, default=None, help="Sample N PDF pages")
    args = parser.parse_args()
    
    digest_data(args.input, args.output, args.sample_html, args.sample_pdf)
