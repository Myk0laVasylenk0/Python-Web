from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.orm import sessionmaker

# SQLite database path
SQLITE_URL = "sqlite:///C:/Users/admin/Desktop/Web/apartment_rental/rental.db"

# PostgreSQL connection
POSTGRES_URL = "postgresql+psycopg2://postgres:123@127.0.0.1:5433/apartment_rental"

# Create engines
sqlite_engine = create_engine(SQLITE_URL)
postgres_engine = create_engine(POSTGRES_URL)

sqlite_metadata = MetaData()
sqlite_metadata.reflect(bind=sqlite_engine)

postgres_metadata = MetaData()

def map_sqlite_to_postgres_type(column):
    col_type = str(column.type).lower()

    if "integer" in col_type:
        return "INTEGER"
    elif "varchar" in col_type or "text" in col_type:
        return "TEXT"
    elif "float" in col_type or "real" in col_type:
        return "DOUBLE PRECISION"
    elif "numeric" in col_type or "decimal" in col_type:
        return "NUMERIC"
    elif "boolean" in col_type:
        return "BOOLEAN"
    else:
        return "TEXT"

with postgres_engine.begin() as conn:
    for table_name, table in sqlite_metadata.tables.items():
        column_defs = []
        pk_columns = []

        for col in table.columns:
            col_def = f'"{col.name}" {map_sqlite_to_postgres_type(col)}'
            if not col.nullable:
                col_def += " NOT NULL"
            column_defs.append(col_def)

            if col.primary_key:
                pk_columns.append(col.name)

        pk_sql = ""
        if pk_columns:
            pk_sql = f", PRIMARY KEY ({', '.join([f'\"{c}\"' for c in pk_columns])})"

        create_sql = f'''
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            {", ".join(column_defs)}
            {pk_sql}
        )
        '''

        conn.execute(text(create_sql))
        print(f"Created table: {table_name}")

# Copy data
sqlite_conn = sqlite_engine.connect()
postgres_conn = postgres_engine.connect()
trans = postgres_conn.begin()

try:
    for table_name, table in sqlite_metadata.tables.items():
        rows = sqlite_conn.execute(table.select()).mappings().all()

        if rows:
            for row in rows:
                columns = ', '.join([f'"{k}"' for k in row.keys()])
                placeholders = ', '.join([f':{k}' for k in row.keys()])
                insert_sql = text(
                    f'INSERT INTO "{table_name}" ({columns}) VALUES ({placeholders})'
                )
                postgres_conn.execute(insert_sql, row)

            print(f"Migrated {len(rows)} rows from {table_name}")
        else:
            print(f"No data in {table_name}")

    trans.commit()
    print("Migration completed successfully.")

except Exception as e:
    trans.rollback()
    print("Migration failed:", e)

finally:
    sqlite_conn.close()
    postgres_conn.close()