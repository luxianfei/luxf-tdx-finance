import re

# 读取页面内容
with open('baidu_stock.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找JSON数据
json_patterns = [
    r'window\.stockInfo\s*=\s*(\{.*?\});',
    r'window\.data\s*=\s*(\{.*?\});',
    r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});',
    r'"industry".*?:"([^"]+)"',
    r'"sector".*?:"([^"]+)"',
    r'"plate".*?:"([^"]+)"'
]

print('查找行业/板块相关的JSON数据:')
for pattern in json_patterns:
    matches = re.findall(pattern, content)
    if matches:
        print(f'\n模式: {pattern}')
        for match in matches[:3]:
            print(f'  匹配: {match[:200]}')

# 查找可能包含行业信息的脚本
script_tags = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
print(f'\n\n找到 {len(script_tags)} 个script标签')

# 在脚本中查找行业相关信息
for i, script in enumerate(script_tags[:10]):
    if 'industry' in script.lower() or '行业' in script or 'sector' in script.lower() or '板块' in script:
        print(f'\n脚本 {i} 包含行业相关信息:')
        # 提取相关片段
        lines = script.split('\n')
        for line in lines[:10]:
            if 'industry' in line.lower() or '行业' in line or 'sector' in line.lower() or '板块' in line:
                print(f'  {line.strip()[:150]}')
