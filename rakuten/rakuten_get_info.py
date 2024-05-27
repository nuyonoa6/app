import pandas as pd
import requests
import json
import datetime
import os
import re
from time import sleep
from config import CLIENT_ME

MAX_PAGE = 5
HITS_PER_PAGE = 30
REQ_URL = 'https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601'
WANT_ITEMS = [
    'itemUrl',
    'itemName', 'itemPrice', 'catchcopy', 'itemPriceMax3',
    'itemCaption', 'reviewCount', 'shopName', 'shopUrl', 'platform', 'janCode'
]

sta_time = datetime.datetime.today()
this_date = format(sta_time, '%Y%m%d')
path_output_dir = f'./output/{this_date}'
req_params = {
    'applicationId': CLIENT_ME['APPLICATION_ID'],
    'format': 'json',
    'formatVersion': '2',
    'keyword': '',
    'hits': HITS_PER_PAGE,
    'page': 0,
    'minPrice': 0,
    'maxPrice': 0
}

def main():
    if not os.path.isdir(path_output_dir):
        os.mkdir(path_output_dir)

    # 最初に 'shift_jis' エンコーディングでファイルを読み込む
    try:
        with open('./list_keyword.txt', 'r', encoding='shift_jis') as f:
            keywords = f.read().split('\n')
    except UnicodeDecodeError:
        # 失敗した場合は 'cp932' を使用
        with open('./list_keyword.txt', 'r', encoding='cp932') as f:
            keywords = f.read().split('\n')
    
    if os.path.exists('./price_range.txt'):
        with open('./price_range.txt', 'r', encoding='utf-8') as f:
            prices = f.read().split('\n')
            if len(prices) == 2:
                req_params['minPrice'] = prices[0]
                req_params['maxPrice'] = prices[1]

    with open('./ng_keyword.txt', 'r', encoding='utf-8') as f:
        ng_keywords = f.read().split('\n')

    create_output_data(keywords, ng_keywords)

    print(f"{'#'*10}")

def create_output_data(arg_keywords, ng_keywords):
    for keyword in arg_keywords:
        cnt = 1
        keyword = keyword.replace('\u3000', ' ')
        req_params['keyword'] = keyword
        path_file = f'{path_output_dir}/rakuten_{keyword}.csv'
        df = pd.DataFrame(columns=WANT_ITEMS)

        print(f"{'#'*10}\nNowKeyword --> {keyword}  Ngkeyword -->{ng_keywords}")

        while True:
            req_params['page'] = cnt
            res = requests.get(REQ_URL, req_params)
            res_code = res.status_code
            res = json.loads(res.text)

            if res_code != 200:
                print(f"ErrorCode --> {res_code}\nError --> {res['error']}\nPage --> {cnt}")
            else:
                if res['hits'] == 0:
                    break
                
                items = res['Items']
                filtered_items = [item for item in items if not any(ng in item['itemName'] for ng in ng_keywords)]
                if not filtered_items:
                    break
                
                for item in filtered_items:
                    item_data = {
                        'itemUrl': item.get('itemUrl'),
                        'itemName': item.get('itemName'),
                        'itemPrice': item.get('itemPrice'),
                        'catchcopy': item.get('catchcopy', ''),
                        'itemPriceMax3': item.get('itemPriceMax3', ''),
                        'itemCaption': item.get('itemCaption', ''),
                        'reviewCount': item.get('reviewCount', 0),
                        'shopName': item.get('shopName', ''),
                        'shopUrl': item.get('shopUrl', ''),
                        'platform': 'Rakuten',
                        'janCode': item.get('janCode', '')  # JANコードを取得
                    }
                    df = pd.concat([df, pd.DataFrame([item_data])], ignore_index=True)

            if cnt == MAX_PAGE:
                break
            
            cnt += 1
            #sleep(1)
    
        df.to_csv(path_file, index=False, encoding="utf_8_sig", sep=",")
        print(f"Finished!! Saved to {path_file}")

if __name__ == '__main__':
    main()
