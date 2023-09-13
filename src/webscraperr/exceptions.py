class DatabaseNotSetException(Exception):
    def __init__(self, message="Database connection not set."):
        super().__init__(message)

class DatabaseAuthenticationNotSet(Exception):
    def __init__(self, message="Database authentication not properly set."):
        super().__init__(message)

class DatabaseNotSupportedException(Exception):
    def __init__(self, message="Database type is not supported. Use MYSQL OR SQLITE."):
        super().__init__(message)

class ParserNotSetException(Exception):
    def __init__(self, message="Webscraper parser not set."):
        super().__init__(message)