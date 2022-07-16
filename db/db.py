import sqlite3


def connect():
    conn = sqlite3.connect('db/data.db')
    cursor = conn.cursor()
    return conn, cursor
