// 测试主题切换逻辑
function testThemeToggle() {
    const themes = ['light', 'dark', 'gold'];
    let currentIndex = 0;
    
    // 模拟切换主题
    setInterval(() => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newIndex = (themes.indexOf(currentTheme) + 1) % themes.length;
        const newTheme = themes[newIndex];
        
        document.documentElement.setAttribute('data-theme', newTheme);
        console.log(`切换到主题: ${newTheme}`);
        
        // 更新图标
        const icon = document.getElementById('themeIcon');
        if (icon) {
            if (newTheme === 'dark') {
                icon.className = 'fas fa-sun';
            } else if (newTheme === 'gold') {
                icon.className = 'fas fa-crown';
            } else {
                icon.className = 'fas fa-moon';
            }
        }
    }, 2000);
}

// 页面加载后自动测试
document.addEventListener('DOMContentLoaded', function() {
    testThemeToggle();
});
