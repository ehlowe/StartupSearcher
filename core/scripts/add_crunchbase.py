import time
import os
import sys
sys.path.append(os.getcwd())

import dotenv
dotenv.load_dotenv()

import psycopg2
from core.database import models
from core.data_ingestion import crunchbase

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
    create_crunchbase_table(cur)
    load_crunchbase_data(cur)

    cur.close()
    conn.commit()
    conn.close()

def create_crunchbase_table(cur):
    """Creates the crunchbase table in the database"""
    cur.execute("""
    CREATE TABLE IF NOT EXISTS crunchbase (
        {fields}
    );
    """.format(fields=models.dict_to_sql_fields(models.crunchbase_fields)))

def load_crunchbase_data(cur):
    """Loads the crunchbase data into the database"""
    sql_ready_data=crunchbase.raw_database_to_sql_database_converter()

    for row in sql_ready_data:
        if row:
            # Check if the company already exists
            check_query = """
            SELECT COUNT(*) FROM crunchbase WHERE company_name = %s
            """
            cur.execute(check_query, (row['company_name'],))
            if cur.fetchone()[0] == 0:
                # Company doesn't exist, insert the new record
                columns = ', '.join(row.keys())
                placeholders = ', '.join(['%s'] * len(row))
                insert_query = f"""
                INSERT INTO crunchbase ({columns})
                VALUES ({placeholders})
                """
                cur.execute(insert_query, tuple(row.values()))

    print("Crunchbase Data loaded")