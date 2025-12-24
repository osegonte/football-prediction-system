"""
VPN Manager - Controls NordVPN connection and rotation.
Currently a scaffold - will be implemented when VPN credentials are ready.
"""
import logging
from core.settings import USE_VPN, VPN_ROTATE_AFTER

logger = logging.getLogger(__name__)


class VPNManager:
    """Manages VPN connection and rotation."""
    
    def __init__(self):
        self.enabled = USE_VPN
        self.rotate_after = VPN_ROTATE_AFTER
        self.request_count = 0
        self.current_server = None
        
        if self.enabled:
            logger.info("VPN Manager initialized (VPN ENABLED)")
            # TODO: Add NordVPN connection logic here
        else:
            logger.info("VPN Manager initialized (VPN DISABLED)")
    
    def should_rotate(self) -> bool:
        """Check if it's time to rotate VPN."""
        if not self.enabled:
            return False
        
        return self.request_count >= self.rotate_after
    
    def rotate(self):
        """Rotate to a new VPN server."""
        if not self.enabled:
            logger.debug("VPN rotation skipped (VPN disabled)")
            return
        
        # TODO: Implement NordVPN rotation logic
        logger.info("VPN rotation triggered (not implemented yet)")
        self.request_count = 0
    
    def increment_request(self):
        """Increment request counter."""
        self.request_count += 1
        
        if self.should_rotate():
            self.rotate()
    
    def connect(self):
        """Connect to VPN."""
        if not self.enabled:
            return
        
        # TODO: Implement NordVPN connection
        logger.info("VPN connect triggered (not implemented yet)")
    
    def disconnect(self):
        """Disconnect from VPN."""
        if not self.enabled:
            return
        
        # TODO: Implement NordVPN disconnection
        logger.info("VPN disconnect triggered (not implemented yet)")
