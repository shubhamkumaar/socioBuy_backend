from neo4j import GraphDatabase
import config
from functools import lru_cache

@lru_cache
def get_settings():
    return config.Settings()

Settings = get_settings()

driver = GraphDatabase.driver(
    Settings.neo4j_database_uri,
    auth=(Settings.neo4j_username, Settings.neo4j_password)
)

def get_db():

    session = driver.session()
    try:
        yield session
    finally:
        session.close()

def close_driver():
    driver.close()