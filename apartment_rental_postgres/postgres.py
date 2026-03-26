

import psycopg2
conn = psycopg2.connect(dbname="postgres", user="postgres", password="123", host="127.0.0.1", port="5433")
cursor = conn.cursor()
conn.autocommit = True
# команда для створення бази даних metanit
sql = "CREATE DATABASE apartment_rental"
# виконуємо код sql
cursor.execute(sql)
print("База даних успішно створена")
cursor.close()
conn.close()