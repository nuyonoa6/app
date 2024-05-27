from flask import Flask, request, render_template, jsonify
import sqlite3
import subprocess
import os
import traceback

app = Flask(__name__)

# データベースファイルとキーワードファイルのパスを定義
DATABASE = os.path.join(os.path.dirname(__file__), 'database', 'database.db')
KEYWORD_FILE = os.path.join(os.path.dirname(__file__), 'list_keyword.txt')

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

            # クエリの空白をアンダースコアに置換
            table_name = query.replace(" ", "_")

            # データベース接続
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()

            # テーブルが存在するか確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            table_exists = cursor.fetchone()
            
            if table_exists:
                # テーブルが存在する場合、その内容を表示
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                conn.close()
                return render_template('search.html', query=query, columns=columns, rows=rows)
            else:
                # テーブルが存在しない場合、list_keyword.txtを初期化してから書き込み、スクリプトを実行
                with open(KEYWORD_FILE, 'w') as f:
                    f.write(query)  # 改行なしで書き込む

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
                    cursor.execute(f"SELECT * FROM {table_name}")
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

if __name__ == '__main__':
    app.run(debug=True)
