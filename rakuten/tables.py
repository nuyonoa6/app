import sqlite3
import os

# データベースファイルのパスを定義
DATABASE = os.path.join(os.path.dirname(__file__), 'database/database.db')

def list_tables():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # すべてのテーブル名を取得
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    if tables:
        print("Tables in the database:")
        for table in tables:
            print(table[0])
    else:
        print("No tables found in the database.")

    conn.close()

if __name__ == "__main__":
    list_tables()
