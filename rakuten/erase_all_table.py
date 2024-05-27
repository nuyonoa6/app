import sqlite3
import os

# データベースファイルのパスを定義
DATABASE = os.path.join(os.path.dirname(__file__), 'database.db')

def clear_database():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # すべてのテーブル名を取得
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    # すべてのテーブルを削除
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
        print(f"Table {table[0]} dropped.")

    conn.commit()
    conn.close()
    print("Database cleared.")

if __name__ == "__main__":
    clear_database()
