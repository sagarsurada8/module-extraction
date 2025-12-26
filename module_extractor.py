import os
import json
import sys
import argparse
from crawler.crawler import crawl
from crawler.url_validator import validate_urls
from processor.content_extractor import extract_clean_text
from ai.module_inference import infer_modules
from utils.cache import make_key, get_cached, set_cache

def run(urls, max_depth=1, max_pages=10, chars_per_page=1000, batch_size=1):
    """
    Run the module extraction pipeline.
    
    Args:
        urls: List of URLs or single URL string
        max_depth: Maximum crawl depth
        max_pages: Maximum pages to crawl per URL
        chars_per_page: Characters to extract from each page
        batch_size: Batch size for processing (future enhancement)
    
    Returns:
        List of extracted modules or None on error
    """
    # Ensure urls is a list
    if isinstance(urls, str):
        urls = [urls]
    
    # Validate and normalize all URLs
    urls = validate_urls(urls)
    
    if not urls:
        print("❌ Error: No valid URLs provided")
        return None

    # Check cache for recent results
    cache_key = make_key(urls, max_depth=max_depth, max_pages=max_pages, chars_per_page=chars_per_page)
    cached = get_cached(cache_key)
    if cached:
        print("♻️  Returning cached result")
        return cached
    
    print(f"\n📝 Processing {len(urls)} URL(s)...")
    pages = []

    # Support local files (markdown/pdf) as well as web URLs
    from utils.format_handlers import parse_local_file

    combined_text = ""
    print("\n📄 Processing content...")

    for url in urls:
        # local file path
        local_path = url
        if url.startswith("file://"):
            local_path = url[len("file://"):]
        if os.path.exists(local_path):
            try:
                print(f"📄 Reading local file: {local_path}")
                local_text = parse_local_file(local_path) or ""
                if local_text:
                    combined_text += local_text[:chars_per_page] + "\n"
                continue
            except Exception as e:
                print(f"⚠️  Error reading local file {local_path}: {str(e)}")
                # fall through to attempt web crawl

        try:
            print(f"🔗 Crawling: {url}")
            crawl(url, pages, max_depth=max_depth, max_pages=max_pages)
        except Exception as e:
            print(f"⚠️  Error crawling {url}: {str(e)}")
            continue

    # process crawled pages if any
    if pages:
        print(f"\n✅ Crawled {len(pages)} page(s) total")
        for url, soup in pages:
            try:
                text = extract_clean_text(str(soup))
                combined_text += text[:chars_per_page] + "\n"
            except Exception as e:
                print(f"⚠️  Error processing {url}: {str(e)}")
                continue

    if not combined_text.strip():
        print("❌ Error: No meaningful content extracted")
        return None

    # Infer modules from combined content
    print("\n🧠 Inferring modules...")
    result = infer_modules(combined_text)

    # Add heuristic confidence scores when missing
    try:
        if isinstance(result, list):
            for m in result:
                if 'confidence' not in m and 'Confidence' not in m:
                    desc = m.get('Description','') or ''
                    subs = m.get('Submodules') or {}
                    # heuristic: base + longer description + more submodules
                    base = 0.5
                    desc_bonus = min(len(desc) / 200.0 * 0.2, 0.2)
                    subs_bonus = min(len(subs) / 5.0 * 0.2, 0.2)
                    conf = min(base + desc_bonus + subs_bonus, 0.98)
                    m['confidence'] = round(conf, 2)
    except Exception:
        pass

    # Save to cache (1 day TTL)
    try:
        set_cache(cache_key, result, ttl=86400)
    except Exception:
        pass

    # Save results
    os.makedirs("output", exist_ok=True)
    with open("output/result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("✅ result.json written")
    return result


def main():
    """Command-line interface for module extractor."""
    parser = argparse.ArgumentParser(
        description="Extract module structure from documentation websites",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single URL
  python module_extractor.py --urls https://help.instagram.com/

  # Multiple URLs
  python module_extractor.py --urls https://fastapi.tiangolo.com/ https://docs.python.org/

  # With options
  python module_extractor.py --urls https://docs.example.com/ --depth 2 --pages 20
        """
    )
    
    parser.add_argument(
        "--urls",
        nargs="+",
        required=True,
        help="One or more documentation URLs to process"
    )
    
    parser.add_argument(
        "--depth",
        type=int,
        default=1,
        help="Maximum crawl depth (default: 1)"
    )
    
    parser.add_argument(
        "--pages",
        type=int,
        default=10,
        help="Maximum pages per URL (default: 10)"
    )
    
    parser.add_argument(
        "--chars",
        type=int,
        default=1000,
        help="Characters per page to process (default: 1000)"
    )
    
    parser.add_argument(
        "--output",
        default="output/result.json",
        help="Output file path (default: output/result.json)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("📦 DOCUMENTATION MODULE EXTRACTOR")
    print("=" * 70)
    
    try:
        result = run(
            args.urls,
            max_depth=args.depth,
            max_pages=args.pages,
            chars_per_page=args.chars
        )
        
        if result:
            print("\n" + "=" * 70)
            print(f"✅ SUCCESS: Extracted {len(result)} modules")
            print("=" * 70)
            print("\nResults saved to:", args.output)
            print("\nSample output:")
            if result:
                print(json.dumps(result[:2], indent=2, ensure_ascii=False))
            return 0
        else:
            print("\n" + "=" * 70)
            print("❌ FAILED: Could not extract modules")
            print("=" * 70)
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
