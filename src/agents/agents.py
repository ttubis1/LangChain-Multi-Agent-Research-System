import re
import requests
import trafilatura
from bs4 import BeautifulSoup
from readability import Document

from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

# שימוש בחבילה המעודכנת של Tavily בהתאם לאזהרה
from langchain_tavily import TavilySearch

# שימוש ב-LangGraph prebuilt agent
from langgraph.prebuilt import create_react_agent

# אתחול המודל
llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

# ──────────────────────────────────────────────────────────
# כלי סגראפינג משופר (Scraper Tool)
# ──────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────
# בניית Search Agent ו-Reader Agent (תיקון prompt ו-Tavily)
# ──────────────────────────────────────────────────────────
def build_search_agent():
    # שימוש ב-TavilySearch המעודכן (יש לוודא הרצת pip install -U langchain-tavily אם נדרש)
    tools = [TavilySearch(max_results=5)]
    system_prompt = "You are an expert web researcher. Find recent, reliable and detailed sources."
    # שימוש בארגומנט 'prompt' התקין בגרסאות LangGraph העדכניות
    return create_react_agent(llm, tools, prompt=system_prompt)

def build_reader_agent():
    tools = [scrape_url]
    system_prompt = "You are an expert web reader. Pick the best URL from search results and scrape it."
    return create_react_agent(llm, tools, prompt=system_prompt)


# ──────────────────────────────────────────────────────────
# Writer Chain
# ──────────────────────────────────────────────────────────
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Be detailed, factual and professional."""),
])

writer_chain = writer_prompt | llm | StrOutputParser()


# ──────────────────────────────────────────────────────────
# Critic Chain
# ──────────────────────────────────────────────────────────
critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

critic_chain = critic_prompt | llm | StrOutputParser()


# ──────────────────────────────────────────────────────────
# Refiner Chain
# ──────────────────────────────────────────────────────────
refiner_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Your task is to rewrite and improve the research report based on the critic's feedback."),
    ("human", """Here is the original research report on the topic: "{topic}"

Original Report:
{report}

Critic's Feedback & Areas to Improve:
{critic_feedback}

Please rewrite the report to address all of the critic's points (add historical context, deeper analysis, and more academic rigor where requested). Keep the structured format (Introduction, Key Findings, Conclusion, Sources).""")
])

refiner_chain = refiner_prompt | llm | StrOutputParser()