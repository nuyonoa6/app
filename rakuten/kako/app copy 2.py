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
    # テーブル名を二重引用符でエスケープ
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

            # クエリの空白（半角および全角）をアンダースコアに置換
            table_name = re.sub(r'\s+', '_', query)

            # データベース接続
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()

            # テーブルが存在するか確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            table_exists = cursor.fetchone()
            
            if table_exists:
                # テーブルが存在する場合、検索キーワードに基づいて一致度スコアを計算し、結果をソート
                search_query = calculate_match_score(table_name, query)
                cursor.execute(search_query, (query, query, query, query))
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                conn.close()
                return render_template('search.html', query=query, columns=columns, rows=rows)
            else:
                # テーブルが存在しない場合、list_keyword.txtを初期化してから書き込み、スクリプトを実行
                with open(KEYWORD_FILE, 'w') as f:
                    f.write(query)  # 改行なしで書き込む

                # 現在の日付に基づいてCSVディレクトリのパスを生成
                today = datetime.today().strftime('%Y%m%d')
                csv_directory = f'output/{today}'

                # get_info.pyとctos.pyを実行
                get_info_result = subprocess.run(['python3', os.path.join(os.path.dirname(__file__), 'get_info.py')], capture_output=True, text=True)
                ctos_result = subprocess.run(['python3', os.path.join(os.path.dirname(__file__), 'ctos.py')], capture_output=True, text=True)

                # デバッグ情報の出力
                print("get_info.py output:", get_info_result.stdout)
                print("get_info.py errors:", get_info_result.stderr)
                print("ctos.py output:", ctos_result.stdout)
                print("ctos.py errors:", ctos_result.stderr)

                # 再度データベース接続を開いてテーブルを検索して表示
                conn.close()
                conn = sqlite3.connect(DATABASE)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                table_exists = cursor.fetchone()
                
                if table_exists:
                    search_query = calculate_match_score(table_name, query)
                    cursor.execute(search_query, (query, query, query, query))
                    rows = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    conn.close()
                    return render_template('search.html', query=query, columns=columns, rows=rows)
                else:
                    conn.close()
                    return jsonify({'error': 'Table was not created successfully', 'get_info_output': get_info_result.stdout, 'get_info_errors': get_info_result.stderr, 'ctos_output': ctos_result.stdout, 'ctos_errors': ctos_result.stderr}), 500

        return render_template('search.html')
    except Exception as e:
        error_message = traceback.format_exc()
        print("Error occurred:", error_message)
        return jsonify({'error': 'Internal server error', 'details': str(e), 'trace': error_message}), 500

@app.route('/compare_prices')
def compare_prices():
    item_name = request.args.get('item_name')
    if item_name:
        # 価格比較サイトのURLにリダイレクト
        compare_url = f"https://example.com/compare?item_name={item_name}"
        return redirect(compare_url)
    else:
        return jsonify({'error': 'Item name is required'}), 400

if __name__ == '__main__':
    app.run(debug=True)
