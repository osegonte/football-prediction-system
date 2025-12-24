"""
Request Manager - Handles intelligent request distribution with delays,
user agent rotation, and VPN management.
"""
import time
import random
import logging
from typing import Optional, Dict
import requests

from core.settings import (
    MIN_DELAY, MAX_DELAY, MAX_RETRIES, RETRY_DELAY, 
    EXPONENTIAL_BACKOFF, ROTATE_USER_AGENT, USER_AGENT_ROTATE_AFTER
)
from core.user_agent_manager import UserAgentManager
from core.vpn_manager import VPNManager

logger = logging.getLogger(__name__)


class RequestManager:
    """
    Manages all HTTP requests with intelligent rate limiting,
    user agent rotation, and VPN management.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.user_agent_manager = UserAgentManager()
        self.vpn_manager = VPNManager()
        
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        
        # Set initial headers
        self._update_headers()
        
        logger.info("RequestManager initialized")
    
    def _update_headers(self):
        """Update session headers with new user agent."""
        headers = self.user_agent_manager.get_headers()
        self.session.headers.update(headers)
        logger.debug("Headers updated with new user agent")
    
    def _smart_delay(self):
        """Apply random delay between requests to appear human."""
        delay = random.uniform(MIN_DELAY, MAX_DELAY)
        logger.debug(f"Applying delay: {delay:.2f} seconds")
        time.sleep(delay)
    
    def _should_rotate_user_agent(self) -> bool:
        """Check if it's time to rotate user agent."""
        if not ROTATE_USER_AGENT:
            return False
        return self.total_requests % USER_AGENT_ROTATE_AFTER == 0
    
    def make_request(self, url: str, params: dict = None, max_retries: int = MAX_RETRIES) -> Optional[dict]:
        """
        Make a smart HTTP request with all protections enabled.
        
        Args:
            url: Full URL to request
            params: Optional query parameters
            max_retries: Maximum number of retry attempts
            
        Returns:
            JSON response data or None if failed
        """
        # Apply smart delay before request
        self._smart_delay()
        
        # Rotate user agent if needed
        if self._should_rotate_user_agent():
            self._update_headers()
        
        # Check VPN rotation
        self.vpn_manager.increment_request()
        
        # Attempt request with retries
        for attempt in range(max_retries):
            try:
                self.total_requests += 1
                
                logger.debug(f"Making request {self.total_requests} to {url}")
                response = self.session.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    self.successful_requests += 1
                    logger.debug(f"Request successful (Total: {self.successful_requests}/{self.total_requests})")
                    return response.json()
                    
                elif response.status_code == 429:
                    # Rate limited - wait longer
                    wait_time = RETRY_DELAY * (2 ** attempt) if EXPONENTIAL_BACKOFF else RETRY_DELAY * 3
                    logger.warning(f"Rate limited (429). Waiting {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                    
                else:
                    logger.error(f"Request failed with status {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error on attempt {attempt + 1}/{max_retries}: {e}")
                
                if attempt < max_retries - 1:
                    wait_time = RETRY_DELAY * (2 ** attempt) if EXPONENTIAL_BACKOFF else RETRY_DELAY
                    logger.info(f"Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
        
        # All retries failed
        self.failed_requests += 1
        logger.error(f"Request failed after {max_retries} attempts")
        return None
    
    def get_stats(self) -> Dict:
        """Get request statistics."""
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0
        }
    
    def print_stats(self):
        """Print request statistics."""
        stats = self.get_stats()
        print(f"\n{'='*50}")
        print(f"REQUEST STATISTICS")
        print(f"{'='*50}")
        print(f"Total Requests:      {stats['total_requests']}")
        print(f"Successful:          {stats['successful_requests']}")
        print(f"Failed:              {stats['failed_requests']}")
        print(f"Success Rate:        {stats['success_rate']:.1f}%")
        print(f"{'='*50}\n")
