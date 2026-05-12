// 验证主题切换功能
console.log('=== 主题切换验证 ===');

// 检查主题列表
const themes = ['light', 'dark', 'gold'];
console.log('支持的主题:', themes);

// 模拟切换主题
function verifyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const appliedTheme = document.documentElement.getAttribute('data-theme');
    console.log(`设置主题: ${theme}, 实际应用: ${appliedTheme}`);
    
    // 检查CSS变量是否生效
    const computedStyle = window.getComputedStyle(document.body);
    const bgColor = computedStyle.getPropertyValue('--bg-secondary');
    console.log(`主题 ${theme} 的背景色: ${bgColor}`);
}

// 测试所有主题
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成，开始验证主题切换...');
    
    // 测试light主题
    verifyTheme('light');
    
    // 延迟测试dark主题
    setTimeout(() => {
        verifyTheme('dark');
        
        // 延迟测试gold主题
        setTimeout(() => {
            verifyTheme('gold');
            console.log('=== 主题验证完成 ===');
        }, 1000);
    }, 1000);
});
