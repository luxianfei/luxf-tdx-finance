# 通达信 F10 财务数据采集工具

从通达信本地数据（gpcw 文件）中提取 A 股完整财务指标，与通达信 F10 界面完全一致。

## 功能特性

- ✅ **完整 F10 指标**：每股指标、利润、营收、毛利率、ROE、YoY、TTM
- ✅ **YoY 计算验证通过**：营收同比、扣非净利润同比与通达信 F10 完全一致
- ✅ **全A股批量采集**：支持并发采集所有 A 股数据
- ✅ **MySQL 8.0 存储**：完整数据库设计，支持增量更新
- ✅ **gpcw 文件缓存**：自动下载和缓存通达信财务数据包

## 项目结构

```
luxf_tdx_finance/
├── config.py                 # 配置文件
├── main.py                   # 单股票采集入口
├── batch_fetch.py            # 全A股批量采集
├── requirements.txt          # 依赖包
├── README.md                 # 本文档
│
├── database/                 # 数据库模块
│   ├── mysql_client.py       # MySQL 客户端
│   ├── schema.py            # 表结构初始化
│   └── schema.sql           # SQL 脚本（备用）
│
├── fetchers/                 # 数据采集模块
│   ├── gpcw_parser.py       # gpcw 二进制解析
│   └── finance_collector.py # 财务数据采集器
│
├── models/                   # 数据模型
│   └── finance_models.py    # 财务记录模型
│
├── utils/                    # 工具模块
│   └── stock_list.py        # 股票列表工具
│
└── tests/                    # 测试用例
    └── test_finance.py
```

## 安装

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 MySQL

编辑 `config.py` 中的 MySQL 配置：

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
# 方法1: 使用 Python 初始化
python main.py --init  # 初始化数据库表

# 方法2: 使用 MySQL 命令行
mysql -u root -p < database/schema.sql
```

## 使用方法

### 单股票采集

```bash
# 采集单只股票（默认 688456）
python main.py 688456

# 指定季度数
python main.py 688456 --quarters 8

# 采集并存入 MySQL
python main.py 688456 --mysql

# 指定缓存目录
python main.py 688456 --cache-dir ./finance_data
```

### 全A股批量采集

```bash
# 初始化数据库（首次运行）
python batch_fetch.py --init

# 采集全部 A 股
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

### 运行测试

```bash
python -m pytest tests/ -v
```

## 数据库表结构

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
| kfe_np_ttm_w | DECIMAL | 扣非净利润TTM(万元) |
| ... | ... | 更多字段 |

### fetch_log - 采集日志

记录每次采集的状态和结果。

## gpcw 字段映射（已验证）

| 指标 | 列号 | 说明 |
|------|------|------|
| 每股基本收益 | 1 | d[0] |
| 每股净资产 | 3 | d[2] |
| 每股未分配利润 | 5 | d[4] |
| 每股公积金 | 6 | d[5] |
| 每股经营现金流 | 7 | d[6] |
| 归属净利润 | 96 | d[95] |
| 扣非净利润_单季 | 233 | d[232] |
| 单季度营收 | 312 | d[311] |
| 单季度成本 | 328 | d[327] |
| 营收同比基数 | 230 | d[229] |
| ROE摊薄 | 281 | d[280] |

## 验证结果

**688456 有研粉材 2024Q4 数据已验证正确：**

| 指标 | 脚本输出 | 通达信F10 | 状态 |
|------|----------|-----------|------|
| 营收同比增长率 | 29.10% | 29.10% | ✅ |
| 扣非净利润同比增长率 | 463.35% | 463.35% | ✅ |

## 依赖包

- `pytdx` - 通达信数据接口
- `pymysql` - MySQL 数据库驱动
- `pandas` - 数据处理
- `numpy` - 数值计算

## 注意事项

1. **首次运行**：需要下载 gpcw 文件（约 200MB），会自动缓存到 `finance_data/` 目录
2. **网络问题**：如果下载失败，可以手动从通达信安装目录复制 `vipdoc/gpcw/` 下的文件
3. **MySQL 编码**：确保数据库使用 `utf8mb4` 编码以支持中文字符
4. **性能建议**：批量采集时建议使用 `--workers 4` 参数加速

## License

MIT License
