import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun

web_search = DuckDuckGoSearchRun()

@tool
def read_web_page(url: str) -> str:
    """Extrai e lê o conteúdo de texto de uma página Web ou link específico."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
            
        texto = soup.get_text(separator=' ', strip=True)
        return texto[:6000] if len(texto) > 6000 else texto
    except Exception as e:
        return f"Erro ao acessar {url}: {str(e)}"