from selenium.webdriver.chrome.options import Options

def get_default_config():
    default_config = {
        "DRIVER": {
            "OPTIONS": None,
            "HEADLESS": False,
            "PROFILE_NAME": "Test Profile"
        },
        "DATABASE": {
            "TYPE": "MYSQL",
            "AUTH": {
                "user": "",
                "password": "",
                "host": "",
                "database": ""
            },
            "TABLE": "items",
            "DATABASE": ""
        },
        "SCRAPER": {
            "REQUEST_DELAY": 1.5
        }
    }
    return default_config


def validate_config(config):
    # Validate DRIVER section
    driver_config = config.get("DRIVER", {})
    if not isinstance(driver_config, dict):
        raise ValueError("Invalid DRIVER configuration")

    if "OPTIONS" in driver_config and driver_config["OPTIONS"] is not None:
        if not isinstance(driver_config["OPTIONS"], Options):
            raise ValueError("DRIVER OPTIONS must be an instance of Option")
    else:
        driver_config["OPTIONS"] = None

    if "HEADLESS" in driver_config:
        if not isinstance(driver_config["HEADLESS"], bool):
            raise ValueError("DRIVER HEADLESS must be a boolean")
    else:
        driver_config["HEADLESS"] = False

    if "PROFILE_NAME" in driver_config:
        if not isinstance(driver_config["PROFILE_NAME"], str) or not driver_config["PROFILE_NAME"]:
            raise ValueError("DRIVER PROFILE_NAME must be a string")
    else:
        driver_config["PROFILE_NAME"] = "Test Profile"

    # Validate DATABASE section
    database_config = config.get("DATABASE", {})
    if not isinstance(database_config, dict):
        raise ValueError("Invalid DATABASE configuration")

    database_type = database_config.get("TYPE", "")
    if database_type not in ["MYSQL", "SQLITE"]:
        raise ValueError("DATABASE TYPE must be 'MYSQL' or 'SQLITE'")

    if database_type == "MYSQL":
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

    request_delay = scraper_config.get("REQUEST_DELAY", 1.5)
    if not isinstance(request_delay, (int, float)):
        raise ValueError("SCRAPER REQUEST_DELAY must be a float")
    if request_delay <= 0:
        raise ValueError("SCRAPER REQUEST_DELAY must be greater than 0")

    config["DRIVER"] = driver_config
    config["DATABASE"] = database_config
    config["SCRAPER"] = scraper_config