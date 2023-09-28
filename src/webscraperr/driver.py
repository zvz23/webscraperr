import os
import sys
import seleniumwire.undetected_chromedriver as uc
    
def get_driver(config: dict):
    profile_path = get_profile_path(config['PROFILE_NAME'])
    driver = None
    if config['OPTIONS']:
        driver = uc.Chrome(options=config['OPTIONS'], user_data_dir=profile_path)
    else:
        driver = uc.Chrome(user_data_dir=profile_path)
    driver.maximize_window()
    return driver

def get_profile_path(profile_name: str):
    profile_path = None
    if sys.platform == 'linux' or sys.platform == 'linux2':
        profile_path = os.path.expanduser('~/.config/google-chrome', profile_name)
    elif sys.platform == 'win32' or sys.platform == 'win64':
        profile_path = os.path.join(os.getenv('LOCALAPPDATA'), 'Google', 'Chrome', 'User Data', profile_name)
    elif sys.platform == 'darwin':
        profile_path = os.path.expanduser('~/Library/Application Support/Google/Chrome', profile_name)
    return profile_path