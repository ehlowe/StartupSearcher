
import psycopg2
import os
import sys

import dotenv
dotenv.load_dotenv()

sys.path.append(os.getcwd())

from core.database import models, helpers
from core.data_ingestion import crunchbase, industries

def make_table_insert_data():
    """Initializes the database with the necessary tables"""
    conn = psycopg2.connect(
        dbname="startup_database",
        user="postgres",
        password=os.getenv("DB_PASSWORD"),
        host="localhost",
        port="5432"
    )

    cur = conn.cursor()
    create_industry_connections_table(cur)
    raw_industries_data=industries.fetch_industry_data(cur)
    simplified_industries_data=industries.simplify_industry_data(raw_industries_data)
    industries.insert_industry_data(cur, simplified_industries_data)

    cur.close()
    conn.commit()
    conn.close()

def create_industry_connections_table(cur):
    """Creates the industry_connections table in the database"""
    cur.execute("""
    CREATE TABLE IF NOT EXISTS industry_connections (
        {fields}
    );
    """.format(fields=models.dict_to_sql_fields(models.industry_connections_fields)))

