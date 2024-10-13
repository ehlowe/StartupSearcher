
import psycopg2
import os
import sys
import time

import dotenv
dotenv.load_dotenv()

sys.path.append(os.getcwd())

# database is in a folder below
from core.database import models
from core.data_ingestion import crunchbase
from core.scripts import add_industry_connections, add_crunchbase


def initialize_database():
    """Initializes the database with the necessary tables"""
    add_crunchbase.make_table_insert_data()
    add_industry_connections.make_table_insert_data()


if __name__ == "__main__":
    print("Initializing database")
    initialize_database()
    print("Database initialized")
