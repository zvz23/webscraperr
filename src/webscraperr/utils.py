from .db import get_db_class_by_config
def load_urls(urls_file: str):
    with open(urls_file, 'r') as f:
        return f.read().split('\n')
    

def save_urls(database_config: dict, urls: list):
    to_save_urls = [[i] for i in urls]
    with get_db_class_by_config(database_config)(database_config) as conn:
        conn.save_urls(to_save_urls)