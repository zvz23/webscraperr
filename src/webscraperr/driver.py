import os
import sys
import seleniumwire.undetected_chromedriver as uc
    
def get_driver(config: dict):
    driver = None
    if config['OPTIONS']:
        driver = uc.Chrome(options=config['OPTIONS'])
    else:
        options = uc.ChromeOptions()
        options.headless = False
        driver = uc.Chrome(options=options)
    driver.maximize_window()
    return driver