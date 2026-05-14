# Luxf股票深度投研分析平台

基于通达信本地+百度财经+同花顺财经数据的A股财务数据采集、分析和可视化平台。

## 功能特性

- ✅ **完整F10财务指标**：每股指标、利润、营收、毛利率、ROE、YoY、TTM
- ✅ **YoY计算验证通过**：营收同比、扣非净利润同比与通达信F10完全一致
- ✅ **全A股批量采集**：支持并发采集所有A股数据
- ✅ **MySQL 8.0存储**：完整数据库设计，支持增量更新
- ✅ **gpcw文件缓存**：自动下载和缓存通达信财务数据包
- ✅ **PS市销率科技股筛选**：支持按PS倍数、营收增速筛选科技成长股
- ✅ **申万行业分类**：一级/二级行业分类，支持从通达信本地导入
- ✅ **股票板块解析**：从通达信本地解析股票所属板块（创业板/科创板/主板等）
- ✅ **Web可视化界面**：股票详情页、筛选页面，支持表头固定、分页
- ✅ **RESTful API**：提供股票数据查询、筛选等API接口

## 项目结构

```
luxf_tdx_finance/
├── config.py                 # 配置文件（数据库连接等）
├── main.py                   # 单股票采集入口
├── api_server.py             # Flask API服务
├── requirements.txt          # 依赖包
├── README.md                 # 本文档
├── start_server.bat          # 启动API服务脚本
│
├── database/                 # 数据库模块
│   ├── mysql_client.py       # MySQL客户端
│   ├── schema.py             # 表结构初始化
│   └── schema.sql            # SQL脚本
│
├── fetchers/                 # 数据采集模块
│   ├── gpcw_parser.py        # gpcw二进制解析
│   ├── finance_collector.py  # 财务数据采集器
│   ├── local_data_collector.py # 本地数据采集
│   ├── f10_collector.py      # F10数据采集
│   └── stock_info_collector.py # 股票基本信息采集
│
├── models/                   # 数据模型
│   ├── finance_models.py     # 财务记录模型
│   └── tech_sector.py        # 科技板块数据模型
│
├── utils/                    # 工具模块
│   └── stock_list.py         # 股票列表工具
│
├── scripts/                  # 数据处理脚本
│   ├── update_tech_stocks.py     # 更新科技股列表
│   ├── import_tdx_plate.py       # 从通达信导入板块
│   ├── import_tdx_industry.py    # 从通达信导入行业
│   ├── import_shenwan_level2.py  # 导入申万二级行业
│   └── unify_industry_codes.py   # 统一行业代码
│
├── web/                      # Web前端
│   ├── index.html            # 首页
│   ├── stock_detail.html     # 股票详情页
│   ├── ps_filter.html        # PS筛选页面
│   ├── stock_filter.html     # 股票筛选页面
│   ├── css/style.css         # 样式文件
│   └── js/app.js             # JavaScript逻辑
│
├── checks/                   # 检查脚本
│   └── *.py                  # 各种数据检查脚本
│
├── debug/                    # 调试脚本
│   └── *.py                  # 各种调试脚本
│
├── tests/                    # 测试用例
│   └── *.py                  # 测试文件
│
├── finance_data/             # 财务数据缓存
│   └── gpcw*.zip             # 通达信gpcw数据包
│
└── workbuddy/                # 工作助手
    └── stock_report_generator.py # 股票报告生成
```

## 安装

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置MySQL

编辑 `config.py` 中的MySQL配置：

```python
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "your_password_here",  # ⚠️ 修改为你的密码
    "database": "stock_finance",
    "charset": "utf8mb4",
}
```

### 3. 创建数据库

```bash
# 方法1: 使用Python初始化
python main.py --init  # 初始化数据库表

# 方法2: 使用MySQL命令行
mysql -u root -p < database/schema.sql
```

## 使用方法

### 单股票采集

```bash
# 采集单只股票（默认 688456）
python main.py 688456

# 指定季度数
python main.py 688456 --quarters 8

# 采集并存入MySQL
python main.py 688456 --mysql

# 指定缓存目录
python main.py 688456 --cache-dir ./finance_data
```

### 全A股批量采集

```bash
# 初始化数据库（首次运行）
python batch_fetch.py --init

# 采集全部A股
python batch_fetch.py --all

# 只采集上海市场
python batch_fetch.py --all --market sh

# 只采集深圳市场
python batch_fetch.py --all --market sz

# 增量更新（只采集未完成的股票）
python batch_fetch.py --update

# 指定股票代码
python batch_fetch.py --codes 688456,000001,600519

# 并发采集（加速）
python batch_fetch.py --all --workers 4
```

### 启动API服务

```bash
# 方式1：直接运行
python api_server.py

# 方式2：使用批处理脚本
start_server.bat

# 服务地址: http://localhost:9528
```

### 行业分类更新

```bash
# 更新科技股列表
python scripts/update_tech_stocks.py

# 从通达信导入板块信息
python scripts/import_tdx_plate.py

# 更新申万二级行业分类
python scripts/import_shenwan_level2.py

# 统一各表行业代码
python scripts/unify_industry_codes.py
```

### Web界面访问

启动API服务后，访问以下页面：

- **首页**: http://localhost:9528/index.html
- **股票详情**: http://localhost:9528/stock_detail.html?code=688456
- **PS筛选**: http://localhost:9528/ps_filter.html
- **股票筛选**: http://localhost:9528/stock_filter.html

## API接口

### 获取股票行情数据

```
GET /api/stock/{code}/market_data
```

**响应示例**:
```json
{
    "code": "688456",
    "name": "有研粉材",
    "industry": "电气设备-电机",
    "plate": "科创板",
    "current_price": 82.35,
    "market_cap": 8536000000,
    "pe_ttm": 45.23
}
```

### PS科技股筛选

```
GET /api/stocks/filter/ps_tech?psMin=8&psMax=15&page=1&limit=50
```

**参数**:
- `psMin`: 最小PS倍数（默认8）
- `psMax`: 最大PS倍数（默认15）
- `revenueGrowthMin`: 最小营收增速（可选）
- `page`: 页码（默认1）
- `limit`: 每页条数（默认50）

## 数据库表结构

### 核心数据表

| 表名 | 说明 |
|------|------|
| `stock_list` | 股票基本信息（代码、名称、行业、上市日期等） |
| `stock_market_data` | 股票行情数据（价格、市值、PE、PB、板块等） |
| `quarterly_finance` | 季度财务数据（营收、利润、同比增速等） |
| `profit_forecast` | 盈利预测数据（机构预测） |
| `tech_sector_stocks` | 科技股列表 |
| `industry_map` | 行业映射表（申万一级/二级行业） |

### quarterly_finance - 季度财务数据

| 字段 | 类型 | 说明 |
|------|------|------|
| code | VARCHAR(10) | 股票代码 |
| report_date | INT | 报告期 (如 20241231) |
| year | SMALLINT | 年份 |
| quarter | TINYINT | 季度 (1-4) |
| eps_basic | DECIMAL | 每股基本收益(元) |
| gross_margin | DECIMAL | 毛利率(%) |
| roe_diluted | DECIMAL | ROE摊薄(%) |
| revenue_yoy | DECIMAL | 营收同比(%) |
| kfe_np_yoy | DECIMAL | 扣非净利润同比(%) |
| revenue_quarterly_w | DECIMAL | 单季度营收(万元) |
| kfe_np_ttm_w | DECIMAL | 扣非净利润TTM(万元) |

### industry_map - 行业映射表

| 字段 | 类型 | 说明 |
|------|------|------|
| code | VARCHAR(10) | 行业代码（如 SW001、SW00101） |
| name | VARCHAR(50) | 行业名称 |
| parent_code | VARCHAR(10) | 父级行业代码 |
| level | TINYINT | 级别（1=一级行业，2=二级行业） |

## 申万一级行业分类

| 代码 | 行业名称 | 代码 | 行业名称 |
|------|----------|------|----------|
| SW001 | 农林牧渔 | SW017 | 交通运输 |
| SW002 | 采掘 | SW018 | 房地产 |
| SW003 | 化工 | SW019 | 商业贸易 |
| SW004 | 钢铁 | SW020 | 休闲服务 |
| SW005 | 有色金属 | SW021 | 综合 |
| SW006 | 建筑装饰 | SW022 | 建筑材料 |
| SW007 | 电气设备 | SW023 | 通信 |
| SW008 | 机械设备 | SW024 | 计算机 |
| SW009 | 国防军工 | SW025 | 传媒 |
| SW010 | 汽车 | SW026 | 银行 |
| SW011 | 家用电器 | SW027 | 非银金融 |
| SW012 | 食品饮料 | SW028 | 电子 |
| SW013 | 纺织服装 | SW029 | 医药商业 |
| SW014 | 轻工制造 | SW030 | 环保 |
| SW015 | 医药生物 | SW031 | 半导体 |
| SW016 | 公用事业 | | |

## 验证结果

**688456 有研粉材 2024Q4 数据已验证正确：**

| 指标 | 脚本输出 | 通达信F10 | 状态 |
|------|----------|-----------|------|
| 营收同比增长率 | 29.10% | 29.10% | ✅ |
| 扣非净利润同比增长率 | 463.35% | 463.35% | ✅ |

## 依赖包

```text
pytdx==1.7.0
pymysql==1.1.0
pandas==2.1.4
numpy==1.26.3
flask==3.0.0
requests==2.31.0
lxml==4.9.4
akshare==1.10.9
```

## 注意事项

1. **首次运行**：需要下载gpcw文件（约200MB），会自动缓存到`finance_data/`目录
2. **网络问题**：如果下载失败，可以手动从通达信安装目录复制`vipdoc/gpcw/`下的文件
3. **MySQL编码**：确保数据库使用`utf8mb4`编码以支持中文字符
4. **性能建议**：批量采集时建议使用`--workers 4`参数加速
5. **通达信路径**：如果需要从本地导入板块/行业数据，请确保通达信安装路径正确

## License

MIT License
