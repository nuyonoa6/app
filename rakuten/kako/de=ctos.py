import pandas as pd
import sqlite3
import os

# CSVディレクトリとデータベースディレクトリのパス
csv_directory = 'output/20240517'
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
        
        table_name = os.path.splitext(filename)[0]
        
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"Saved {filename} to table {table_name}")

# def display_table_contents(connection):
#     cursor = connection.cursor()
#     for filename in os.listdir(csv_directory):
#         if filename.endswith('.csv'):
#             table_name = os.path.splitext(filename)[0]
#             print(f"\nContents of table '{table_name}':")

#             cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
#             if cursor.fetchone() is None:
#                 print(f"Table '{table_name}' does not exist.")
#                 continue
            
#             cursor.execute(f"SELECT * FROM {table_name}")
#             rows = cursor.fetchall()
            
#             for row in rows:
#                 print(row)

# display_table_contents(conn)

conn.close()