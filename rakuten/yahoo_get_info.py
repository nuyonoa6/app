import requests
import json
import pandas as pd
import os
from datetime import datetime

# 出力ディレクトリの設定
sta_time = datetime.today()
this_date = format(sta_time, '%Y%m%d')
path_output_dir = f'./output/{this_date}'

# YahooショッピングAPIの設定
appid = "dj00aiZpPW5jdDVXYTBLV2ViWCZzPWNvbnN1bWVyc2VjcmV0Jng9MWI-"

# 価格範囲の読み取り
use_price_range = False
if os.path.exists('./price_range.txt'):
    with open('./price_range.txt', 'r', encoding='utf-8') as f:
        prices = f.read().split('\n')
        if len(prices) == 2:
            Lowest_price = prices[0]
            Highest_price = prices[1]
            use_price_range = True

# 必要なカラム
WANT_ITEMS = [
    'itemUrl',
    'itemName', 'itemPrice', 'catchcopy', 'itemPriceMax3',
    'itemCaption', 'reviewCount', 'shopName', 'shopUrl', 'platform', 'janCode'
]

def fetch_data(url):
    call = requests.get(url)
    return json.loads(call.content)

def create_output_data(data, keyword):
    items = data['hits']
    records = []

    for item in items:
        item_data = {
            'itemUrl': item.get('url'),
            'itemName': item.get('name'),
            'itemPrice': item.get('price'),
            'catchcopy': item.get('headline', ''),
            'itemPriceMax3': '',  # Yahoo APIには該当項目がないため空欄
            'itemCaption': item.get('description', ''),
            'reviewCount': item.get('review', {}).get('count', 0),
            'shopName': item.get('seller', {}).get('name', ''),
            'shopUrl': item.get('seller', {}).get('url', ''),
            'platform': 'Yahoo',
            'janCode': item.get('janCode', '')  # JANコードを取得
        }
        records.append(item_data)
    
    df = pd.DataFrame(records, columns=WANT_ITEMS)
    
    if not os.path.isdir(path_output_dir):
        os.makedirs(path_output_dir)
    
    path_file = f'{path_output_dir}/yahoo_{keyword}.csv'
    df.to_csv(path_file, index=False, encoding="utf_8_sig", sep=",")
    print(f"Finished! Data saved to {path_file}")

def main():

    if not os.path.isdir(path_output_dir):
        os.makedirs(path_output_dir)

    # 最初に 'shift_jis' エンコーディングでファイルを読み込む
    try:
        with open('./list_keyword.txt', 'r', encoding='shift_jis') as f:
            keywords = f.read().split('\n')
    except UnicodeDecodeError:
        # 失敗した場合は 'cp932' を使用
        with open('./list_keyword.txt', 'r', encoding='cp932') as f:
            keywords = f.read().split('\n')

    for keyword in keywords:
        keyword = keyword.replace('\u3000', ' ')
        if use_price_range:
            url = f'https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch?appid={appid}&price_from={Lowest_price}&price_to={Highest_price}&query={keyword}&results=100'
        else:
            url = f'https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch?appid={appid}&query={keyword}&results=100'
        
        data = fetch_data(url)
        create_output_data(data, keyword)

if __name__ == '__main__':
    main()
