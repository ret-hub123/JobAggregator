from bs4 import BeautifulSoup
import requests
from abc import ABC, abstractmethod
import logging

class BaseParser(ABC):
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...'
        })
        self.logger = logging.getLogger(__name__)


    def get_response(self, method, url, **kwargs):
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            self.logger.error(f"Request error for {url}: {e}")
            return None

    @abstractmethod
    def parse_vacantions(self, search_params):
        pass






