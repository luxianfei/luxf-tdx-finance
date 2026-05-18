# -*- coding: utf-8 -*-

# 读取文件
with open('e:/trae_proj/luxf-tdx-finance-v1.0/web/index.html', 'rb') as f:
    content_bytes = f.read()

try:
    content = content_bytes.decode('utf-8')
except:
    content = content_bytes.decode('gbk')

# 要添加的新功能卡片
new_card = '''
                <div class="feature-card card-8" onclick="navigateTo('qa_filter.html')">
                    <div class="feature-icon icon-8">
                        <i class="fas fa-comments"></i>
                    </div>
                    <h3>互动问答筛选</h3>
                    <p>按答复时间筛选近期有互动问答的股票，查看详细问答内容</p>
                    <span class="arrow">
                        <span>开始筛选</span>
                        <i class="fas fa-arrow-right"></i>
                    </span>
                </div>
'''

# 在 PS 科技股筛选卡片后添加新卡片
insert_marker = '''                <div class="feature-card card-7" onclick="navigateTo('ps_filter.html')">
                    <div class="feature-icon icon-7">
                        <i class="fas fa-rocket"></i>
                    </div>
                    <h3>PS科技股筛选</h3>
                    <p>基于PS市销率和机构盈利预测，筛选高成长科技股</p>
                    <span class="arrow">
                        <span>开始筛选</span>
                        <i class="fas fa-arrow-right"></i>
                    </span>
                </div>

            </div>'''

content = content.replace(insert_marker, insert_marker.replace('</div>\n            </div>', new_card + '\n            </div>'))

# 写入文件
with open('e:/trae_proj/luxf-tdx-finance-v1.0/web/index.html', 'wb') as f:
    f.write(content.encode('utf-8'))

print('导航链接添加完成')
