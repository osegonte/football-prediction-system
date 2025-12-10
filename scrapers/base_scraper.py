import requests
import time
import logging
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseSofascoreScraper:
    """Base class for all Sofascore scrapers with common functionality."""
    
    def __init__(self, delay: float = 1.0):
        self.base_url = "https://api.sofascore.com/api/v1"
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.sofascore.com/',
            'Cache-Control': 'no-cache',
        })
        
    def _make_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Make a request with error handling and retry logic."""
        url = f"{self.base_url}{endpoint}"
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                time.sleep(self.delay)
                response = self.session.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    logger.warning(f"Rate limited, waiting {self.delay * 3} seconds...")
                    time.sleep(self.delay * 3)
                else:
                    logger.error(f"Request failed with status {response.status_code} for {endpoint}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error for {endpoint}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(self.delay * 2)
                    
        return None
