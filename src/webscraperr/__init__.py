from typing import Callable, List, Dict, Union, Tuple
from .db import *
from .exceptions import *
from .driver import get_driver
import parsel
import requests
import json
import undetected_chromedriver as uc
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains
import time

class WebScraperRequest:
    def __init__(self, config: dict):
        self.config = config
        self.get_items_urls_func : Callable[[parsel.Selector], List[str]] = None
        self.get_next_page_func : Callable[[parsel.Selector], str] = None
        self.parse_info_func : Callable[[parsel.Selector], Dict] = None
        self.parse_url_and_info_func: Callable[[parsel.Selector], List[Tuple[str, Dict]]] = None
    
    def scrape_items_urls(self, urls: list):
        with requests.Session() as s:
            for url in urls:
                next_page = url[:]
                while next_page:
                    print("SCRAPING URLS", next_page)
                    response = s.get(next_page)
                    if not response.ok:
                        print("FAILED GETTING URLS ", next_page)
                        continue
                    selector = parsel.Selector(text=response.text)
                    items_urls = [[i] for i in self.get_items_urls_func(selector)]
                    if len(items_urls) > 0:
                        with get_db_class_by_config(self.config)(self.config['DATABASE']) as conn:
                            conn.save_urls(items_urls)
                            print(f"FOUND {len(items_urls)} URLS IN", next_page)
                    else:
                        print("NO URLS FOUND IN", next_page)
                    next_page = None
                    if self.get_next_page_func:
                        next_page = self.get_next_page_func(selector)
                        if next_page:
                            time.sleep(self.config['SCRAPER']['REQUEST_DELAY'])
    
    def scrape_items_infos(self):
        items = []
        with get_db_class_by_config(self.config)(self.config['DATABASE']) as conn:
            items = conn.get_all_without_info()
        with requests.Session() as s:
            for item in items:
                print("GETTING INFO ", item['URL'])
                response = s.get(item['URL'])
                if not response.ok:
                    print("FAILED GETTING INFO ", item['URL'])
                    continue
                selector = parsel.Selector(text=response.text)
                info = self.parse_info_func(selector)
                if info is None:
                    print("NO INFO ", item['URL'])
                    continue
                with get_db_class_by_config(self.config)(self.config['DATABASE']) as conn:
                    conn.set_info_by_id(item['ID'], json.dumps(info))
                    print("SAVED INFO ", item['URL'])
                time.sleep(self.config['SCRAPER']['REQUEST_DELAY'])

class WebScraperChrome:
    def __init__(self, config: dict):
        self.config = config
        self.get_items_urls_func : Callable[[uc.Chrome], List[str]] = None
        self.get_next_page_func : Callable[[uc.Chrome], Union[str, WebElement]] = None
        self.parse_info_func : Callable[[uc.Chrome], Dict] = None
        self.parse_url_and_info_func : Callable[[uc.Chrome], List[Tuple[str, Dict]]] = None
        self.driver : uc.Chrome = get_driver(config['DRIVER'])

    def scrape_items_urls(self, urls: list):
        for url in urls:
            self.driver.get(url)
            while True:
                print("SCRAPING URLS", self.driver.current_url)
                items_urls = [[i] for i in self.get_items_urls_func(self.driver)]
                if len(items_urls) > 0:
                    with get_db_class_by_config(self.config)(self.config['DATABASE']) as conn:
                        conn.save_urls(items_urls)
                        print(f"FOUND {len(items_urls)} URLS IN", url)
                else:
                    print("NO URLS FOUND IN", url)
                if self.get_next_page_func:
                    next_page = self.get_next_page_func(self.driver)
                    if isinstance(next_page, str):
                        self.driver.get(next_page)
                    elif isinstance(next_page, WebElement):
                        ActionChains(self.driver, 500).move_to_element(next_page).pause(0.4).click().perform()
                        time.sleep(2)
                    else:
                        break
                    time.sleep(self.config['SCRAPER']['REQUEST_DELAY'])
                else:
                    break
                            
    def scrape_items_infos(self):
        if self.parse_info_func is None:
            raise ParserNotSetException()
        items = []
        with get_db_class_by_config(self.config)(self.config['DATABASE']) as conn:
            items = conn.get_all_without_info()
        for item in items:
            print("GETTING INFO ", item['URL'])
            self.driver.get(item['URL'])
            info = self.parse_info_func(self.driver)
            if info is None:
                print("NO INFO ", item['URL'])
                continue
            with get_db_class_by_config(self.config)(self.config['DATABASE']) as conn:
                conn.set_info_by_id(item['ID'], json.dumps(info))
                print("SAVED INFO ", item['URL'])
            time.sleep(self.config['SCRAPER']['REQUEST_DELAY'])