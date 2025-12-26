from module_extractor import run

urls = [
    "https://help.zluri.com/"
]

run(
    urls=urls,
    max_depth=1,
    max_pages=2,
    chars_per_page=800,
    batch_size=1
)
