import re
import requests
import trafilatura
from bs4 import BeautifulSoup
from readability import Document
from langchain_core.tools import tool
from langchain_tavily import TavilySearch

# כלי חיפוש (Tavily)
web_search = TavilySearch(max_results=5)

# כלי סקרייפינג
@tool
def scrape_url(url: str) -> str:
    """
    Scrape and extract clean readable content from a URL.
    Uses robust fetching strategies and fallbacks for high reliability.
    """
    html = None

    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            html = downloaded
    except Exception:
        pass

    if not html:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        try:
            session = requests.Session()
            response = session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            html = response.text
        except Exception as e:
            return f"Could not connect to URL: {str(e)}"

    if not html:
        return "Could not retrieve page content from the URL."

    try:
        extracted = trafilatura.extract(html, include_comments=False, include_tables=False)
        if extracted and len(extracted.strip()) > 200:
            return re.sub(r'\s+', ' ', extracted)[:5000]

        doc = Document(html)
        soup = BeautifulSoup(doc.summary(), "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        if text and len(text.strip()) > 200:
            return re.sub(r'\s+', ' ', text)[:5000]

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()
        cleaned = re.sub(r'\s+', ' ', soup.get_text(separator=" ", strip=True))
        if cleaned:
            return cleaned[:5000]

        return "Could not extract meaningful content from the page."
    except Exception as e:
        return f"Error processing page content: {str(e)}"