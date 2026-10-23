import sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(ROOT_DIR))

from datetime import datetime
from logs.cmd.setup_logger import get_logger

now = datetime.now().strftime("%Y%m%d_%H%M%S")

LOG_NAME = f"web_page_reader_tool_{now}_log"
logger = get_logger(name=LOG_NAME)


@tool
def read_web_page(url: str) -> str:
    """
    extracts the text content from a web page or specific link.
    """
    logger.info(f"Attempting to read web page from URL: {url}")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        text = soup.get_text(separator=" ", strip=True)
        result = text[:6000] if len(text) > 6000 else text

        logger.info(f"Successfully extracted text from {url} (length: {len(result)} chars)")
        return result
    except Exception as e:
        error_msg = f"ERROR: failed to access {url}: {str(e)}"
        logger.error(error_msg)
        return error_msg
