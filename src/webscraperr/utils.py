def load_urls(urls_file: str):
    with open(urls_file, 'r') as f:
        return f.read().split('\n')