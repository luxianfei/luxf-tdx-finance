import requests

# 测试新浪财经API
stocks = ['688456', '300034', '002709', '688536']

for code in stocks:
    market = 'sh' if code.startswith('6') else 'sz'
    url = f'https://hq.sinajs.cn/list={market}{code}'
    
    response = requests.get(url)
    response.encoding = 'gbk'
    
    if response.status_code == 200:
        content = response.text
        # 格式: var hq_str_sh688456="有研粉材,86.26,82.60,80.90,89.66,80.88,9468929,814627812,..."
        fields = content.split(',')
        print(f'\n股票: {code}')
        print(f'名称: {fields[0].split("=")[1].strip("\"")}')
        print(f'总字段数: {len(fields)}')
        # 新浪财经的行业信息通常在后面的字段中
        for i in range(len(fields)-10, len(fields)):
            if i < len(fields):
                print(f'字段{i}: {fields[i]}')
