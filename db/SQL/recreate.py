import sqlite3


def connect():
    conn = sqlite3.connect('../data.db')
    cursor = conn.cursor()
    return conn, cursor

conn, cursor = connect()

for file in ['delete.sql', 'create.sql']:
    for query in open(file).read().strip().split(';'):
        print(query)
        cursor.execute(query)
