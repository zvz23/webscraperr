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
import csv

class ExportMixin:
    def export_to_csv(self):
        items = []
        with get_db_class_by_config(self.config['DATABASE'])(self.config['DATABASE']) as conn:
            items = conn.get_all()
        if len(items) > 0:
            headers = ['url']
            headers.extend(json.loads(items[0]['INFO']).keys())
            with open(self.config['EXPORT']['FILENAME'], 'w', encoding='utf-8', newline='') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=headers)
                writer.writeheader()
                for item in items:
                    base_row = {'url': item['URL']}
                    info_json_obj = json.loads(item['INFO'])
                    rows = []
                    if isinstance(info_json_obj, dict):
                        temp_row = base_row.copy()
                        temp_row.update(info_json_obj)
                        rows.append(temp_row)
                    elif isinstance(info_json_obj, list):
                        for i in info_json_obj:
                            if isinstance(i, dict):
                                temp_row = base_row.copy()
                                temp_row.update(i)
                                rows.append(temp_row)
                    writer.writerows(rows)
                print(f"DATA EXPORTED TO {self.config['EXPORT']['FILENAME']}")

    def export_to_json(self):
        items = []
        with get_db_class_by_config(self.config['DATABASE'])(self.config['DATABASE']) as conn:
            items = conn.get_all()
        if len(items) > 0:
            with open(self.config['EXPORT']['FILENAME'], 'w', encoding='utf-8') as json_file:
                items_rows = []
                for item in items:
                    row = {'url': item['URL']}
                    row.update(json.loads(item['INFO']))
                    items_rows.append(row)
                json.dump(items_rows, json_file)
                print(f"DATA EXPORTED TO {self.config['EXPORT']['FILENAME']}")


class WebScraperRequest(ExportMixin):
    def __init__(self, config: dict):
        self.config = config
        self.get_items_urls_func : Callable[[requests.Response], List[str]] = None
        self.get_items_urls_and_infos_func: Callable[[requests.Response], List[Tuple[str, Dict]]] = None
        self.get_next_page_func : Callable[[requests.Response], str] = None
        self.parse_info_func : Callable[[requests.Response], Dict] = None
        self.session: requests.Session = None

    def __enter__(self):
        self.session = requests.Session()
        return self
    
    def __exit__(self, type, value, traceback):
        self.session.close()

    def scrape_items_urls(self, urls: list):
        if self.get_items_urls_func is None and self.get_items_urls_and_infos_func is None:
            raise ParserNotSetException()
        with requests.Session() as s:
            for url in urls:
                next_page = url[:]
                while next_page:
                    print("SCRAPING URLS ", next_page)
                    response = s.get(next_page)
                    if not response.ok:
                        print("FAILED GETTING URLS ", next_page)
                        continue
                    db_class = get_db_class_by_config(self.config['DATABASE'])
                    if self.get_items_urls_func:
                        items_urls = [[i] for i in self.get_items_urls_func(response)]
                        if items_urls:
                            with db_class(self.config['DATABASE']) as conn:
                                conn.save_urls(items_urls)
                                print(f"FOUND {len(items_urls)} URLS IN", next_page)
                        else:
                            print("NO URLS FOUND IN ", next_page)

                    if self.get_items_urls_and_infos_func:
                        items_urls_and_infos = [[i[0], json.dumps(i[1])] for i in self.get_items_urls_and_infos_func(response)]
                        if items_urls_and_infos:
                            with db_class(self.config['DATABASE']) as conn:
                                conn.save_url_and_info_many(items_urls_and_infos)
                                print(f"FOUND {len(items_urls_and_infos)} URLS AND INFOS IN ", url)
                        else:
                            print("NO URLS AND INFOS FOUND IN ", url)

                    next_page = None
                    if self.get_next_page_func:
                        next_page = self.get_next_page_func(response)
                        if next_page:
                            time.sleep(self.config['SCRAPER']['REQUEST_DELAY'])
    
    def scrape_items_infos(self):
        if self.parse_info_func is None:
            raise ParserNotSetException()
        
        items = []
        with get_db_class_by_config(self.config['DATABASE'])(self.config['DATABASE']) as conn:
            items = conn.get_all_without_info()
        with requests.Session() as s:
            for item in items:
                print("GETTING INFO ", item['URL'])
                response = s.get(item['URL'])
                if not response.ok:
                    print("FAILED GETTING INFO ", item['URL'])
                    continue
                info = self.parse_info_func(response)
                if info:
                    print("NO INFO ", item['URL'])
                    continue
                with get_db_class_by_config(self.config['DATABASE'])(self.config['DATABASE']) as conn:
                    if self.config['DATABASE']['UPDATE_INFO'] and item['INFO'] is not None:
                        info.update(json.loads(item['INFO']))
                    conn.set_info_by_id(item['ID'], json.dumps(info))
                    print("SAVED INFO ", item['URL'])
                time.sleep(self.config['SCRAPER']['REQUEST_DELAY'])

class WebScraperChrome(ExportMixin):
    def __init__(self, config: dict):
        self.config = config
        self.get_items_urls_func : Callable[[uc.Chrome], List[str]] = None
        self.get_items_urls_and_infos_func: Callable[[uc.Chrome], List[Tuple[str, Dict]]] = None
        self.get_next_page_func : Callable[[uc.Chrome], Union[str, WebElement]] = None
        self.parse_info_func : Callable[[uc.Chrome], Dict] = None
        self.driver : uc.Chrome = None

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
            if self.config['DRIVER']['AFTER_GET_DELAY']:
                time.sleep(self.config['DRIVER']['AFTER_GET_DELAY'])
            while True:
                print("SCRAPING URLS", self.driver.current_url)
                db_class = get_db_class_by_config(self.config['DATABASE'])
                if self.get_items_urls_func:
                    items_urls = [[i] for i in self.get_items_urls_func(self.driver)]
                    if len(items_urls) > 0:
                        with db_class(self.config['DATABASE']) as conn:
                            conn.save_urls(items_urls)
                            print(f"FOUND {len(items_urls)} URLS IN", url)
                    else:
                        print("NO URLS FOUND IN ", url)
                
                if self.get_items_urls_and_infos_func:
                    items_urls_and_infos = [[i[0], json.dumps(i[1])] for i in self.get_items_urls_and_infos_func(self.driver)]
                    if len(items_urls_and_infos) > 0:
                        with db_class(self.config['DATABASE']) as conn:
                            conn.save_url_and_info_many(items_urls_and_infos)
                            print(f"FOUND {len(items_urls_and_infos)} URLS AND INFOS IN ", url)
                    else:
                        print("NO URLS AND INFOS FOUND IN ", url)

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
        with get_db_class_by_config(self.config['DATABASE'])(self.config['DATABASE']) as conn:
            items = conn.get_all_without_info()
        for item in items:
            print("GETTING INFO ", item['URL'])
            self.driver.get(item['URL'])
            if self.config['DRIVER']['AFTER_GET_DELAY']:
                time.sleep(self.config['DRIVER']['AFTER_GET_DELAY'])
            info = self.parse_info_func(self.driver)
            if info is None:
                print("NO INFO ", item['URL'])
                continue
            with get_db_class_by_config(self.config['DATABASE'])(self.config['DATABASE']) as conn:
                if self.config['DATABASE']['UPDATE_INFO'] and item['INFO'] is not None:
                    info.update(json.loads(item['INFO']))
                conn.set_info_by_id(item['ID'], json.dumps(info))
                print("SAVED INFO ", item['URL'])
            time.sleep(self.config['SCRAPER']['REQUEST_DELAY'])