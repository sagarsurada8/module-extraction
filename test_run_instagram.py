from module_extractor import run

if __name__ == '__main__':
    urls = ["https://help.instagram.com/"]
    # Fast settings: shallow crawl, few pages, more chars per page
    run(
        urls=urls,
        max_depth=1,
        max_pages=5,
        chars_per_page=2000,
        batch_size=1
    )
    print("Finished — results written to output/result.json")
