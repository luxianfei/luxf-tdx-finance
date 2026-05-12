# database package

MYSQL_AVAILABLE = False
MySQLClient = None
pymysql = None

try:
    import pymysql as _pymysql
    pymysql = _pymysql
    from .mysql_client import MySQLClient
    from .schema import init_database, create_tables
    MYSQL_AVAILABLE = True
    __all__ = ["MySQLClient", "init_database", "create_tables", "MYSQL_AVAILABLE", "pymysql"]
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"MySQL 功能不可用: {e}")
    __all__ = ["MySQLClient", "init_database", "create_tables", "MYSQL_AVAILABLE", "pymysql"]
