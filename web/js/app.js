/**
 * 股票财务分析系统 - 前端应用
 * 功能：主题切换、数据加载、图表渲染、表格展示
 */

// 全局变量
let currentChart = null;
let currentData = [];
let currentMetric = 'gross_margin';

// API基础URL配置
const API_BASE_URL = window.location.protocol === 'file:' ? 'http://localhost:9528' : '';

// 指标配置
const METRIC_CONFIG = {
    gross_margin: {
        label: '毛利率',
        unit: '%',
        color: '#3182ce',
        bgColor: 'rgba(49, 130, 206, 0.1)'
    },
    revenue_yoy: {
        label: '营收同比',
        unit: '%',
        color: '#48bb78',
        bgColor: 'rgba(72, 187, 120, 0.1)'
    },
    revenue_qoq: {
        label: '营收环比',
        unit: '%',
        color: '#38b2ac',
        bgColor: 'rgba(56, 178, 172, 0.1)'
    },
    kfe_np_yoy: {
        label: '扣非同比',
        unit: '%',
        color: '#ed8936',
        bgColor: 'rgba(237, 137, 54, 0.1)'
    },
    kfe_np_qoq: {
        label: '扣非环比',
        unit: '%',
        color: '#ed64a6',
        bgColor: 'rgba(237, 100, 166, 0.1)'
    },
    kfe_np_ttm_w: {
        label: '扣非TTM',
        unit: '亿',
        color: '#9f7aea',
        bgColor: 'rgba(159, 122, 234, 0.1)',
        convert: function(value) { return value / 10000; }
    }
};

/**
 * 初始化页面
 */
function initPage() {
    // 从URL获取股票代码
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code') || '688456';
    
    // 加载主题设置
    loadTheme();
    
    // 加载股票数据
    loadStockData(code);
    
    // 绑定图表控制按钮事件
    bindChartControls();
    
    // 绑定搜索框回车事件
    document.getElementById('stockSearch').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchStock();
        }
    });
}

/**
 * 加载主题设置
 */
function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

/**
 * 切换主题
 */
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    // 循环切换：light -> dark -> gold -> light
    const themes = ['light', 'dark', 'gold'];
    const currentIndex = themes.indexOf(currentTheme);
    const newTheme = themes[(currentIndex + 1) % themes.length];
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
    
    // 重新渲染图表以适应新主题
    if (currentData.length > 0) {
        renderChart(currentMetric);
    }
}

/**
 * 更新主题图标
 */
function updateThemeIcon(theme) {
    const icon = document.getElementById('themeIcon');
    if (theme === 'dark') {
        icon.className = 'fas fa-sun';
    } else if (theme === 'gold') {
        icon.className = 'fas fa-crown';
    } else {
        icon.className = 'fas fa-moon';
    }
}

/**
 * 搜索股票
 */
async function searchStock() {
    const input = document.getElementById('stockSearch');
    const keyword = input.value.trim();
    
    if (!keyword) {
        alert('请输入股票代码或名称');
        return;
    }
    
    try {
        // 调用搜索API
        const response = await fetch(`${API_BASE_URL}/api/stocks?q=${encodeURIComponent(keyword)}&limit=10`);
        const result = await response.json();
        
        if (result.success && result.data && result.data.stocks.length > 0) {
            const stocks = result.data.stocks;
            
            if (stocks.length === 1) {
                // 只有一个匹配结果，直接跳转
                window.location.href = `stock_detail.html?code=${stocks[0].code}`;
            } else {
                // 多个匹配结果，让用户选择
                const options = stocks.map(stock => `${stock.name} (${stock.code})`).join('\n');
                const selected = prompt(`找到 ${stocks.length} 个匹配结果，请选择：\n${options}`);
                
                if (selected) {
                    // 提取股票代码
                    const codeMatch = selected.match(/\((\d{6})\)/);
                    if (codeMatch) {
                        window.location.href = `stock_detail.html?code=${codeMatch[1]}`;
                    }
                }
            }
        } else {
            alert('未找到匹配的股票，请尝试其他关键词');
        }
    } catch (error) {
        console.error('搜索股票失败:', error);
        alert('搜索失败，请稍后重试');
    }
}

/**
 * 加载股票数据
 */
async function loadStockData(code) {
    showLoading(true);
    
    try {
        // 加载股票基本信息
        await loadStockInfo(code);
        
        // 加载F10数据（行情、公司概况、盈利预测）
        await Promise.all([
            loadF10Market(code),
            loadF10Profile(code),
            loadF10Forecast(code)
        ]);
        
        // 加载季度指标数据
        const response = await fetch(`${API_BASE_URL}/api/stock/${code}/metrics?limit=16`);
        const result = await response.json();
        
        if (result.success && result.data) {
            currentData = result.data.metrics;
            
            // 更新关键指标卡片
            updateMetricCards(currentData);
            
            // 渲染图表
            renderChart(currentMetric);
            
            // 渲染表格
            renderTable(currentData);
        } else {
            console.error('加载数据失败:', result.message);
            alert('加载数据失败: ' + result.message);
        }
    } catch (error) {
        console.error('请求失败:', error);
        alert('请求失败，请检查网络连接');
    } finally {
        showLoading(false);
    }
}

/**
 * 加载股票基本信息
 */
async function loadStockInfo(code) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/stock/${code}/info`);
        const result = await response.json();
        
        if (result.success && result.data) {
            const info = result.data;
            document.getElementById('stockName').textContent = info.name || '--';
            document.getElementById('stockCode').textContent = info.code || code;
            
            // 触发股票信息加载完成事件
            window.dispatchEvent(new CustomEvent('stockInfoLoaded', {detail: {code: info.code || code, name: info.name}}));
        }
    } catch (error) {
        console.error('加载股票信息失败:', error);
        document.getElementById('stockName').textContent = '股票' + code;
        document.getElementById('stockCode').textContent = code;
    }
}

/**
 * 加载F10行情数据
 */
async function loadF10Market(code) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/stock/${code}/f10/market`);
        const result = await response.json();
        
        if (result.success && result.data) {
            const market = result.data;
            
            // 更新价格
            const priceElement = document.getElementById('currentPrice');
            const changeElement = document.getElementById('priceChange');
            const changePercentElement = document.getElementById('priceChangePercent');
            
            if (market.price) {
                const price = parseFloat(market.price);
                priceElement.textContent = price.toFixed(2);
                
                const change = market.change ? parseFloat(market.change) : 0;
                const changePercent = market.change_percent ? parseFloat(market.change_percent) : 0;
                
                if (change >= 0) {
                    changeElement.textContent = '+' + change.toFixed(2);
                    changePercentElement.textContent = '+' + changePercent.toFixed(2) + '%';
                    changeElement.classList.add('positive');
                    changePercentElement.classList.add('positive');
                } else {
                    changeElement.textContent = change.toFixed(2);
                    changePercentElement.textContent = changePercent.toFixed(2) + '%';
                    changeElement.classList.add('negative');
                    changePercentElement.classList.add('negative');
                }
            }
            
            // 更新市值
            const marketCapValue = parseFloat(market.market_cap);
            document.getElementById('marketCap').textContent = !isNaN(marketCapValue) && marketCapValue > 0 ? marketCapValue.toFixed(2) + '亿' : '--';
            
            // 显示更新时间
            const updateTimeElement = document.getElementById('updateTime');
            if (market.snapshot_time) {
                const updateTime = new Date(market.snapshot_time);
                updateTimeElement.textContent = `(更新: ${updateTime.toLocaleString()})`;
            } else {
                updateTimeElement.textContent = '';
            }
        }
    } catch (error) {
        console.error('加载F10行情数据失败:', error);
    }
}

/**
 * 加载F10公司概况
 */
async function loadF10Profile(code) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/stock/${code}/f10/profile`);
        const result = await response.json();
        
        if (result.success && result.data) {
            const profile = result.data;
            
            // 更新行业标签（使用F10数据）
            const industryTag = document.getElementById('industryTag');
            if (industryTag && (!industryTag.textContent || industryTag.textContent === '--')) {
                industryTag.textContent = profile.industry || '--';
            }
        }
    } catch (error) {
        console.error('加载F10公司概况失败:', error);
    }
}

/**
 * 加载盈利预测数据
 */
async function loadF10Forecast(code) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/stock/${code}/f10/forecast`);
        const result = await response.json();
        
        if (result.success && result.data && result.data.data) {
            const forecastList = result.data.data;
            const transformedData = transformForecastData(forecastList);
            renderForecastTable(transformedData);
        }
    } catch (error) {
        console.error('加载盈利预测数据失败:', error);
    }
}

/**
 * 转换盈利预测数据格式
 * 从: [{report_year: 2027, eps: 1.15, revenue: 5308.72, ...}, ...]
 * 到: [{指标: '每股收益', '2027': 1.15, '2026': 0.95, ...}, ...]
 */
function transformForecastData(data) {
    if (!data || data.length === 0) return [];
    
    const years = [...new Set(data.map(item => item.report_year))].sort().reverse();
    
    const metricNames = {
        'eps': '每股收益(元)',
        'revenue': '营业收入(亿元)',
        'net_profit': '净利润(亿元)',
        'pe': '市盈率',
        'roe': 'ROE(%)',
        'book_value_ps': '每股净资产(元)'
    };
    
    const result = [];
    
    for (const [key, label] of Object.entries(metricNames)) {
        const row = { '指标': label };
        years.forEach(year => {
            const yearData = data.find(item => item.report_year === year);
            // 检查值是否存在且不为null
            if (yearData && yearData[key] !== null && yearData[key] !== undefined) {
                row[year] = typeof yearData[key] === 'number' ? yearData[key].toFixed(2) : yearData[key];
            } else {
                row[year] = '--';
            }
        });
        result.push(row);
    }
    
    return result;
}

/**
 * 渲染盈利预测表格
 */
function renderForecastTable(data) {
    const header = document.getElementById('forecastHeader');
    const body = document.getElementById('forecastBody');
    
    // 清空现有内容
    header.innerHTML = '<th>指标</th>';
    body.innerHTML = '';
    
    if (!data || data.length === 0) {
        body.innerHTML = '<tr><td colspan="100%">暂无盈利预测数据</td></tr>';
        return;
    }
    
    // 获取所有年份列
    const years = new Set();
    data.forEach(row => {
        Object.keys(row).forEach(key => {
            if (key !== '指标' && key !== '') {
                years.add(key);
            }
        });
    });
    
    // 添加年份表头
    const sortedYears = Array.from(years).sort();
    sortedYears.forEach(year => {
        const th = document.createElement('th');
        th.textContent = year;
        header.appendChild(th);
    });
    
    // 添加数据行
    data.forEach(row => {
        const tr = document.createElement('tr');
        
        // 指标列
        const td = document.createElement('td');
        td.textContent = row['指标'] || '--';
        td.style.fontWeight = '500';
        tr.appendChild(td);
        
        // 年份数据列
        sortedYears.forEach(year => {
            const td = document.createElement('td');
            td.textContent = row[year] || '--';
            tr.appendChild(td);
        });
        
        body.appendChild(tr);
    });
}

/**
 * 更新关键指标卡片
 */
function updateMetricCards(data) {
    if (data.length === 0) return;
    
    const latest = data[0];
    const prev = data.length > 1 ? data[1] : null;
    
    // 毛利率
    updateMetricCard('latestGrossMargin', 'grossMarginChange', 
        latest.gross_margin, prev ? prev.gross_margin : null, '%');
    
    // 营收同比
    updateMetricCard('latestRevenueYoy', 'revenueYoyChange',
        latest.revenue_yoy, prev ? prev.revenue_yoy : null, '%');
    
    // 扣非同比
    updateMetricCard('latestKfeYoy', 'kfeYoyChange',
        latest.kfe_np_yoy, prev ? prev.kfe_np_yoy : null, '%');
    
    // 扣非TTM（转换为亿）
    const ttmElement = document.getElementById('latestKfeTtm');
    if (latest.kfe_np_ttm_w !== null && latest.kfe_np_ttm_w !== undefined) {
        ttmElement.textContent = formatNumber(latest.kfe_np_ttm_w / 10000);
    } else {
        ttmElement.textContent = '--';
    }
    
    // 营收环比
    updateMetricCard('latestRevenueQoq', 'revenueQoqChange',
        latest.revenue_qoq, prev ? prev.revenue_qoq : null, '%');
    
    // 扣非环比
    updateMetricCard('latestKfeQoq', 'kfeQoqChange',
        latest.kfe_np_qoq, prev ? prev.kfe_np_qoq : null, '%');
}

/**
 * 更新单个指标卡片
 */
function updateMetricCard(valueId, changeId, current, previous, unit) {
    const valueElement = document.getElementById(valueId);
    const changeElement = document.getElementById(changeId);
    
    if (current !== null && current !== undefined) {
        valueElement.textContent = current.toFixed(2) + unit;
        
        if (previous !== null && previous !== undefined) {
            const change = current - previous;
            const changePercent = previous !== 0 ? (change / Math.abs(previous) * 100) : 0;
            
            if (change > 0) {
                changeElement.textContent = `↑ ${change.toFixed(2)} (${changePercent.toFixed(1)}%)`;
                changeElement.className = 'metric-change positive';
            } else if (change < 0) {
                changeElement.textContent = `↓ ${Math.abs(change).toFixed(2)} (${Math.abs(changePercent).toFixed(1)}%)`;
                changeElement.className = 'metric-change negative';
            } else {
                changeElement.textContent = '- 持平';
                changeElement.className = 'metric-change';
            }
        } else {
            changeElement.textContent = '--';
            changeElement.className = 'metric-change';
        }
    } else {
        valueElement.textContent = '--';
        changeElement.textContent = '--';
        changeElement.className = 'metric-change';
    }
}

/**
 * 绑定图表控制按钮
 */
function bindChartControls() {
    const buttons = document.querySelectorAll('.chart-btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', function() {
            // 更新按钮状态
            buttons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // 更新当前指标
            currentMetric = this.getAttribute('data-metric');
            
            // 重新渲染图表
            renderChart(currentMetric);
        });
    });
}

/**
 * 渲染图表
 */
function renderChart(metric) {
    const ctx = document.getElementById('metricsChart').getContext('2d');
    const config = METRIC_CONFIG[metric];
    
    const sortedData = [...currentData].sort((a, b) => a.report_date - b.report_date);
    const labels = sortedData.map(d => d.report_date);
    // 如果有转换函数，应用转换（如扣非TTM从万转换为亿）
    const values = sortedData.map(d => {
        const val = d[metric];
        if (val !== null && val !== undefined && config.convert) {
            return config.convert(val);
        }
        return val;
    });
    
    // 销毁旧图表
    if (currentChart) {
        currentChart.destroy();
    }
    
    // 获取当前主题颜色
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)';
    const textColor = isDark ? '#cbd5e1' : '#4a5568';
    
    // 创建新图表
    currentChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: config.label,
                data: values,
                borderColor: config.color,
                backgroundColor: config.bgColor,
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6,
                pointBackgroundColor: config.color,
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: isDark ? '#1e293b' : '#fff',
                    titleColor: isDark ? '#f1f5f9' : '#1a1a2e',
                    bodyColor: isDark ? '#cbd5e1' : '#4a5568',
                    borderColor: isDark ? '#334155' : '#e2e8f0',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            let value = context.parsed.y;
                            if (value !== null && value !== undefined) {
                                return `${config.label}: ${value.toFixed(2)}${config.unit}`;
                            }
                            return `${config.label}: --`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: gridColor,
                        drawBorder: false
                    },
                    ticks: {
                        color: textColor,
                        font: {
                            size: 11
                        }
                    }
                },
                y: {
                    grid: {
                        color: gridColor,
                        drawBorder: false
                    },
                    ticks: {
                        color: textColor,
                        font: {
                            size: 11
                        },
                        callback: function(value) {
                            return value + config.unit;
                        }
                    }
                }
            }
        }
    });
}

/**
 * 渲染数据表格
 */
function renderTable(data) {
    const tbody = document.getElementById('tableBody');
    tbody.innerHTML = '';
    
    data.forEach(item => {
        const row = document.createElement('tr');
        
        const kfeTtm = item.kfe_np_ttm_w !== null && item.kfe_np_ttm_w !== undefined ? item.kfe_np_ttm_w / 10000 : null;
        const netProfit = item.net_profit !== null && item.net_profit !== undefined ? item.net_profit / 10000 : null;
        
        row.innerHTML = `
            <td>${item.report_date || '--'}</td>
            <td>${formatValue(item.gross_margin, '%')}</td>
            <td class="${getTrendClass(item.revenue_yoy)}">${formatValue(item.revenue_yoy, '%')}</td>
            <td class="${getTrendClass(item.revenue_qoq)}">${formatValue(item.revenue_qoq, '%')}</td>
            <td class="${getTrendClass(item.np_yoy)}">${formatValue(item.np_yoy, '%')}</td>
            <td class="${getTrendClass(item.kfe_np_yoy)}">${formatValue(item.kfe_np_yoy, '%')}</td>
            <td class="${getTrendClass(item.kfe_np_qoq)}">${formatValue(item.kfe_np_qoq, '%')}</td>
            <td>${formatNumber(kfeTtm)}</td>
            <td>${formatNumber(item.revenue)}</td>
            <td>${formatNumber(netProfit)}</td>
            <td>${formatValue(item.eps, '')}</td>
            <td>${formatValue(item.roe, '%')}</td>
        `;
        
        tbody.appendChild(row);
    });
}

/**
 * 格式化数值
 */
function formatValue(value, unit) {
    if (value === null || value === undefined) return '--';
    return value.toFixed(2) + unit;
}

/**
 * 格式化数字（添加千分位）
 */
function formatNumber(num) {
    if (num === null || num === undefined) return '--';
    return num.toLocaleString('zh-CN', { minimumFractionDigits: 4, maximumFractionDigits: 4 });
}

/**
 * 获取趋势样式类
 */
function getTrendClass(value) {
    if (value === null || value === undefined) return '';
    return value > 0 ? 'positive' : (value < 0 ? 'negative' : '');
}

/**
 * 显示/隐藏加载遮罩
 */
function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.add('active');
    } else {
        overlay.classList.remove('active');
    }
}

/**
 * 导出数据
 */
function exportData() {
    if (currentData.length === 0) {
        alert('暂无数据可导出');
        return;
    }
    
    // 构建CSV内容
    const headers = ['报告期', '毛利率(%)', '营收同比(%)', '净利润同比(%)', '扣非同比(%)', 
                     '扣非TTM(万)', '营收(万)', '净利润(万)', 'EPS(元)', 'ROE(%)'];
    
    let csv = headers.join(',') + '\n';
    
    currentData.forEach(item => {
        const row = [
            item.period,
            item.gross_margin || '',
            item.revenue_yoy || '',
            item.net_profit_yoy || '',
            item.kfe_np_yoy || '',
            item.kfe_np_ttm_w || '',
            item.revenue_quarterly_w || '',
            item.net_profit_attr_w || '',
            item.eps_basic || '',
            item.roe_diluted || ''
        ];
        csv += row.join(',') + '\n';
    });
    
    // 下载CSV文件
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `stock_${currentData[0].code}_metrics.csv`;
    link.click();
}