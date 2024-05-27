import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(__file__), 'database', 'database.db')

def main():
    try:
        # データベースに接続
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # すべてのテーブル名を取得
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        if not tables:
            print("No tables found in the database.")
            return

        # 各テーブルの最初の5行を表示
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 2")
            rows = cursor.fetchall()

            if not rows:
                print("No data found.")
            else:
                # カラム名を表示
                col_names = [description[0] for description in cursor.description]
                print(f"Columns: {col_names}")

                for row in rows:
                    print(row)

        conn.close()
        print("Database connection closed.")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == '__main__':
    main()
