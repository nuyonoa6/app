import pandas as pd
import sqlite3
import os
import re
from datetime import datetime

# 現在の日付に基づいてCSVディレクトリのパスを生成
today = datetime.today().strftime('%Y%m%d')
csv_directory = f'output/{today}'
db_directory = 'database'
db_file_path = os.path.join(db_directory, 'database.db')

# データベースディレクトリが存在しない場合は作成
if not os.path.exists(db_directory):
    os.makedirs(db_directory)

# データベースに接続
conn = sqlite3.connect(db_file_path)

# CSVディレクトリ内のすべてのCSVファイルを処理
for filename in os.listdir(csv_directory):
    if filename.endswith('.csv'):
        csv_file_path = os.path.join(csv_directory, filename)
        try:
            df = pd.read_csv(csv_file_path)
            if df.empty:
                print(f"Skipped {filename} because it is empty.")
                continue
        except pd.errors.EmptyDataError:
            print(f"Skipped {filename} because it contains no data.")
            continue

        # JANコードが存在する商品のみをフィルタリング
        df = df[df['janCode'].notna() & (df['janCode'] != '')]
        
        if df.empty:
            print(f"Skipped {filename} because it contains no items with a valid JAN code.")
            continue
        
        # テーブル名を空白（半角および全角）をアンダースコアに変換して生成
        table_name = re.sub(r'\s+', '_', os.path.splitext(filename)[0])
        
        try:
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            print(f"Saved {filename} to table {table_name}")
        except Exception as e:
            print(f"Error saving {filename} to table {table_name}: {e}")

# すべてのテーブル名を取得して表示
def list_tables(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    if tables:
        print("Tables in the database:")
        for table in tables:
            print(table[0])
    else:
        print("No tables found in the database.")

list_tables(conn)
conn.close()
print("Database connection closed.")
