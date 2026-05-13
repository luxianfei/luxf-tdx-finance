import requests

# 测试多个股票
stocks = ['688456', '300034', '002709', '688536']

for code in stocks:
    market = 'sh' if code.startswith('6') else 'sz'
    url = f'http://qt.gtimg.cn/q={market}{code}'
    
    response = requests.get(url)
    response.encoding = 'gbk'
    
    if response.status_code == 200:
        content = response.text
        fields = content.split('~')
        print(f'\n股票: {code}')
        print(f'名称: {fields[1]}')
        print(f'总字段数: {len(fields)}')
        print('\n关键字段:')
        print(f'字段50: {fields[50] if len(fields) > 50 else "N/A"}')
        print(f'字段61: {fields[61] if len(fields) > 61 else "N/A"}')
        print(f'字段62: {fields[62] if len(fields) > 62 else "N/A"}')
        print(f'字段63: {fields[63] if len(fields) > 63 else "N/A"}')
        print(f'字段64: {fields[64] if len(fields) > 64 else "N/A"}')
        print(f'字段65: {fields[65] if len(fields) > 65 else "N/A"}')
        print(f'字段70: {fields[70] if len(fields) > 70 else "N/A"}')
        print(f'字段71: {fields[71] if len(fields) > 71 else "N/A"}')
