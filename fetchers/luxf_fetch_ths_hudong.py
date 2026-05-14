#!/usr/bin/env python3
"""
Fetch Q&A data from THS (Tonghuashun) interactive platform API.
Usage: python3 fetch_ths.py <stock_code> [output_json]
Example: python3 fetch_ths.py 688456
         python3 fetch_ths.py 688596 output.json
"""
import sys
import subprocess
import json
import time
import random
import requests
from datetime import datetime, timedelta

API_BASE = "https://basic.10jqka.com.cn/interactive/api/list/"
REFERER = "https://news.10jqka.com.cn/hudong/"

# 随机User-Agent列表，模拟不同浏览器
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# 随机延迟范围（秒）
MIN_DELAY = 1.5
MAX_DELAY = 3.5


def get_random_headers():
    """生成随机请求头，模拟真实浏览器"""
    return {
        'Referer': REFERER,
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
    }


def random_delay(min_delay=MIN_DELAY, max_delay=MAX_DELAY):
    """随机延迟，避免被识别为爬虫"""
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)


def fetch_page_with_requests(code, page, extra=""):
    """使用requests库获取数据（推荐用于API调用），带反爬虫机制"""
    ts = int(time.time() * 1000)
    url = (f"{API_BASE}?top=0&totalcache=1&pagesize=20&page={page}&code={code}"
           f"{extra}&sort=atime&jsonp=callback&return=jsonp&true=callback&_={ts}")

    headers = get_random_headers()

    try:
        # 添加随机延迟
        random_delay()

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        raw = response.text.strip()
        if raw.startswith('callback('):
            raw = raw[len('callback('):-1]
        return json.loads(raw)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page {page}: {e}")
        # 遇到错误时增加延迟
        random_delay(3, 5)
        return {'result': [], 'total': '?'}


def fetch_page(code, page, extra=""):
    """使用curl获取数据（保持兼容）"""
    ts = int(time.time() * 1000)
    url = (f"{API_BASE}?top=0&totalcache=1&pagesize=20&page={page}&code={code}"
           f"{extra}&sort=atime&jsonp=callback&return=jsonp&true=callback&_={ts}")
    r = subprocess.run(
        ['curl', '-s', url, '-H', f'Referer: {REFERER}', '-H', f'User-Agent: {UA}', '--compressed'],
        capture_output=True, text=True, timeout=15
    )
    raw = r.stdout.strip()
    if raw.startswith('callback('):
        raw = raw[len('callback('):-1]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {'result': [], 'total': '?'}

def fetch_all(code, extra=""):
    """Fetch ALL pages for given stock code. Returns list of all items."""
    all_items = []
    for page in range(1, 500):
        data = fetch_page(code, page, extra)
        items = data.get('result', [])
        if not items:
            break
        all_items.extend(items)
        time.sleep(0.3)
        sys.stderr.write(f"  page {page}: {len(items)} items (total: {len(all_items)})\n")
    return all_items


def fetch_qa_data(code, limit=20, fetch_all=False, max_years=3):
    """
    获取股票的互动问答数据（用于API调用）
    :param code: 股票代码
    :param limit: 返回条数限制（当fetch_all=True时无效）
    :param fetch_all: 是否获取所有数据
    :param max_years: 最多获取多少年的数据
    :return: 问答数据列表，按回答时间倒序排列
    """
    all_items = []
    page = 1

    three_years_ago = (datetime.now() - timedelta(days=max_years * 365)).strftime('%Y-%m-%d')

    while True:
        data = fetch_page_with_requests(code, page)
        items = data.get('result', [])

        if not items:
            break

        for item in items:
            uid = item.get('uid', '')
            ask_user = uid.replace('投资者_', '') if uid.startswith('投资者_') else uid

            ask_time = item.get('qtime', '')
            answer_time = item.get('atime', '')

            is_replied = item.get('isreply', '0') == '1'
            if not is_replied:
                continue

            # 检查回答时间是否在3年内（而不是提问时间）
            # 因为可能存在很早提问但最近才回答的情况
            if answer_time:
                try:
                    answer_date = answer_time[:10]
                    if answer_date < three_years_ago:
                        break
                except:
                    pass

            all_items.append({
                'id': item.get('seq'),
                'code': item.get('code'),
                'title': item.get('question', '')[:50] + '...' if len(item.get('question', '')) > 50 else item.get('question', ''),
                'content': item.get('question', ''),
                'answer': item.get('answer', ''),
                'ask_time': ask_time,
                'answer_time': answer_time,
                'ask_user': ask_user,
                'status': item.get('isreply', '0'),
                'source': item.get('source', '')
            })

        # 如果遇到超过3年的数据，停止翻页
        if answer_time:
            try:
                answer_date = answer_time[:10]
                if answer_date < three_years_ago:
                    break
            except:
                pass

        if not fetch_all and len(all_items) >= limit:
            break

        page += 1

        if page > 100:
            break

    # 按回答时间倒序排列（而不是提问时间）
    all_items.sort(key=lambda x: x['answer_time'] or '', reverse=True)

    if not fetch_all:
        return all_items[:limit]

    return all_items

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 fetch_ths.py <stock_code> [output_json]")
        sys.exit(1)
    code = sys.argv[1]
    outfile = sys.argv[2] if len(sys.argv) > 2 else f"{code}_items.json"
    extra = sys.argv[3] if len(sys.argv) > 3 else ""

    sys.stderr.write(f"Fetching Q&A for stock {code}...\n")
    items = fetch_all(code, extra)
    sys.stderr.write(f"\nTotal: {len(items)} items collected\n")

    with open(outfile, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    sys.stderr.write(f"Saved to: {outfile}\n")
    print(outfile)

if __name__ == '__main__':
    main()