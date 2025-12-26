from bs4 import BeautifulSoup
import re

def extract_clean_text(html_content: str) -> str:
    """
    Extract clean, meaningful text from HTML documentation.
    
    Removes:
    - Scripts, styles, metadata
    - Headers, footers, navigation menus
    - Sidebars and ads
    - Social media widgets
    
    Preserves:
    - Document structure and hierarchy
    - Lists and tables
    - Important content areas
    
    Args:
        html_content: Raw HTML string
        
    Returns:
        Cleaned, normalized text with structure
    """
    soup = BeautifulSoup(html_content, "lxml")

    # Remove non-content elements
    unwanted_tags = [
        "script", "style", "meta", "link",      # Metadata & assets
        "footer", "header", "nav", "noscript",   # Navigation
        "[role='navigation']", "[role='banner']", # ARIA nav roles
        "aside",                                  # Sidebars
        ".sidebar", ".nav", ".navigation",       # CSS classes
        ".breadcrumb", ".cookie", ".popup",      # UI elements
    ]
    
    # Remove tags by name
    for tag in soup(["script", "style", "footer", "header", "nav", "noscript", "aside"]):
        tag.decompose()
    
    # Remove by CSS class patterns
    for element in soup.find_all(class_=re.compile(r"(sidebar|nav|menu|breadcrumb|cookie|popup|ad|advertisement)")):
        element.decompose()
    
    # Remove by role attribute
    for element in soup.find_all(attrs={"role": ["navigation", "banner", "contentinfo"]}):
        element.decompose()

    # Extract text while preserving structure
    # Convert tables to readable format
    for table in soup.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = []
            for td in tr.find_all(["td", "th"]):
                cells.append(td.get_text(strip=True))
            if cells:
                rows.append(" | ".join(cells))
        if rows:
            table_text = "\nTable:\n" + "\n".join(rows) + "\n"
            table.replace_with(table_text)

    # Preserve list structure
    for ul in soup.find_all("ul"):
        items = []
        for li in ul.find_all("li", recursive=False):
            items.append("• " + li.get_text(strip=True))
        list_text = "\n" + "\n".join(items) + "\n"
        ul.replace_with(list_text)
    
    for ol in soup.find_all("ol"):
        items = []
        for i, li in enumerate(ol.find_all("li", recursive=False), 1):
            items.append(f"{i}. " + li.get_text(strip=True))
        list_text = "\n" + "\n".join(items) + "\n"
        ol.replace_with(list_text)

    # Get text with proper separation
    text = soup.get_text(separator="\n")
    
    # Normalize whitespace
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            # Skip common low-value patterns
            if not re.match(r"^(copyright|©|privacy|terms|cookie|advertisement|ads|share|follow|subscribe)", line, re.I):
                lines.append(line)
    
    text = "\n".join(lines)
    
    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    return text
