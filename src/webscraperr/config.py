from seleniumwire.undetected_chromedriver import ChromeOptions
from .db import DBTypes

def get_default_config():
    default_config = {
        "DRIVER": {
            "OPTIONS": None,
            "PROFILE_NAME": "Test Profile",
            "AFTER_GET_DELAY": None
        },
        "DATABASE": {
            "TYPE": DBTypes.SQLITE,
            "AUTH": {
                "user": "",
                "password": "",
                "host": "",
                "database": ""
            },
            "TABLE": "items",
            "DATABASE": "",
        },
        "SCRAPER": {
            "REQUEST_DELAY": None
        }
    }
    return default_config

def validate_config(config):
    # Validate DRIVER section
    driver_config = config.get("DRIVER", {})
    if not isinstance(driver_config, dict):
        raise ValueError("Invalid DRIVER configuration")

    if "OPTIONS" in driver_config and driver_config["OPTIONS"] is not None:
        if not isinstance(driver_config["OPTIONS"], ChromeOptions):
            raise ValueError("DRIVER OPTIONS must be an instance of ChromeOptions")
    else:
        driver_config["OPTIONS"] = None

    if "PROFILE_NAME" in driver_config:
        if not isinstance(driver_config["PROFILE_NAME"], str) or not driver_config["PROFILE_NAME"]:
            raise ValueError("DRIVER PROFILE_NAME must be a string")
    else:
        driver_config["PROFILE_NAME"] = "Test Profile"

    if "AFTER_GET_DELAY" in driver_config:
        after_get_delay = driver_config.get('AFTER_GET_DELAY')
        if after_get_delay is not None:
            if type(after_get_delay) not in [int, float]:
                raise ValueError("DRIVER AFTER_GET_DELAY must be an int or float")
            else:
                if after_get_delay <= 0:
                    raise ValueError("DRIVER AFTER_GET_DELAY must be greater than 0")
    else:
        driver_config["AFTER_GET_DELAY"] = None

    # Validate DATABASE section
    database_config = config.get("DATABASE", {})
    if not isinstance(database_config, dict):
        raise ValueError("Invalid DATABASE configuration")

    database_type = database_config.get("TYPE", DBTypes.SQLITE)
    if not isinstance(database_type, DBTypes):
        raise ValueError(f"DATABASE TYPE must be {DBTypes.__name__}")

    if database_type == DBTypes.MYSQL:
        auth = database_config.get("AUTH", {})
        if not isinstance(auth, dict):
            raise ValueError("DATABASE AUTH must be a dictionary")
        required_keys = ["user", "password", "host", "database"]
        for key in required_keys:
            if key not in auth or not auth[key]:
                raise ValueError(f"DATABASE AUTH is missing the '{key}' key")

    database_table = database_config.get("TABLE", "items")
    if not isinstance(database_table, str) or not database_table:
        raise ValueError("DATABASE TABLE must be set")
    database_config["TABLE"] = database_table 

    database_name = database_config.get("DATABASE")
    if not isinstance(database_name, str) or not database_name:
        raise ValueError("DATABASE NAME must be set")

    # Validate SCRAPER section
    scraper_config = config.get("SCRAPER", {})
    if not isinstance(scraper_config, dict):
        raise ValueError("Invalid SCRAPER configuration")

    if "REQUEST_DELAY" in driver_config:
        request_delay = driver_config.get('REQUEST_DELAY')
        if request_delay is not None:
            if type(request_delay) not in [int, float]:
                raise ValueError("SCRAPER REQUEST_DELAY must be an int or float")
            else:
                if request_delay <= 0:
                    raise ValueError("SCRAPER REQUEST_DELAY must be greater than 0")
    else:
        scraper_config["REQUEST_DELAY"] = None

    config["DRIVER"] = driver_config
    config["DATABASE"] = database_config
    config["SCRAPER"] = scraper_config