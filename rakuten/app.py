from flask import Flask, request, render_template, jsonify, redirect, url_for
import sqlite3
import subprocess
import os
import traceback
from datetime import datetime
import re

app = Flask(__name__)

DATABASE = os.path.join(os.path.dirname(__file__), 'database', 'database.db')
KEYWORD_FILE = os.path.join(os.path.dirname(__file__), 'list_keyword.txt')

def calculate_match_score(table_name, query):
    table_name_escaped = f'"{table_name}"'
    return f"""
    SELECT
        *,
        (3 * (CASE WHEN itemName LIKE '%' || ? || '%' THEN 1 ELSE 0 END) +
         2 * (CASE WHEN catchcopy LIKE '%' || ? || '%' THEN 1 ELSE 0 END) +
         (CASE WHEN itemCaption LIKE '%' || ? || '%' THEN 1 ELSE 0 END) +
         (CASE WHEN shopName LIKE '%' || ? || '%' THEN 1 ELSE 0 END) -
         (CASE WHEN itemName LIKE '%中古%' OR catchcopy LIKE '%中古%' OR itemCaption LIKE '%中古%' THEN 5 ELSE 0 END)) AS match_score
    FROM {table_name_escaped}
    WHERE itemName NOT LIKE '%中古%' AND catchcopy NOT LIKE '%中古%' AND itemCaption NOT LIKE '%中古%'
    ORDER BY match_score DESC, itemPrice ASC;
    """

def run_platform_scripts():
    script_dir = os.path.dirname(__file__)
    for filename in os.listdir(script_dir):
        if filename.endswith('_get_info.py'):
            script_path = os.path.join(script_dir, filename)
            result = subprocess.run(['python3', script_path], capture_output=True, text=True)
            print(f"{filename} output:", result.stdout)
            print(f"{filename} errors:", result.stderr)

@app.route('/')
def home():
    return render_template('search.html')

@app.route('/search', methods=['GET', 'POST'])
def search_table():
    try:
        if request.method == 'POST':
            query = request.form.get('query')
            if not query:
                return jsonify({'error': 'Query parameter is required'}), 400

            keyword = re.sub(r'\s+', '_', query)
            platforms = ['rakuten', 'yahoo']  # 今後追加する他のプラットフォームもここに追加

            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()

            table_exists = False
            for platform in platforms:
                table_name = f"{platform}_{keyword}"
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                if cursor.fetchone():
                    table_exists = True
                    break
            
            if table_exists:
                search_query = calculate_match_score(table_name, query)
                cursor.execute(search_query, (query, query, query, query))
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                conn.close()
                return render_template('search.html', query=query, columns=columns, rows=rows)
            else:
                with open(KEYWORD_FILE, 'w') as f:
                    f.write(query)

                today = datetime.today().strftime('%Y%m%d')
                csv_directory = f'output/{today}'

                run_platform_scripts()

                # ctos.pyを実行
                ctos_result = subprocess.run(['python3', os.path.join(os.path.dirname(__file__), 'ctos.py')], capture_output=True, text=True)
                print("ctos.py output:", ctos_result.stdout)
                print("ctos.py errors:", ctos_result.stderr)

                conn.close()
                conn = sqlite3.connect(DATABASE)
                cursor = conn.cursor()

                table_exists = False
                for platform in platforms:
                    table_name = f"{platform}_{keyword}"
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                    if cursor.fetchone():
                        table_exists = True
                        break
                
                if table_exists:
                    search_query = calculate_match_score(table_name, query)
                    cursor.execute(search_query, (query, query, query, query))
                    rows = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    conn.close()
                    return render_template('search.html', query=query, columns=columns, rows=rows)
                else:
                    conn.close()
                    return jsonify({'error': 'Table was not created successfully'}), 500

        return render_template('search.html')
    except Exception as e:
        error_message = traceback.format_exc()
        print("Error occurred:", error_message)
        return jsonify({'error': 'Internal server error', 'details': str(e), 'trace': error_message}), 500

@app.route('/compare_prices')
def compare_prices():
    item_name = request.args.get('item_name')
    if item_name:
        price_data = [
            ('Rakuten', '1200円', 'https://search.rakuten.co.jp/search/mall/' + item_name),
            ('Yahoo', '1100円', 'https://shopping.yahoo.co.jp/search?p=' + item_name)
        ]
        return render_template('compare.html', item_name=item_name, price_data=price_data)
    else:
        return jsonify({'error': 'Item name is required'}), 400

if __name__ == '__main__':
    app.run(debug=True)
