import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_session_with_retries(retries=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504]):
    """Create a requests session with automatic retry logic."""
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["GET", "HEAD"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def is_documentation_url(url: str, domain: str) -> bool:
    """Check if URL is likely documentation content (not download, image, etc)."""
    url_lower = url.lower()
    
    # Skip binary/media files
    skip_extensions = [
        '.pdf', '.zip', '.tar', '.gz', '.exe', '.msi',
        '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg',
        '.mp4', '.webm', '.mp3', '.wav', '.flac',
        '.json', '.xml', '.csv',
    ]
    
    for ext in skip_extensions:
        if url_lower.endswith(ext):
            return False
    
    # Skip common non-content pages
    skip_patterns = ['logout', 'login', 'register', 'account', 'cart', 'checkout', 'download']
    for pattern in skip_patterns:
        if pattern in url_lower:
            return False
    
    # Check same domain
    return urlparse(url).netloc == domain

def crawl(url, pages=None, visited=None, depth=0, max_depth=1, max_pages=5):
    """
    Recursively crawl a website and collect HTML content with robust error handling.

    Args:
        url (str): URL to start crawling from.
        pages (list): List to store tuples (url, BeautifulSoup object)
        visited (set): Set of already visited URLs
        depth (int): Current recursion depth
        max_depth (int): Maximum crawl depth
        max_pages (int): Maximum number of pages to crawl
        
    Returns:
        list: List of crawled pages (url, BeautifulSoup object)
    """
    if pages is None:
        pages = []
    if visited is None:
        visited = set()

    domain = urlparse(url).netloc
    
    # Stop conditions
    if depth > max_depth or url in visited or len(pages) >= max_pages:
        return pages

    visited.add(url)

    # User agent to mimic browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    session = create_session_with_retries()
    
    try:
        # Fetch with timeout and follow redirects
        res = session.get(
            url,
            timeout=15,
            headers=headers,
            allow_redirects=True,
            verify=True
        )
        
        # Check response status
        if res.status_code == 404:
            logger.warning(f"[404 Not Found] {url}")
            return pages
        
        res.raise_for_status()
        
        # Check content type
        content_type = res.headers.get('content-type', '').lower()
        if 'text/html' not in content_type:
            logger.info(f"[Skipped] Non-HTML content: {url}")
            return pages
        
        # Check if page is too small (likely not documentation)
        if len(res.text) < 100:
            logger.info(f"[Skipped] Page too small: {url}")
            return pages
        
        soup = BeautifulSoup(res.text, "lxml")
        pages.append((url, soup))
        logger.info(f"[OK] Crawled ({len(pages)}): {url}")

        # Crawl internal links
        for link in soup.find_all("a", href=True):
            if len(pages) >= max_pages:
                break
            
            full_url = urljoin(url, link["href"])
            
            # Remove URL fragments
            full_url = full_url.split('#')[0]
            
            # Check if URL is valid and not visited
            if is_documentation_url(full_url, domain) and full_url not in visited:
                crawl(full_url, pages, visited, depth + 1, max_depth, max_pages)

    except requests.exceptions.Timeout:
        logger.error(f"[Timeout] {url} (took > 15s)")
    except requests.exceptions.ConnectionError:
        logger.error(f"[Connection Error] {url} - cannot reach host")
    except requests.exceptions.HTTPError as e:
        logger.error(f"[HTTP Error] {url}: {e.response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"[Request Error] {url}: {str(e)}")
    except Exception as e:
        logger.error(f"[Unexpected Error] {url}: {str(e)}")

    return pages

