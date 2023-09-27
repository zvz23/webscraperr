from typing import Callable, List, Dict, Union, Tuple
from .db import *
from .exceptions import *
from .driver import get_driver
import requests
import json
import undetected_chromedriver as uc
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains
import time

def config_sleep(seconds: Union[float, None]):
    if seconds is not None:
        time.sleep(seconds)

class WebScraperRequest:
    def __init__(self, config: dict):
        self.config = config
        self.get_items_urls_func : Callable[[requests.Response], List[str]] = None
        self.get_items_urls_and_infos_func: Callable[[requests.Response], List[Tuple[str, Dict]]] = None
        self.get_next_page_func : Callable[[requests.Response], str] = None
        self.parse_info_func : Callable[[requests.Response], Dict] = None
        self.session: requests.Session = None
        self.db_class = get_db_class_by_config(config['DATABASE'])

    def __enter__(self):
        self.session = requests.Session()
        return self
    
    def __exit__(self, type, value, traceback):
        self.session.close()

    def scrape_items_urls(self, urls: list):
        if self.get_items_urls_func is None and self.get_items_urls_and_infos_func is None:
            raise ParserNotSetException()
        for url in urls:
            next_page = url[:]
            while next_page:
                print("SCRAPING URLS ", next_page)
                response = self.session.get(next_page)
                if not response.ok:
                    print("FAILED GETTING URLS ", next_page)
                    continue
                if self.get_items_urls_func:
                    items_urls = [[i] for i in self.get_items_urls_func(response)]
                    if items_urls:
                        with self.db_class(self.config['DATABASE']) as conn:
                            conn.save_urls(items_urls)
                            print(f"FOUND {len(items_urls)} URLS IN", next_page)
                    else:
                        print("NO URLS FOUND IN ", next_page)

                if self.get_items_urls_and_infos_func:
                    items_urls_and_infos = [[i[0], json.dumps(i[1])] for i in self.get_items_urls_and_infos_func(response)]
                    if items_urls_and_infos:
                        with self.db_class(self.config['DATABASE']) as conn:
                            conn.save_url_and_info_many(items_urls_and_infos)
                            print(f"FOUND {len(items_urls_and_infos)} URLS AND INFOS IN ", url)
                    else:
                        print("NO URLS AND INFOS FOUND IN ", url)

                next_page = None
                if self.get_next_page_func:
                    next_page = self.get_next_page_func(response)
                    if next_page:
                        config_sleep(self.config['SCRAPER']['REQUEST_DELAY'])
    
    def scrape_items_infos(self, update=False, items_filter=ItemsFilterByInfo.WITHOUT_INFO):
        if self.parse_info_func is None:
            raise ParserNotSetException()
        items = []
        with self.db_class(self.config['DATABASE']) as conn:
            items = get_items_by_filter(conn, items_filter)
        for item in items:
            print("GETTING INFO ", item['URL'])
            response = self.session.get(item['URL'])
            if not response.ok:
                print("FAILED GETTING INFO ", item['URL'])
                continue
            info = self.parse_info_func(response)
            if info is None:
                print("NO INFO ", item['URL'])
                continue
            with self.db_class(self.config['DATABASE']) as conn:
                if update and item['INFO'] is not None:
                    info.update(json.loads(item['INFO']))
                conn.set_info_by_id(item['ID'], json.dumps(info))
                print("SAVED INFO ", item['URL'])
            config_sleep(self.config['SCRAPER']['REQUEST_DELAY'])

    def scrape_items_infos_key_url(self, key: str, parse_info_func: Callable[[requests.Response], Dict]):
        items = []
        with self.db_class(self.config['DATABASE']) as conn:
            items = conn.get_all_with_info()
            for item in items:
                info = json.loads(item['INFO'])
                if key not in info:
                    print("KEY NOT FOUND IN ", item['URL'])
                    continue
                key_url = info.get(key)
                if key_url is None:
                    print("NO KEY VALUE ", item['URL'])
                    continue                
                print("GETTING KEY INFO ", item['URL'])
                response = self.session.get(key_url)
                if not response.ok:
                    print("FAILED GETTING KEY INFO ", item['URL'])
                    continue
                key_info = parse_info_func(response)
                if key_info is None:
                    print("NO INFO ", key_url)
                    continue
                info.update(key_info)
                with self.db_class(self.config['DATABASE']) as conn:
                    conn.set_info_by_id(item['ID'], json.dumps(info))
                    print("SAVED INFO ", item['URL'])
                config_sleep(self.config['SCRAPER']['REQUEST_DELAY'])

class WebScraperChrome:
    def __init__(self, config: dict):
        self.config = config
        self.get_items_urls_func : Callable[[uc.Chrome], List[str]] = None
        self.get_items_urls_and_infos_func: Callable[[uc.Chrome], List[Tuple[str, Dict]]] = None
        self.get_next_page_func : Callable[[uc.Chrome], Union[str, WebElement]] = None
        self.parse_info_func : Callable[[uc.Chrome], Dict] = None
        self.driver : uc.Chrome = None
        self.db_class = get_db_class_by_config(config['DATABASE'])

    def __enter__(self):
        self.driver = get_driver(self.config['DRIVER'])
        return self
    
    def __exit__(self, type, value, traceback):
        try:
            self.driver.close()
        except:
            print("There was a problem closing the chrome instances. You will need to close them manually")

    def scrape_items_urls(self, urls: list):
        if self.get_items_urls_func is None and self.get_items_urls_and_infos_func is None:
            raise ParserNotSetException()
        
        for url in urls:
            self.driver.get(url)
            config_sleep(self.config['DRIVER']['AFTER_GET_DELAY'])
            while True:
                print("SCRAPING URLS", self.driver.current_url)
                if self.get_items_urls_func:
                    items_urls = [[i] for i in self.get_items_urls_func(self.driver)]
                    if len(items_urls) > 0:
                        with self.db_class(self.config['DATABASE']) as conn:
                            conn.save_urls(items_urls)
                            print(f"FOUND {len(items_urls)} URLS IN", url)
                    else:
                        print("NO URLS FOUND IN ", url)
                
                if self.get_items_urls_and_infos_func:
                    items_urls_and_infos = [[i[0], json.dumps(i[1])] for i in self.get_items_urls_and_infos_func(self.driver)]
                    if len(items_urls_and_infos) > 0:
                        with self.db_class(self.config['DATABASE']) as conn:
                            conn.save_url_and_info_many(items_urls_and_infos)
                            print(f"FOUND {len(items_urls_and_infos)} URLS AND INFOS IN ", url)
                    else:
                        print("NO URLS AND INFOS FOUND IN ", url)

                if self.get_next_page_func:
                    next_page = self.get_next_page_func(self.driver)
                    if isinstance(next_page, str):
                        self.driver.get(next_page)
                        config_sleep(self.config['DRIVER']['AFTER_GET_DELAY'])
                    elif isinstance(next_page, WebElement):
                        ActionChains(self.driver, 500).move_to_element(next_page).pause(0.4).click().perform()
                        time.sleep(2)
                    else:
                        break
                    config_sleep(self.config['SCRAPER']['REQUEST_DELAY'])
                else:
                    break
                            
    def scrape_items_infos(self, update=False, items_filter: ItemsFilterByInfo = ItemsFilterByInfo.WITHOUT_INFO):
        if self.parse_info_func is None:
            raise ParserNotSetException()
        items = []
        with self.db_class(self.config['DATABASE']) as conn:
            items = get_items_by_filter(conn, items_filter)
        for item in items:
            print("GETTING INFO ", item['URL'])
            self.driver.get(item['URL'])
            config_sleep(self.config['DRIVER']['AFTER_GET_DELAY'])
            info = self.parse_info_func(self.driver)
            if info is None:
                print("NO INFO ", item['URL'])
                continue
            with self.db_class(self.config['DATABASE']) as conn:
                if update and item['INFO'] is not None:
                    info.update(json.loads(item['INFO']))
                conn.set_info_by_id(item['ID'], json.dumps(info))
                print("SAVED INFO ", item['URL'])
            config_sleep(self.config['SCRAPER']['REQUEST_DELAY'])

    def scrape_items_infos_key_url(self, key: str, parse_info_func: Callable[[uc.Chrome], Dict]):
        items = []
        with self.db_class(self.config['DATABASE']) as conn:
            items = conn.get_all_with_info()
            for item in items:
                info = json.loads(item['INFO'])
                if key not in info:
                    print("KEY NOT FOUND IN ", item['URL'])
                    continue
                key_url = info.get(key)
                if key_url is None:
                    print("NO KEY VALUE ", item['URL'])
                    continue
                print("GETTING KEY INFO ", item['URL'])
                self.driver.get(key_url)
                config_sleep(self.config['DRIVER']['AFTER_GET_DELAY'])
                key_info = parse_info_func(self.driver)
                if key_info is None:
                    print("NO INFO ", key_url)
                    continue
                info.update(key_info)
                with self.db_class(self.config['DATABASE']) as conn:
                    conn.set_info_by_id(item['ID'], json.dumps(info))
                    print("SAVED INFO ", item['URL'])