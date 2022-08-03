import sqlite3
import psycopg2
import os
from pathlib import Path
from db.db import connect


"""
ниже мы закоментили вариант 1 - запуска stand_alone скриптов
"""
# from sys import path
# from pathlib import Path
#
# path.append(str(Path(__file__).parent.parent))
# print(path)
#
# from db import connect


if __name__ == '__main__':
    conn, cursor = connect()

    for file in ['delete.sql', 'create.sql']:
        for query in open(Path('db').joinpath('SQL').joinpath(file)).read().strip().split(';'):
            print(query)
            if query != '':
                cursor.execute(query)

        conn.commit()
