# Module Extractor - User Guide

## Overview
The Module Extractor analyzes documentation websites and extracts their structure into a JSON format showing:
- **Modules**: Top-level sections (e.g., "Account Settings", "Content Sharing")
- **Descriptions**: 1-2 sentence summaries of each module
- **Submodules**: Features, tools, or subsections within each module

## Quick Start

### 1. Open the Streamlit App
```bash
cd d:\SAGAR\pulse-module-extractor
streamlit run app.py
```
The app will open at: `http://localhost:8506`

### 2. Enter a Documentation URL
In the "📌 Documentation URL" input box, paste any documentation URL:
- Instagram Help: `https://help.instagram.com/`
- FastAPI: `https://fastapi.tiangolo.com/`
- Python Docs: `https://docs.python.org/`
- Or any other documentation site

### 3. Click "🚀 Extract Modules"
The app will:
1. Crawl the website
2. Extract content structure
3. Parse modules and submodules
4. Display results in JSON format

## Output Format

The JSON output shows a list of modules:

```json
[
  {
    "module": "Account Settings",
    "Description": "Manage your Instagram account preferences, privacy settings, and security credentials. Learn how to customize your profile and account visibility.",
    "Submodules": {
      "Change Username": "Update your Instagram handle and display name via account settings.",
      "Manage Privacy": "Control who can see your profile, posts, and stories.",
      "Two-Factor Authentication": "Add an extra layer of security to your account."
    }
  },
  {
    "module": "Content Sharing",
    "Description": "Tools and workflows for creating, editing, and publishing content on Instagram.",
    "Submodules": {
      "Creating Reels": "Record, edit, and share short-form video content using Reels.",
      "Tagging Users": "Tag individuals or businesses in posts and stories for engagement."
    }
  }
]
```

## Using AI for Better Extraction

### Option 1: OpenAI (Recommended)
1. Get an API key from: https://platform.openai.com/account/api-keys
2. Edit `.env` and add your key:
   ```
   OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
   OPENAI_MODEL=gpt-4
   ```
3. Restart Streamlit and re-run extraction

### Option 2: Groq (Free, Limited)
1. Get an API key from: https://console.groq.com/
2. Edit `.env`:
   ```
   GROQ_API_KEY=your-groq-api-key-here
   GROQ_MODEL=llama-3.1-70b-stable
   ```
3. Restart Streamlit and re-run extraction

### Option 3: Local Extraction (No Billing)
The app automatically falls back to local rule-based extraction if no AI keys are configured. This works well for structured documentation but may be less detailed than AI extraction.

## Features

### JSON Display
- Shows the complete extraction result in formatted JSON
- Easy to copy and save

### Interactive Module Browser
- Expand each module to see details
- View submodules with descriptions
- Count of submodules shown in header

### Download Results
- Download extracted data as `modules.json`
- Save results for later use or processing

### Crawler Logs
- Optional checkbox to show "Show crawler logs"
- See which pages were crawled and any errors

## Tips

1. **Best Results**: Use OpenAI for high-quality AI-powered extraction
2. **Fast Processing**: Local extraction is instant with no API calls
3. **Complex Sites**: JavaScript-heavy sites (like Instagram) may need AI refinement
4. **Structured Docs**: Well-organized documentation (Python, FastAPI) works great with local extraction
5. **Large Sites**: The crawler respects depth/page limits to avoid timeouts

## Troubleshooting

**"No modules extracted"**
- Check if the URL is accessible in your browser
- Try a different documentation site
- Verify network connection

**"Invalid OpenAI API key"**
- Check that the key in `.env` is correct
- Ensure it's not expired or revoked
- Create a new key in OpenAI Dashboard

**"Groq model not found"**
- Check available models at: https://console.groq.com/docs/models
- Update `GROQ_MODEL` in `.env`
- Or remove the setting to use default fallback list

**"Extraction seems incomplete"**
- Try with a smaller documentation site first
- Check if the site blocks web crawlers
- Use OpenAI for AI-powered extraction instead of local fallback
