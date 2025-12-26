from urllib.parse import urlparse
import re

def validate_urls(urls):
    """
    Validate and normalize a list of URLs.
    
    Features:
    - Accepts single URL or list of URLs
    - Adds https:// if missing
    - Removes duplicates
    - Filters out invalid formats
    - Provides detailed error feedback
    
    Args:
        urls (str or list): Single URL or list of URLs

    Returns:
        list: List of valid, unique, normalized URLs
        
    Raises:
        ValueError: If no valid URLs provided
    """
    # Handle single URL string
    if isinstance(urls, str):
        urls = [urls]
    
    # Ensure it's a list
    if not isinstance(urls, (list, tuple)):
        raise ValueError("URLs must be a string or list of strings")
    
    valid_urls = []
    seen = set()  # Track duplicates
    errors = []

    for url in urls:
        if not url:
            continue
            
        url = url.strip()
        
        if not url:
            continue

        # Prepend https:// if missing protocol
        if not url.startswith(("http://", "https://", "ftp://")):
            # Basic format check
            if "." not in url:
                errors.append(f"Invalid: '{url}' - no domain specified")
                continue
            url = "https://" + url

        try:
            # Parse and validate
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in ("http", "https", "ftp"):
                errors.append(f"Invalid: '{url}' - unsupported protocol '{parsed.scheme}'")
                continue
            
            # Check netloc (domain)
            if not parsed.netloc:
                errors.append(f"Invalid: '{url}' - no domain found")
                continue
            
            # Check for basic domain format
            if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', parsed.netloc):
                errors.append(f"Invalid: '{url}' - malformed domain '{parsed.netloc}'")
                continue
            
            # Avoid duplicates
            if url in seen:
                continue
            
            seen.add(url)
            valid_urls.append(url)
            
        except Exception as e:
            errors.append(f"Invalid: '{url}' - {str(e)}")
            continue

    # Report errors if any
    if errors:
        for error in errors:
            print(f"⚠️  {error}")
    
    if not valid_urls:
        raise ValueError(f"No valid URLs found. Errors: {'; '.join(errors)}")
    
    return valid_urls
    return valid_urls

