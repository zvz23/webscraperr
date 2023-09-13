
# Webscraperr

This Python library is designed to facilitate the common workflow of web scraping, particularly for e-commerce websites. It provides a structured framework where users can define their own logic for gathering product URLs, parsing individual product pages, and selecting the next page. The URLs and product info are saved directly to a database. It supports various databases such as SQLite and MySQL.




## Installation

Install webscraperr with pip

```bash
    pip install webscraperr
```
    
## Usage

The configurations of the scraper is stored in a config dictionary. The config must be prepared, modified and validated before passing it to the scraper.
```python
from webscraperr.config import get_default_config, validate_config

config = get_default_config()
config['DATABASE']['TYPE'] = 'SQLITE'
config['DATABASE']['DATABASE'] = 'mydatabase.db'
config['DATABASE']['TABLE'] = 'products' # If TABLE is not set "items" will be the defaut table name
config['SCRAPER']['REQUEST_DELAY'] = 1.6

validate_config(config) # Will raise an error if config is not properly set
```

After preparing and validating the config, you must initialize the database

```python
from webscraperr.db import init_sqlite

init_sqlite(config['DATABASE'])

# This will create the database and the table
```

For this example we are going to use `WebScraperRequest`. This scrapper will be using `requests` library for the http requests and `parsel` for parsing the html. You will need to define the functions for parsing the html.


```python
from webscraperr import WebScraperRequest
from urllib.parse import urljoin

urls = ["https://webscraper.io/test-sites/e-commerce/static/computers/tablets"]

def get_next_page_func(selector):
    next_page_url = selector.css('a[rel="next"]::attr(href)').get()
    if next_page_url is not None:
        return urljoin(BASE_URL, next_page_url)
    return None # must return None for the scraper to know that there is no next page

def parse_info_func(selector):
    info = {
        'name': selector.css(".caption h4:nth-child(2)::text").get(),
        'price': selector.css(".caption .price::text").get()
    }
    return info


scraper = WebScraperRequest(config)
scraper.get_items_urls_func = lambda selector : [urljoin(BASE_URL, i) for i in selector.css(".thumbnail a::attr(href)").getall()]
scraper.get_next_page_func = get_next_page_func
scraper.parse_info_func = parse_info_func

scraper.scrape_items_urls(urls) # This will start the scraping of products urls

scraper.scrape_items_infos() # This will navigate to the product page and parse the html

```



## Development Status

Please note that this library is still under development and may be subject to changes. I am constantly working on improving its functionality, flexibility and performance. Your patience, feedback, and contributions are much appreciated.

