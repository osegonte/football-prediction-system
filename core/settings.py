"""
Configuration settings for the scraping system.
"""

# ============================================================================
# SCRAPING SETTINGS
# ============================================================================

# Delay between requests (seconds)
MIN_DELAY = 1.0
MAX_DELAY = 3.0

# Request limits
MAX_REQUESTS_PER_MINUTE = 50
MAX_REQUESTS_PER_HOUR = 1000

# Batch processing
BATCH_SIZE = 10  # Process 10 items at a time
BATCH_PAUSE = 120  # Wait 2 minutes between batches (seconds)

# ============================================================================
# TEAM HISTORY SETTINGS
# ============================================================================

DEFAULT_MATCHES_PER_TEAM = 10  # How many past matches to fetch per team

# ============================================================================
# VPN SETTINGS (Optional - Set to True when ready)
# ============================================================================

USE_VPN = False  # Enable VPN rotation
VPN_ROTATE_AFTER = 50  # Rotate VPN every N requests
NORDVPN_USERNAME = ""  # Leave empty for now
NORDVPN_PASSWORD = ""  # Leave empty for now

# ============================================================================
# USER AGENT ROTATION
# ============================================================================

ROTATE_USER_AGENT = True  # Rotate browser signatures
USER_AGENT_ROTATE_AFTER = 10  # Change user agent every N requests

# ============================================================================
# RETRY SETTINGS
# ============================================================================

MAX_RETRIES = 3
RETRY_DELAY = 2.0  # Seconds to wait before retry
EXPONENTIAL_BACKOFF = True  # Increase delay after each retry

# ============================================================================
# LOGGING
# ============================================================================

LOG_REQUESTS = True  # Log all requests
LOG_FILE = "logs/scraper.log"
