import sqlite3
from mysql.connector import connect

def get_db_class_by_config(database_config: dict):
    if database_config['TYPE'] == 'MYSQL':
        return WebScraperDBMySQL
    elif database_config['TYPE'] == 'SQLITE':
        return WebScraperDBSqlite

def init_mysql(database_config: dict):
    temp_auth = database_config['AUTH'].copy()
    if 'database' in temp_auth:
        del temp_auth['database']
    with connect(**temp_auth) as conn:
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_config['DATABASE']}")

    with connect(**database_config['AUTH']) as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS`{database_config['DATABASE']}`.`{database_config['TABLE']}` (
            `ID` INT NOT NULL AUTO_INCREMENT,
            `URL` VARCHAR(255) NOT NULL,
            `INFO` JSON NULL,
            PRIMARY KEY (`ID`),
            UNIQUE INDEX `URL_UNIQUE` (`URL` ASC) VISIBLE);
        """)

def init_sqlite(database_config: dict):
    with sqlite3.connect(database_config['DATABASE']) as conn:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {database_config['TABLE']} (
        ID   INTEGER NOT NULL
                    PRIMARY KEY AUTOINCREMENT,
        URL  TEXT    NOT NULL
                    UNIQUE,
        INFO TEXT
        );
    """)

class WebScraperDBSqlite:
    def __init__(self, config):
        self.config = config
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.config['DATABASE'])
        self.cursor = self.conn.cursor()
        self.cursor.row_factory = sqlite3.Row
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.commit()
            self.conn.close()

    def get_all(self):
        self.cursor.execute(f"SELECT * FROM {self.config['TABLE']}")
        return self.cursor.fetchall()

    def get_all_without_info(self):
        self.cursor.execute(f"SELECT * FROM {self.config['TABLE']} WHERE INFO IS NULL")
        return self.cursor.fetchall()
    
    def get_all_with_info(self):
        self.cursor.execute(f"SELECT * FROM {self.config['TABLE']} WHERE INFO IS NOT NULL")
        return self.cursor.fetchall()
    
    def get_by_id(self, id: int):
        self.cursor.execute(f"SELECT * FROM {self.config['TABLE']} WHERE ID=?", [id])
        return self.cursor.fetchone()

    def get_by_url(self, url: int):
        self.cursor.execute(f"SELECT * FROM {self.config['TABLE']} WHERE URL=?", [url])
        return self.cursor.fetchone()

    def save_url(self, url: str):
        self.cursor.execute(f"INSERT OR IGNORE INTO {self.config['TABLE']}(URL) VALUES(?)", [url])

    def save_urls(self, urls: list):
        self.cursor.executemany(f"INSERT OR IGNORE INTO {self.config['TABLE']}(URL) VALUES(?)", urls)

    def save_url_and_info(self, url: str, info: str):
        self.cursor.execute(f"INSERT OR IGNORE INTO {self.config['TABLE']}(URL, INFO) VALUES(?, ?)", [url, info])

    def save_url_and_info_many(self, datas: list):
        self.cursor.executemany(f"INSERT OR IGNORE INTO {self.config['TABLE']}(URL, INFO) VALUES(?, ?)", datas)

    def set_info_by_id(self, id: int, info: str):
        self.cursor.execute(f"UPDATE {self.config['TABLE']} SET INFO=? WHERE ID=?", [info, id])
    
    def set_info_by_url(self, url: str, info: str):
        self.cursor.execute(f"UPDATE {self.config['TABLE']} SET INFO=? WHERE URL=?", [info, url])

    def clear_database(self):
        self.cursor.execute(f"DELETE FROM {self.config['TABLE']}")

class WebScraperDBMySQL:
    def __init__(self, config: dict):
        self.config = config
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = connect(**self.config['AUTH'])
        self.cursor = self.conn.cursor(dictionary=True)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.commit()
            self.conn.close()
    
    def get_all(self):
        self.cursor.execute(f"SELECT * FROM {self.config['TABLE']}")
        return self.cursor.fetchall()
    
    def get_all_without_info(self):
        self.cursor.execute(f"SELECT * FROM {self.config['TABLE']} WHERE INFO IS NULL")
        return self.cursor.fetchall()
    
    def get_all_with_info(self):
        self.cursor.execute(f"SELECT * FROM {self.config['TABLE']} WHERE INFO IS NOT NULL")
        return self.cursor.fetchall()
    
    def get_by_url(self, url: str):
        self.cursor.execute(f"SELECT * FROM {self.config['TABLE']} WHERE URL=%s", (url, ))
        return self.cursor.fetchone()

    def get_by_id(self, id: int):
        self.cursor.execute(f"SELECT * FROM {self.config['TABLE']} WHERE ID=%s", (id, ))
        return self.cursor.fetchone()

    def save_url(self, url: str):
        self.cursor.execute(f"INSERT IGNORE INTO {self.config['TABLE']}(URL) VALUES(%s)", (url,))
    
    def save_urls(self, urls: str):
        self.cursor.executemany(f"INSERT IGNORE INTO {self.config['TABLE']}(URL) VALUES(%s)", urls)
    
    def save_url_and_info(self, url: str, info: str):
        self.cursor.execute(f"INSERT IGNORE INTO {self.config['TABLE']}(URL, INFO) VALUES(%s, %s)", (url, info))

    def save_url_and_info_many(self, datas: list):
        self.cursor.executemany(f"INSERT IGNORE INTO {self.config['TABLE']}(URL, INFO) VALUES(%s, %s)", datas)

    def set_info_by_id(self, id: int, info: str):
        self.cursor.execute(f"UPDATE {self.config['TABLE']} SET INFO=%s WHERE ID=%s", (info, id))

    def set_info_by_url(self, url: str, info: str):
        self.cursor.execute(f"UPDATE {self.config['TABLE']} SET INFO=%s WHERE URL=%s", (info, url))
    
    def clear_database(self):
        self.cursor.execute(f"DELETE FROM {self.config['TABLE']}")
