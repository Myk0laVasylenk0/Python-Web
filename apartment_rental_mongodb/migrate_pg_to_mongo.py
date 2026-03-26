from sqlalchemy import create_engine, MetaData, Table, select
from pymongo import MongoClient
from datetime import datetime, date
from decimal import Decimal
import uuid


POSTGRES_URL = "postgresql+psycopg2://postgres:123@127.0.0.1:5433/apartment_rental"
MONGO_URL = "mongodb://127.0.0.1:27017/"
MONGO_DB_NAME = "apartment_rental_1"

TABLES_TO_MIGRATE = [
    "cities",
    "landlords",
    "clients",
    "apartments",
    "deals",
]


def convert_value(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


def row_to_dict(row):
    result = {}
    for key, value in row._mapping.items():
        if key == "id":
            result["pg_id"] = convert_value(value)
        else:
            result[key] = convert_value(value)
    return result


def migrate_table(engine, mongo_db, table_name):
    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=engine)

    with engine.connect() as conn:
        rows = conn.execute(select(table)).fetchall()

    documents = [row_to_dict(row) for row in rows]

    collection = mongo_db[table_name]
    collection.delete_many({})

    if documents:
        collection.insert_many(documents)

    print(f"[OK] {table_name}: migrated {len(documents)} rows")


def main():
    engine = create_engine(POSTGRES_URL)
    mongo_client = MongoClient(MONGO_URL)
    mongo_db = mongo_client[MONGO_DB_NAME]

    for table_name in TABLES_TO_MIGRATE:
        migrate_table(engine, mongo_db, table_name)

    print(f"\nDone. Data migrated to MongoDB database: {MONGO_DB_NAME}")


if __name__ == "__main__":
    main()