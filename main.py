from dotenv import load_dotenv
load_dotenv()  # טוען אוטומטית את המשתנים מקובץ ה-.env

from src.tools.tools import web_search, scrape_url
from src.pipelines.pipeline import run_research_pipeline

topic = "which stock within the nasdaqhas the best analysts forecast ?"
run_research_pipeline(topic)