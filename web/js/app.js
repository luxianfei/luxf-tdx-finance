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
        
        // 加载互动问答数据（不阻塞其他加载）
        loadQAData(code);
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
 * 加载股票行情数据（从百度财经抓取）
 */
async function loadF10Market(code) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/stock/${code}/market_data`);
        const result = await response.json();
        
        if (result.success && result.data) {
            const data = result.data;
            
            // 更新价格
            const priceElement = document.getElementById('currentPrice');
            const changeElement = document.getElementById('priceChange');
            const changePercentElement = document.getElementById('priceChangePercent');
            const priceChangeInfo = document.getElementById('priceChangeInfo');
            
            if (data.current_price !== null && data.current_price !== undefined) {
                priceElement.textContent = data.current_price.toFixed(2);
                
                const change = data.price_change !== null && data.price_change !== undefined ? parseFloat(data.price_change) : 0;
                const changePercent = data.change_percent !== null && data.change_percent !== undefined ? parseFloat(data.change_percent) : 0;
                
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
            } else {
                priceChangeInfo.style.display = 'none';
            }
            
            // 更新交易所和板块信息
            document.getElementById('exchangeTag').textContent = data.exchange || '--';
            document.getElementById('plateTag').textContent = data.plate || '--';
            document.getElementById('industryTag').textContent = data.industry || '--';
            
            // 更新行情数据
            document.getElementById('openPrice').textContent = data.open_price !== null ? data.open_price.toFixed(2) : '--';
            document.getElementById('prevClose').textContent = data.prev_close !== null ? data.prev_close.toFixed(2) : '--';
            document.getElementById('highPrice').textContent = data.high_price !== null ? data.high_price.toFixed(2) : '--';
            document.getElementById('lowPrice').textContent = data.low_price !== null ? data.low_price.toFixed(2) : '--';
            
            // 更新成交量和成交额（格式化）
            document.getElementById('volume').textContent = formatVolume(data.volume);
            document.getElementById('amount').textContent = formatAmount(data.amount);
            document.getElementById('marketCap').textContent = formatAmount(data.market_cap);
            document.getElementById('totalShares').textContent = formatAmount(data.total_shares);
            document.getElementById('floatCap').textContent = formatAmount(data.float_cap);
            
            // 更新换手率、量比、市盈率
            document.getElementById('turnoverRate').textContent = data.turnover_rate !== null ? data.turnover_rate.toFixed(2) + '%' : '--';
            document.getElementById('volumeRatio').textContent = data.volume_ratio !== null ? data.volume_ratio.toFixed(2) : '--';
            document.getElementById('peTtm').textContent = data.pe_ttm !== null ? data.pe_ttm.toFixed(2) : '--';
            
            // 更新时间
            document.getElementById('updateTime').textContent = data.update_time || '--';
        }
        
        // 检查自选股状态
        await checkMyStockStatus(code);
    } catch (error) {
        console.error('加载股票行情数据失败:', error);
    }
}

/**
 * 格式化成交量
 */
function formatVolume(volume) {
    if (volume === null || volume === undefined) return '--';
    const v = parseFloat(volume);
    if (isNaN(v)) return '--';
    if (v >= 10000) {
        return (v / 10000).toFixed(2) + '万手';
    }
    return v.toFixed(0) + '手';
}

/**
 * 格式化金额（市值、成交额等）
 */
function formatAmount(amount) {
    if (amount === null || amount === undefined) return '--';
    const a = parseFloat(amount);
    if (isNaN(a)) return '--';
    if (a >= 100000000) {
        return (a / 100000000).toFixed(2) + '亿';
    } else if (a >= 10000) {
        return (a / 10000).toFixed(2) + '万';
    }
    return a.toFixed(0);
}

/**
 * 刷新行情数据
 */
async function refreshMarketData() {
    const refreshBtn = document.getElementById('refreshMarketBtn');
    const originalHtml = refreshBtn.innerHTML;
    
    // 设置刷新状态
    refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    refreshBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/stock/${currentStockCode}/market_data/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 刷新成功，重新加载行情数据
            await loadF10Market(currentStockCode);
            showToast('行情数据刷新成功');
        } else {
            showToast('刷新失败: ' + result.message, 'error');
        }
    } catch (error) {
        console.error('刷新行情数据失败:', error);
        showToast('刷新失败，请检查网络连接', 'error');
    } finally {
        // 恢复按钮状态
        refreshBtn.innerHTML = originalHtml;
        refreshBtn.disabled = false;
    }
}

/**
 * 切换自选股状态
 */
async function toggleMyStock() {
    const toggleBtn = document.getElementById('toggleMyStockBtn');
    const isFavorited = toggleBtn.classList.contains('favorited');
    
    try {
        let response;
        if (isFavorited) {
            // 删除自选股
            response = await fetch(`${API_BASE_URL}/api/my_stock/${currentStockCode}`, {
                method: 'DELETE'
            });
        } else {
            // 添加自选股
            const stockName = document.getElementById('stockName').textContent;
            response = await fetch(`${API_BASE_URL}/api/my_stock/${currentStockCode}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: stockName,
                    pool_type: 'watch',
                    notes: ''
                })
            });
        }
        
        const result = await response.json();
        
        if (result.success) {
            // 切换按钮状态
            toggleBtn.classList.toggle('favorited');
            const actionText = isFavorited ? '已移出自选股' : '已添加到自选股';
            showToast(actionText);
        } else {
            showToast('操作失败: ' + result.message, 'error');
        }
    } catch (error) {
        console.error('切换自选股状态失败:', error);
        showToast('操作失败，请检查网络连接', 'error');
    }
}

/**
 * 检查股票是否在自选股中
 */
async function checkMyStockStatus(code) {
    const toggleBtn = document.getElementById('toggleMyStockBtn');
    if (!toggleBtn) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/my_stocks`);
        const result = await response.json();
        
        if (result.success && result.data) {
            const exists = result.data.some(stock => stock.code === code);
            toggleBtn.classList.toggle('favorited', exists);
        }
    } catch (error) {
        console.error('检查自选股状态失败:', error);
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
 * 显示Toast提示
 */
function showToast(message, type = 'success') {
    // 创建Toast元素
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    // 添加到页面
    document.body.appendChild(toast);
    
    // 显示动画
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    // 3秒后自动消失
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
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

// 全局变量存储当前分页和搜索状态
let currentQAPage = 1;
let currentQAKeyword = '';

/**
 * 加载互动问答数据（支持分页和搜索）
 */
async function loadQAData(code, page = 1, keyword = '') {
    if (!code) {
        // 从URL获取股票代码
        const urlParams = new URLSearchParams(window.location.search);
        code = urlParams.get('code') || '688456';
    }
    
    // 保存当前状态
    currentQAPage = page;
    currentQAKeyword = keyword;
    
    const container = document.getElementById('qaContainer');
    container.innerHTML = '<div class="loading-text">加载中...</div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/stock/${code}/qa?limit=20&page=${page}&keyword=${encodeURIComponent(keyword)}`);
        const result = await response.json();
        
        if (result.success && result.data) {
            renderQAData(result.data.qa_list, keyword);
            renderPagination(result.data);
        } else {
            container.innerHTML = '<div class="empty-state">暂无互动问答数据</div>';
            document.getElementById('qaPagination').innerHTML = '';
        }
    } catch (error) {
        console.error('加载互动问答数据失败:', error);
        container.innerHTML = '<div class="empty-state">加载失败，请稍后重试</div>';
        document.getElementById('qaPagination').innerHTML = '';
    }
}

/**
 * 搜索互动问答
 */
function searchQA() {
    const keyword = document.getElementById('qaSearchInput').value.trim();
    loadQAData(null, 1, keyword);
}

/**
 * 刷新互动问答数据（增量更新）
 */
async function refreshQAData() {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code') || '688456';
    
    const refreshBtn = document.querySelector('.refresh-btn');
    const originalText = refreshBtn.innerHTML;
    refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 刷新中...';
    refreshBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/stock/${code}/qa/fetch`, {
            method: 'POST'
        });
        const result = await response.json();
        
        if (result.success) {
            alert(result.message);
            // 重新加载数据
            loadQAData(code, 1, currentQAKeyword);
        } else {
            alert('刷新失败: ' + result.message);
        }
    } catch (error) {
        console.error('刷新失败:', error);
        alert('刷新失败，请稍后重试');
    } finally {
        refreshBtn.innerHTML = originalText;
        refreshBtn.disabled = false;
    }
}

/**
 * 高亮显示关键字
 */
function highlightKeyword(text, keyword) {
    if (!keyword || !text) {
        return text || '';
    }
    
    const regex = new RegExp(`(${keyword})`, 'gi');
    return text.replace(regex, '<span class="highlight">$1</span>');
}

/**
 * 渲染互动问答数据（支持关键字高亮）
 */
function renderQAData(qaList, keyword = '') {
    const container = document.getElementById('qaContainer');
    
    if (!qaList || qaList.length === 0) {
        container.innerHTML = '<div class="empty-state">暂无互动问答数据</div>';
        return;
    }
    
    let html = '';
    
    qaList.forEach((item, index) => {
        const hasAnswer = item.answer && item.answer.trim();
        const askTime = formatDateTime(item.ask_time);
        const answerTime = item.answer_time ? formatDateTime(item.answer_time) : '';
        
        // 高亮关键字
        const highlightedQuestion = highlightKeyword(item.question, keyword);
        const highlightedAnswer = highlightKeyword(item.answer, keyword);
        
        html += `
            <div class="qa-item">
                <!-- 提问部分（一行显示） -->
                <div class="qa-question-row">
                    <span class="qa-icon question-icon">
                        <i class="fas fa-user-circle"></i>
                    </span>
                    <span class="qa-label">问:</span>
                    <span class="qa-meta">
                        <span class="qa-ask-user">${item.ask_user || '投资者'}</span>
                        <span class="qa-divider">|</span>
                        <span class="qa-ask-time">${askTime}</span>
                    </span>
                    <span class="qa-content-text">${highlightedQuestion || '--'}</span>
                </div>
                
                <!-- 回答部分（一行显示） -->
                ${hasAnswer ? `
                <div class="qa-answer-row">
                    <span class="qa-icon answer-icon">
                        <i class="fas fa-building"></i>
                    </span>
                    <span class="qa-label">答:</span>
                    <span class="qa-meta">
                        <span class="qa-answer-source">${item.code || '公司'}</span>
                        ${answerTime ? `<span class="qa-divider">|</span><span class="qa-answer-time">${answerTime}</span>` : ''}
                    </span>
                    <span class="qa-content-text">${highlightedAnswer}</span>
                </div>
                ` : ''}
            </div>
        `;
    });
    
    container.innerHTML = html;
}

/**
 * 渲染分页控件
 */
function renderPagination(data) {
    const pagination = document.getElementById('qaPagination');
    const { total, total_pages, current_page, limit, keyword } = data;
    
    if (total <= limit) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = `
        <div class="pagination-info">
            共 ${total} 条记录，当前第 ${current_page}/${total_pages} 页
        </div>
        <div class="pagination-buttons">
    `;
    
    // 上一页
    if (current_page > 1) {
        html += `<button class="page-btn" onclick="loadQAData(null, ${current_page - 1}, '${keyword}')">
            <i class="fas fa-chevron-left"></i> 上一页
        </button>`;
    } else {
        html += `<button class="page-btn disabled"><i class="fas fa-chevron-left"></i> 上一页</button>`;
    }
    
    // 页码按钮（最多显示5个）
    const visiblePages = 5;
    let startPage = Math.max(1, current_page - Math.floor(visiblePages / 2));
    let endPage = Math.min(total_pages, startPage + visiblePages - 1);
    
    if (endPage - startPage + 1 < visiblePages) {
        startPage = Math.max(1, endPage - visiblePages + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        if (i === current_page) {
            html += `<button class="page-btn active">${i}</button>`;
        } else {
            html += `<button class="page-btn" onclick="loadQAData(null, ${i}, '${keyword}')">${i}</button>`;
        }
    }
    
    // 下一页
    if (current_page < total_pages) {
        html += `<button class="page-btn" onclick="loadQAData(null, ${current_page + 1}, '${keyword}')">
            下一页 <i class="fas fa-chevron-right"></i>
        </button>`;
    } else {
        html += `<button class="page-btn disabled">下一页 <i class="fas fa-chevron-right"></i></button>`;
    }
    
    html += '</div>';
    
    pagination.innerHTML = html;
}

/**
 * 格式化日期时间
 * 修复时区转换问题：手动解析日期字符串，避免JavaScript的时区转换导致日期偏移
 */
function formatDateTime(datetimeStr) {
    if (!datetimeStr) return '';
    
    try {
        // 优先手动解析日期字符串，避免时区转换问题
        
        // 格式1：2026-05-14 16:31:54 或 2026-05-14 16:31
        const datetimeMatch = datetimeStr.match(/^(\d{4})[-/](\d{2})[-/](\d{2})\s+(\d{2}):(\d{2})(?::(\d{2}))?$/);
        if (datetimeMatch) {
            const year = datetimeMatch[1];
            const month = datetimeMatch[2];
            const day = datetimeMatch[3];
            const hour = datetimeMatch[4];
            const minute = datetimeMatch[5];
            return `${year}/${month}/${day} ${hour}:${minute}`;
        }
        
        // 格式2：RFC 822 格式（如 Thu, 14 May 2026 16:31:54 GMT）
        const rfc822Match = datetimeStr.match(/^[A-Za-z]{3},\s*(\d{2})\s+([A-Za-z]{3})\s+(\d{4})\s+(\d{2}):(\d{2}):(\d{2})\s+GMT$/);
        if (rfc822Match) {
            const day = rfc822Match[1];
            const monthName = rfc822Match[2];
            const year = rfc822Match[3];
            const hour = rfc822Match[4];
            const minute = rfc822Match[5];
            
            // 将月份名称转换为数字
            const monthMap = {
                'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
            };
            const month = monthMap[monthName] || '01';
            
            return `${year}/${month}/${day} ${hour}:${minute}`;
        }
        
        // 格式3：数字格式 20240101120000
        if (datetimeStr.length === 14) {
            const year = datetimeStr.substring(0, 4);
            const month = datetimeStr.substring(4, 6);
            const day = datetimeStr.substring(6, 8);
            const hour = datetimeStr.substring(8, 10);
            const minute = datetimeStr.substring(10, 12);
            return `${year}/${month}/${day} ${hour}:${minute}`;
        }
        
        // 最后尝试使用Date对象（作为后备）
        const date = new Date(datetimeStr);
        if (!isNaN(date.getTime())) {
            return date.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
        
        return datetimeStr;
    } catch (e) {
        return datetimeStr;
    }
}