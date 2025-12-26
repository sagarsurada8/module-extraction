# Documentation Module Extractor

Extract module structure from documentation websites automatically using AI or local rule-based extraction

## Installation

### Prerequisites
- Python 3.8+

### Setup

1. **Clone or navigate to project directory:**
2. **Create virtual environment (optional but recommended):**
3. **Install dependencies:**
4. **Configure API keys (optional for OpenAI):

## Usage

### Option 1: Command-Line Interface

#### Single URL
```bash
python module_extractor.py --urls https://help.instagram.com/
```

#### Multiple URLs
```bash
python module_extractor.py --urls https://fastapi.tiangolo.com/ https://docs.python.org/
```

#### With Custom Options
```bash
python module_extractor.py \
  --urls https://docs.example.com/ \
  --depth 2 \
  --pages 20 \
  --chars 2000 \
  --output my_results.json
```

#### Command-Line Options
```
--urls URLS [URLS ...]      One or more documentation URLs (required)
--depth DEPTH               Maximum crawl depth (default: 1)
--pages PAGES               Maximum pages per URL (default: 10)
--chars CHARS               Characters per page to process (default: 1000)
--output OUTPUT             Output file path (default: output/result.json)
--help                      Show help message
```

### Option 2: Python Function

```python
from module_extractor import run

# Single URL
result = run("https://help.instagram.com/")

# Multiple URLs with options
result = run(
    urls=["https://fastapi.tiangolo.com/", "https://docs.python.org/"],
    max_depth=2,
    max_pages=20,
    chars_per_page=2000
)

# Save results
import json
with open("output.json", "w") as f:
    json.dump(result, f, indent=2)
```

### Option 3: Streamlit Web Interface

```bash
streamlit run app.py
```

Then open your browser to `http://localhost:8506`

1. Enter documentation URL in the input field
2. Click "Extract Modules"
3. View results in JSON format and interactive module browser
4. Download results as JSON file

---

## Output Format

The extraction produces a JSON array of modules:

```json
[
  {
    "module": "Account Settings",
    "Description": "Manage your Instagram account preferences, privacy settings, and security credentials.",
    "Submodules": {
      "Change Username": "Update your Instagram handle and display name.",
      "Manage Privacy": "Control who can see your profile, posts, and stories.",
      "Two-Factor Authentication": "Add extra layer of security to your account."
    }
  },
  {
    "module": "Content Sharing",
    "Description": "Tools and workflows for creating, editing, and publishing content on Instagram.",
    "Submodules": {
      "Creating Reels": "Record, edit, and share short-form video content.",
      "Tagging Users": "Tag individuals or businesses in posts and stories."
    }
  }
]
```

---

## Architecture

### Components

#### 1. **Input Layer** (`crawler/url_validator.py`)
- Validates and normalizes URLs
- Handles protocol detection
- Removes duplicates
- Detailed error reporting

#### 2. **Crawling Layer** (`crawler/crawler.py`)
- Recursive website crawling
- Automatic retry logic with backoff
- Follows redirects
- Filters non-documentation content
- Timeout handling (15s per page)
- Respects same-domain policy
- Content type validation

#### 3. **Content Processing** (`processor/content_extractor.py`)
- HTML parsing with BeautifulSoup
- Smart element removal (headers, footers, nav, sidebars)
- Table extraction and formatting
- List preservation
- Whitespace normalization
- Footer/ad pattern removal

#### 4. **Module Inference** (`ai/module_inference.py`)
- Heading detection (h1-h6, aria-labels, role=heading)
- Smart hierarchy detection
- List item extraction
- Auto-description generation
- Three-tier extraction:
  1. OpenAI GPT-4 (if key available)
  2. Groq LLaMA models (free trials available)
  3. Local rule-based extractor (no billing)

#### 5. **Web UI** (`app.py`)
- Streamlit interface
- Live URL input
- Real-time progress display
- Interactive module browser
- JSON download
- Dark theme

---

## Configuration

### API Keys

Create `.env` file in project root:

```bash
# OpenAI (recommended for quality)
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
OPENAI_MODEL=gpt-4

# Groq (free limited trials)
GROQ_API_KEY=your-groq-key
GROQ_MODEL=llama-3.1-70b-stable
```

### Crawling Parameters

Adjust in command-line or function calls:

```bash
--depth N       # How deep to crawl (1 = same page + direct links)
--pages N       # Max pages per URL (balance between coverage and time)
--chars N       # Chars extracted per page (higher = more context)
```

---

```

---

## Error Handling

### Common Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `No valid URLs provided` | Invalid URL format | Check URL syntax, ensure protocol included |
| `Connection Error` | Website unreachable | Check internet, verify URL is accessible |
| `Timeout` | Page loading took >15s | Try reducing `--pages` or `--depth` |
| `401 Unauthorized` | Invalid OpenAI key | Rotate key in OpenAI Dashboard |
| `No modules extracted` | Page format not recognized | App falls back to local extraction automatically |

### Logging

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Performance Notes

- **Small site** (1-5 pages): 10-30 seconds
- **Medium site** (10-20 pages): 30-120 seconds
- **Large site** (50+ pages): 2-5 minutes

Time depends on:
- Network speed
- Page sizes
- AI service latency (if using OpenAI/Groq)
- System resources



## Project Structure

```
pulse-module-extractor/
├── app.py                          # Streamlit web interface
├── module_extractor.py             # Main CLI & extraction logic
├── requirements.txt                # Python dependencies
├── .env                           # API key configuration
├── USER_GUIDE.md                  # User documentation
├── README.md                      # This file
│
├── crawler/
│   ├── crawler.py                 # Website crawling with retries
│   └── url_validator.py           # URL validation & normalization
│
├── processor/
│   └── content_extractor.py       # HTML parsing & content extraction
│
├── ai/
│   └── module_inference.py        # Module detection & description generation
│
├── output/
│   └── result.json               # Default output location
│
└── test_*.py                      # Test scripts
```

---

## Development

### Adding New Extraction Methods

To add a custom extraction backend:

1. Create function in `ai/module_inference.py`
2. Follow the interface: `def custom_extract(text: str) -> list`
3. Add to fallback chain in `infer_modules()`

### Extending Content Extraction

To improve content extraction for specific sites:

1. Edit `processor/content_extractor.py`
2. Add site-specific CSS selectors or patterns
3. Test with target site

---


```

---

## License

MIT License - Feel free to use and modify for your projects.

---

## Support

For issues or questions:
1. Check the USER_GUIDE.md
2. Review the examples above
3. Check .env configuration
4. Enable logging for debugging
5. Review error messages in console output

---

**Happy Extracting! 📦**
