import os
import sys
import seleniumwire.undetected_chromedriver as uc
    
def get_driver(config: dict):
    profile_path = os.path.join(os.path.expanduser('~'), 'Chrome Profiles', config['PROFILE_NAME'])
    driver = None
    if config['OPTIONS']:
        driver = uc.Chrome(options=config['OPTIONS'], user_data_dir=profile_path)
    else:
        driver = uc.Chrome(user_data_dir=profile_path)
    driver.maximize_window()
    return driver