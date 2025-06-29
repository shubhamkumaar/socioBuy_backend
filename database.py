from neo4j import GraphDatabase, Session
import config
from functools import lru_cache

@lru_cache
def get_settings():
    return config.Settings()

Settings = get_settings()

driver = GraphDatabase.driver(
    Settings.neo4j_database_uri,
    auth=(Settings.neo4j_username, Settings.neo4j_password))

def neo4j_session() -> Session:
    """
    Provides a Neo4j driver connection.
    """
    session = driver.session()
    try:
        return session
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        raise e
    finally:
        session.close()
    
def get_db():
    """
    Provides a Neo4j database connection.
    """
    with neo4j_session() as session:
        yield session
        