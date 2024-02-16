import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Retrieve environment variables using appropriate keys and set default values
db_user = os.getenv('DB_USER')
db_pw = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

# Construct the connection string
conn_str = f'postgresql://{db_user}:{db_pw}@{db_host}:{db_port}/{db_name}'

def get_db_conn():
    # Establish and return a database connection
    conn = psycopg2.connect(conn_str)
    conn.autocommit = True
    return conn