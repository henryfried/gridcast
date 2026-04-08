"""Shared utilities for data ingestion: DB connections, retries, and data validation helpers."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env.postgres"))
url = os.environ.get("DATABASE_URL")
engine = create_engine(url)


def write_to_db(df, table_name):
    df.to_sql(
    table_name,        # table name as a string
    con=engine,         # the database connection (SQLAlchemy engine)
    if_exists='append',   # what to do if the table already exists
    index=False,       # whether to write the DataFrame index as a column
)