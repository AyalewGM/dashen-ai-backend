from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from bs4 import BeautifulSoup
from langchain_community.document_loaders import RecursiveUrlLoader


# Bank-specific seed URLs for RAG
BANK_SEED_URLS: dict[str, list[str]] = {
    "dashen": [
        "https://www.dashenbanksc.com/how-to-transfer-money-using-dashen-mobile-plus/",
        "https://www.dashenbanksc.com/how-to-use-an-atm/",
        "https://www.dashenbanksc.com/privacy-and-security/",
        "https://www.dashenbanksc.com/frequently-asked-questions/",
        "https://www.dashenbanksc.com/how-to-transfer-money-from-abroad/",
        "https://www.dashenbanksc.com/about-us/",
        "https://www.dashenbanksc.com/",
    ],
    "abyssinia": [
        "https://bankofabyssinia.com/",
        "https://bankofabyssinia.com/about-us/",
        "https://bankofabyssinia.com/services/",
        "https://bankofabyssinia.com/digital-banking/",
    ],
    "awash": [
        "https://awashbank.com/",
        "https://awashbank.com/about/",
        "https://awashbank.com/services/",
        "https://awashbank.com/digital-services/",
    ],
    "cbe": [
        "https://combanketh.et/",
        "https://combanketh.et/about-us/",
        "https://combanketh.et/services/",
        "https://combanketh.et/digital-banking/",
    ],
    "amhara": [
        "https://amharabank.com.et/",
        "https://amharabank.com.et/about/",
        "https://amharabank.com.et/services/",
        "https://amharabank.com.et/products/",
    ],
    "zemen": [
        "https://zemenbank.com/",
        "https://zemenbank.com/about-us/",
        "https://zemenbank.com/personal-banking/",
        "https://zemenbank.com/digital-banking/",
    ],
    "tsedey": [
        "https://tsedeybank.com.et/",
        "https://tsedeybank.com.et/about/",
        "https://tsedeybank.com.et/services/",
        "https://tsedeybank.com.et/products/",
    ],
    "nib": [
        "https://nibbanksc.com/",
        "https://nibbanksc.com/about-us/",
        "https://nibbanksc.com/personal-banking/",
        "https://nibbanksc.com/international-banking/",
    ],
}

# Backward compatibility
DASHEN_SEED_URLS: list[str] = BANK_SEED_URLS["dashen"]

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


def load_bank_public_pages(bank_id: str = "dashen", urls: Iterable[str] | None = None) -> List[RawDocument]:
    """Crawl a bounded portion of a bank's public site using LangChain RecursiveUrlLoader.
    
    Args:
        bank_id: Bank identifier (dashen, abyssinia, awash, cbe)
        urls: Optional custom URLs to crawl. If None, uses bank-specific defaults.
    """
    if urls is not None:
        seed_urls = list(urls)
    else:
        seed_urls = BANK_SEED_URLS.get(bank_id, BANK_SEED_URLS["dashen"])
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


def load_dashen_public_pages(urls: Iterable[str] | None = None) -> List[RawDocument]:
    """Backward compatibility wrapper for loading Dashen Bank pages."""
    return load_bank_public_pages(bank_id="dashen", urls=urls)
