from typing import Callable, List, Dict, Union, Tuple
from .db import *
from .exceptions import *
from .driver import get_driver
import requests
import json
import seleniumwire.undetected_chromedriver as uc
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains
import time
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)

logger.addHandler(stream_handler)

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
                logger.info("SCRAPING URLS %s", next_page)
                response = self.session.get(next_page)
                config_sleep(self.config['SCRAPER']['REQUEST_DELAY'])
                if not response.ok:
                    logger.error("FETCH FAILED %s", next_page)
                    continue
                if self.get_items_urls_func:
                    items_urls = [[i] for i in self.get_items_urls_func(response)]
                    if items_urls:
                        with self.db_class(self.config['DATABASE']) as conn:
                            conn.save_urls(items_urls)
                            logger.info("FOUND %d URLS IN %s", len(items_urls), next_page)
                    else:
                        logger.info("NO URLS FOUND IN %s", next_page)

                if self.get_items_urls_and_infos_func:
                    items_urls_and_infos = [[i[0], json.dumps(i[1])] for i in self.get_items_urls_and_infos_func(response)]
                    if items_urls_and_infos:
                        with self.db_class(self.config['DATABASE']) as conn:
                            conn.save_url_and_info_many(items_urls_and_infos)
                            logger.info("FOUND %d URLS AND INFOS IN %s", len(items_urls_and_infos), next_page)
                    else:
                        logger.info("NO URLS AND INFOS FOUND IN %s", next_page)

                next_page = None
                if self.get_next_page_func:
                    logger.info("GOING TO NEXT PAGE %s", next_page)
                    next_page = self.get_next_page_func(response)                      
    
    def scrape_items_infos(self, update=False, items_filter=ItemsFilterByInfo.WITHOUT_INFO):
        if self.parse_info_func is None:
            raise ParserNotSetException()
        items = []
        with self.db_class(self.config['DATABASE']) as conn:
            items = get_items_by_filter(conn, items_filter)
        for item in items:
            logger.info("GETTING INFO %s", item['URL'])
            response = self.session.get(item['URL'])
            config_sleep(self.config['SCRAPER']['REQUEST_DELAY'])
            if not response.ok:
                logger.error("FETCH FAILED %s", item['URL'])
                continue
            info = self.parse_info_func(response)
            if info is None:
                logger.info("NO INFO %s", item['URL'])
                continue
            with self.db_class(self.config['DATABASE']) as conn:
                if update and item['INFO'] is not None:
                    info.update(json.loads(item['INFO']))
                conn.set_info_by_id(item['ID'], json.dumps(info))
                logger.info("INFO SAVED %s", item['URL'])

    def scrape_items_infos_key_url(self, key: str, parse_info_func: Callable[[requests.Response], Dict]):
        items = []
        with self.db_class(self.config['DATABASE']) as conn:
            items = conn.get_all_with_info()
            for item in items:
                info = json.loads(item['INFO'])
                if key not in info:
                    logger.error("KEY NOT FOUND IN %s", item['URL'])
                    continue
                key_url = info.get(key)
                if key_url is None:
                    logger.error("NO KEY VALUE %s", item['URL'])
                    continue                
                logger.info("GETTING KEY INFO %s", item['URL'])
                response = self.session.get(key_url)
                config_sleep(self.config['SCRAPER']['REQUEST_DELAY'])
                if not response.ok:
                    logger.error("FETCH FAILED %s", key_url)
                    continue
                key_info = parse_info_func(response)
                if key_info is None:
                    logger.info("NO INFO %s", key_url)
                    continue
                info.update(key_info)
                with self.db_class(self.config['DATABASE']) as conn:
                    conn.set_info_by_id(item['ID'], json.dumps(info))
                    logger.info("INFO SAVED %s", item['URL'])

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
            logger.error("There was a problem closing the chrome instances. You will need to close them manually")

    def scrape_items_urls(self, urls: list):
        if self.get_items_urls_func is None and self.get_items_urls_and_infos_func is None:
            raise ParserNotSetException()
        
        for url in urls:
            logger.info("SCRAPING URLS %s", url)
            self.driver.get(url)
            while True:
                config_sleep(self.config['DRIVER']['AFTER_GET_DELAY'])
                if self.get_items_urls_func:
                    items_urls = [[i] for i in self.get_items_urls_func(self.driver)]
                    if len(items_urls) > 0:
                        with self.db_class(self.config['DATABASE']) as conn:
                            conn.save_urls(items_urls)
                            logger.info("FOUND %d URLS IN %s", len(items_urls), self.driver.current_url)
                    else:
                        logger.info("NO URLS FOUND IN %s", url)
                
                if self.get_items_urls_and_infos_func:
                    items_urls_and_infos = [[i[0], json.dumps(i[1])] for i in self.get_items_urls_and_infos_func(self.driver)]
                    if len(items_urls_and_infos) > 0:
                        with self.db_class(self.config['DATABASE']) as conn:
                            conn.save_url_and_info_many(items_urls_and_infos)
                            logger.info("FOUND %d URLS AND INFOS IN %s", len(items_urls_and_infos), url)
                    else:
                        logger.info("NO URLS AND INFOS FOUND IN %s", url)

                if self.get_next_page_func:
                    next_page = self.get_next_page_func(self.driver)
                    if isinstance(next_page, str):
                        logger.info("GOING TO NEXT PAGE %s", next_page)
                        self.driver.get(next_page)
                    elif isinstance(next_page, WebElement):
                        logger.info("GOING TO NEXT PAGE ELEMENT %s", next_page.tag_name)
                        ActionChains(self.driver, 500).move_to_element(next_page).pause(0.5).click().perform()
                    else:
                        break
                else:
                    break
                            
    def scrape_items_infos(self, update=False, items_filter: ItemsFilterByInfo = ItemsFilterByInfo.WITHOUT_INFO):
        if self.parse_info_func is None:
            raise ParserNotSetException()
        items = []
        with self.db_class(self.config['DATABASE']) as conn:
            items = get_items_by_filter(conn, items_filter)
        for item in items:
            logger.info("GETTING INFO %s", item['URL'])
            self.driver.get(item['URL'])
            config_sleep(self.config['DRIVER']['AFTER_GET_DELAY'])
            info = self.parse_info_func(self.driver)
            if info is None:
                logger.info("NO INFO %s", item['URL'])
                continue
            with self.db_class(self.config['DATABASE']) as conn:
                if update and item['INFO'] is not None:
                    info.update(json.loads(item['INFO']))
                conn.set_info_by_id(item['ID'], json.dumps(info))
                logger.info("INFO SAVED %s", item['URL'])

    def scrape_items_infos_key_url(self, key: str, parse_info_func: Callable[[uc.Chrome], Dict]):
        items = []
        with self.db_class(self.config['DATABASE']) as conn:
            items = conn.get_all_with_info()
            for item in items:
                info = json.loads(item['INFO'])
                if key not in info:
                    logger.error("KEY NOT FOUND IN %s", item['URL'])
                    continue
                key_url = info.get(key)
                if key_url is None:
                    logger.error("NO KEY VALUE %s", item['URL'])
                    continue
                logger.info("GETTING KEY INFO %s", key_url)
                self.driver.get(key_url)
                config_sleep(self.config['DRIVER']['AFTER_GET_DELAY'])
                key_info = parse_info_func(self.driver)
                if key_info is None:
                    logger.info("NO INFO %s", key_url)
                    continue
                info.update(key_info)
                with self.db_class(self.config['DATABASE']) as conn:
                    conn.set_info_by_id(item['ID'], json.dumps(info))
                    logger.info("INFO SAVED %s", item['URL'])