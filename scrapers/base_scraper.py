import logging
from typing import Optional, Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.request_manager import RequestManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseSofascoreScraper:
    """Base class for all Sofascore scrapers with common functionality."""
    
    def __init__(self):
        self.base_url = "https://api.sofascore.com/api/v1"
        self.request_manager = RequestManager()
        logger.info(f"{self.__class__.__name__} initialized with RequestManager")
        
    def _make_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """
        Make a request using the intelligent RequestManager.
        All anti-ban protections are automatically applied.
        """
        url = f"{self.base_url}{endpoint}"
        return self.request_manager.make_request(url, params=params)
