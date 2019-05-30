from .proxy_config_util import ProxyConfig, parse_os_proxy_config, process_os_proxies
from .constants import *
from .proxy_config_item import *
from .pac_parser import Pac, download_url

# this ensures that we load operating system's
# cert bundles along with those of certifi
from certifi_win32.wincerts import generate_pem
import certifi  # Ensure patch is in place
generate_pem()
