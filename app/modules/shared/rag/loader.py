from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from bs4 import BeautifulSoup
from langchain_community.document_loaders import RecursiveUrlLoader


DASHEN_SEED_URLS: list[str] = [
    "https://www.dashenbanksc.com/how-to-transfer-money-using-dashen-mobile-plus/",
    "https://www.dashenbanksc.com/how-to-use-an-atm/",
    "https://www.dashenbanksc.com/privacy-and-security/",
    "https://www.dashenbanksc.com/frequently-asked-questions/",
    "https://www.dashenbanksc.com/how-to-transfer-money-from-abroad/",
    "https://www.dashenbanksc.com/about-us/",
    "https://www.dashenbanksc.com/",
]

MAX_PAGES = 200
MAX_DEPTH = 3


@dataclass
class RawDocument:
    url: str
    text: str


def _html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # 1. Remove standard noise tags
    noise_tags = [
        "script", "style", "noscript", "header", "footer", "nav", "aside",
        "form", "iframe", "svg", "button", "input"
    ]
    for tag in soup(noise_tags):
        tag.decompose()

    # 2. Remove elements by common noise classes/IDs (heuristics)
    noise_selectors = [
        ".cookie-notice", ".cookie-banner", "#cookie-banner",
        ".sidebar", "#sidebar", ".menu", ".navigation", ".footer"
    ]
    for selector in noise_selectors:
        for tag in soup.select(selector):
            tag.decompose()

    # 3. Try to narrow down to main content
    #    Dashen site likely uses <main>, <article>, or specific divs like .entry-content
    content_area = (
        soup.find("main") or 
        soup.find("article") or 
        soup.find(class_="entry-content") or 
        soup.find(class_="post-content") or
        soup
    )

    text = content_area.get_text(separator="\n")
    
    # 4. Clean up whitespace
    lines = [line.strip() for line in text.splitlines()]
    # Remove short/empty lines to reduce fragmentation
    lines = [line for line in lines if len(line) > 1]
    
    return "\n".join(lines)


def load_dashen_public_pages(urls: Iterable[str] | None = None) -> List[RawDocument]:
    """Crawl a bounded portion of Dashen's public site using LangChain RecursiveUrlLoader."""

    seed_urls = list(urls) if urls is not None else DASHEN_SEED_URLS
    docs: list[RawDocument] = []
    
    # Track visited URLs to avoid duplicates across seeds
    visited_urls = set()

    for url in seed_urls:
        try:
            loader = RecursiveUrlLoader(
                url=url,
                max_depth=MAX_DEPTH,
                extractor=_html_to_text,
                # Prevent aggressive crawling
                use_async=False, 
                timeout=30,
                # Skip common non-content paths for WordPress sites
                exclude_dirs=[
                    "https://dashenbanksc.com/wp-json/", 
                    "https://dashenbanksc.com/xmlrpc.php",
                    "https://dashenbanksc.com/feed/",
                    "https://dashenbanksc.com/comments/feed/",
                ]
            )
            lc_docs = loader.load()
            
            for d in lc_docs:
                source = d.metadata.get("source", "")
                if source in visited_urls:
                    continue
                visited_urls.add(source)
                
                # Filter out empty docs
                if d.page_content.strip():
                    docs.append(RawDocument(url=source, text=d.page_content))
                    
                if len(docs) >= MAX_PAGES:
                    break
        except Exception:
            # If one seed fails, continue to others
            continue
            
        if len(docs) >= MAX_PAGES:
            break

    return docs
