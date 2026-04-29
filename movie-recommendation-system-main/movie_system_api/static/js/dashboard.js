// Dashboard 全局功能
let currentPage = 1;
const itemsPerPage = 10;

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 显示提示信息
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container-fluid');
    container.insertBefore(alertDiv, container.firstChild);
    
    // 自动消失
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

// 加载仪表板统计数据
async function loadDashboardStats() {
    try {
        console.log('正在加载仪表盘统计数据...');
        const response = await fetch('/api/dashboard/stats');

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('仪表盘统计数据响应:', data);

        if (data.error) {
            throw new Error(data.error);
        }

        // 更新DOM元素 - 添加更详细的日志
        const totalMoviesElem = document.getElementById('totalMovies');
        const totalUsersElem = document.getElementById('totalUsers');
        const totalRatingsElem = document.getElementById('totalRatings');
        const totalHistoryElem = document.getElementById('totalHistory');

        console.log('找到的元素:', {
            totalMovies: totalMoviesElem,
            totalUsers: totalUsersElem,
            totalRatings: totalRatingsElem,
            totalHistory: totalHistoryElem
        });

        if (totalMoviesElem) {
            totalMoviesElem.textContent = data.total_movies || 0;
            console.log('设置电影数:', data.total_movies);
        }
        if (totalUsersElem) {
            totalUsersElem.textContent = data.total_users || 0;
            console.log('设置用户数:', data.total_users);
        }
        if (totalRatingsElem) {
            totalRatingsElem.textContent = data.total_ratings || 0;
            console.log('设置评分数:', data.total_ratings);
        }
        if (totalHistoryElem) {
            totalHistoryElem.textContent = data.total_history || 0;
            console.log('设置历史记录数:', data.total_history);
        }

        console.log('仪表盘统计数据更新完成');
    } catch (error) {
        console.error('加载统计数据失败:', error);
        // 设置默认值
        document.getElementById('totalMovies').textContent = 0;
        document.getElementById('totalUsers').textContent = 0;
        document.getElementById('totalRatings').textContent = 0;
        document.getElementById('totalHistory').textContent = 0;
    }
}

// 加载图表数据
async function loadChartData() {
    try {
        const response = await fetch('/api/dashboard/chart-data');
        const data = await response.json();
        
        if (response.ok) {
            renderChart(data);
        }
    } catch (error) {
        console.error('加载图表数据失败:', error);
    }
}

// 在 dashboard.js 中找到 renderChart 函数，替换为以下代码：

// 渲染图表 - 美化版本
function renderChart(data) {
    const ctx = document.getElementById('dataChart').getContext('2d');

    // 销毁现有图表实例（如果存在）
    if (window.dataChartInstance) {
        window.dataChartInstance.destroy();
    }

    // 创建新的图表实例
    window.dataChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels || ['1月', '2月', '3月', '4月', '5月', '6月'],
            datasets: [{
                label: '新增用户',
                data: data.users || [65, 59, 80, 81, 56, 72],
                borderColor: '#8B7355', // 使用主题棕色
                backgroundColor: 'rgba(139, 115, 85, 0.1)',
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                pointBackgroundColor: '#8B7355',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8
            }, {
                label: '新增电影',
                data: data.movies || [28, 48, 40, 45, 36, 60],
                borderColor: '#696969', // 使用主题灰色
                backgroundColor: 'rgba(105, 105, 105, 0.1)',
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                pointBackgroundColor: '#696969',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: {
                            size: 14,
                            weight: '600',
                            family: "'Segoe UI', 'Microsoft YaHei', sans-serif"
                        },
                        color: '#2c3e50'
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(44, 62, 80, 0.95)',
                    titleFont: {
                        size: 13,
                        weight: '600'
                    },
                    bodyFont: {
                        size: 13,
                        weight: '500'
                    },
                    padding: 12,
                    cornerRadius: 8,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += context.parsed.y;
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: '时间',
                        color: '#2c3e50',
                        font: {
                            size: 14,
                            weight: '600',
                            family: "'Segoe UI', 'Microsoft YaHei', sans-serif"
                        },
                        padding: {top: 10, bottom: 5}
                    },
                    grid: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#5d6d7e',
                        font: {
                            size: 13,
                            weight: '500',
                            family: "'Segoe UI', 'Microsoft YaHei', sans-serif"
                        },
                        padding: 8
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: '数量',
                        color: '#2c3e50',
                        font: {
                            size: 14,
                            weight: '600',
                            family: "'Segoe UI', 'Microsoft YaHei', sans-serif"
                        },
                        padding: {top: 5, bottom: 10}
                    },
                    grid: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#5d6d7e',
                        font: {
                            size: 13,
                            weight: '500',
                            family: "'Segoe UI', 'Microsoft YaHei', sans-serif"
                        },
                        padding: 8
                    },
                    suggestedMin: 0
                }
            },
            interaction: {
                intersect: false,
                mode: 'nearest'
            },
            animations: {
                tension: {
                    duration: 1000,
                    easing: 'linear'
                }
            }
        }
    });
}

// 加载最近活动
async function loadRecentActivities() {
    try {
        const response = await fetch('/api/dashboard/recent-activities');
        const data = await response.json();
        
        const container = document.getElementById('recentActivities');
        
        if (response.ok && data.activities) {
            container.innerHTML = data.activities.map(activity => `
                <div class="activity-item">
                    <div class="activity-icon">
                        <i class="fas ${getActivityIcon(activity.type)}"></i>
                    </div>
                    <div class="activity-content">
                        <div class="activity-title">${activity.title}</div>
                        <div class="activity-time">${formatTime(activity.time)}</div>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<div class="text-center text-muted py-3">暂无活动数据</div>';
        }
    } catch (error) {
        console.error('加载活动数据失败:', error);
        document.getElementById('recentActivities').innerHTML = 
            '<div class="text-center text-muted py-3">加载失败</div>';
    }
}

// 获取活动图标
function getActivityIcon(type) {
    const icons = {
        'rating': 'fa-star',
        'user': 'fa-user-plus',
        'movie': 'fa-video',
        'history': 'fa-history'
    };
    return icons[type] || 'fa-bell';
}

// 格式化时间
function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) { // 1分钟内
        return '刚刚';
    } else if (diff < 3600000) { // 1小时内
        return `${Math.floor(diff / 60000)}分钟前`;
    } else if (diff < 86400000) { // 1天内
        return `${Math.floor(diff / 3600000)}小时前`;
    } else {
        return date.toLocaleDateString();
    }
}

// 加载热门电影
async function loadTopMovies() {
    try {
        const response = await fetch('/api/movies/top?limit=5');
        const data = await response.json();
        
        const container = document.getElementById('topMovies');
        
        if (response.ok && data.movies) {
            container.innerHTML = data.movies.map(movie => `
                <div class="d-flex align-items-center mb-4">
                            <div class="movie-poster me-3 shadow-sm rounded" style="width: 65px; height: 90px; overflow: hidden;">
                                ${movie.poster_url ? 
                                    `<img src="${movie.poster_url}" alt="${movie.title}" style="width: 100%; height: 100%; object-fit: cover; object-position: top;" referrerpolicy="no-referrer" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                                     <div class="w-100 h-100 bg-light align-items-center justify-content-center" style="display: none;"><i class="fas fa-film text-muted"></i></div>` : 
                                    '<div class="w-100 h-100 bg-light d-flex align-items-center justify-content-center"><i class="fas fa-film text-muted"></i></div>'}
                            </div>
                    <div class="flex-grow-1">
                        <h6 class="mb-1">${movie.title}</h6>
                        <div class="d-flex align-items-center">
                            <span class="rating-stars me-2">
                                ${generateStarRating(movie.avg_score)}
                            </span>
                            <small class="text-muted">${movie.avg_score || '暂无评分'}</small>
                        </div>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<div class="text-center text-muted py-3">暂无电影数据</div>';
        }
    } catch (error) {
        console.error('加载热门电影失败:', error);
    }
}

// 生成星级评分
function generateStarRating(score) {
    if (!score) return '暂无评分';
    
    const fullStars = Math.floor(score);
    const halfStar = score % 1 >= 0.5;
    const emptyStars = 5 - fullStars - (halfStar ? 1 : 0);
    
    let stars = '';
    for (let i = 0; i < fullStars; i++) {
        stars += '<i class="fas fa-star"></i>';
    }
    if (halfStar) {
        stars += '<i class="fas fa-star-half-alt"></i>';
    }
    for (let i = 0; i < emptyStars; i++) {
        stars += '<i class="far fa-star"></i>';
    }
    return stars;
}

// 加载最新用户
async function loadNewUsers() {
    try {
        const response = await fetch('/api/users/recent?limit=5');
        const data = await response.json();
        
        const container = document.getElementById('newUsers');
        
        if (response.ok && data.users) {
            container.innerHTML = data.users.map(user => `
                <div class="d-flex align-items-center mb-3">
                    <div class="bg-primary rounded-circle d-flex align-items-center justify-content-center me-3" 
                         style="width: 40px; height: 40px; overflow: hidden;">
                        ${user.avatar_url ? `<img src="${user.avatar_url}" alt="avatar" style="width: 100%; height: 100%; object-fit: cover;" referrerpolicy="no-referrer">` : '<i class="fas fa-user text-white"></i>'}
                    </div>
                    <div class="flex-grow-1">
                        <h6 class="mb-1">${user.nickname || user.username}</h6>
                        <small class="text-muted">注册时间: ${formatTime(user.register_date)}</small>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<div class="text-center text-muted py-3">暂无用户数据</div>';
        }
    } catch (error) {
        console.error('加载最新用户失败:', error);
    }
}

// 电影管理功能
async function loadMovies(page = 1) {
    try {
        const search = document.getElementById('searchInput').value;
        const year = document.getElementById('yearFilter').value;
        const genre = document.getElementById('genreFilter').value;
        
        let url = `/api/movies?page=${page}&limit=${itemsPerPage}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;
        if (year) url += `&year=${year}`;
        if (genre) url += `&genre=${genre}`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        const tbody = document.getElementById('moviesTableBody');
        
        if (response.ok && data.movies && data.movies.length > 0) {
            tbody.innerHTML = data.movies.map(movie => `
                <tr>
                    <td>${movie.movie_id}</td>
                    <td>
                        <div class="d-flex align-items-center">
                            ${movie.poster_url ? 
                                `<img src="${movie.poster_url}" class="me-3 rounded shadow-sm" style="width: 50px; height: 70px; object-fit: cover; object-position: top;" alt="poster" referrerpolicy="no-referrer" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                                 <div class="movie-poster me-3 rounded shadow-sm align-items-center justify-content-center bg-light" style="width: 50px; height: 70px; display: none;"><i class="fas fa-film text-muted"></i></div>` : 
                                `<div class="movie-poster me-3 rounded shadow-sm d-flex align-items-center justify-content-center bg-light" style="width: 50px; height: 70px;"><i class="fas fa-film text-muted"></i></div>`
                            }
                            <div>
                                <strong>${movie.title}</strong>
                                ${movie.description ? `<br><small class="text-muted">${movie.description.substring(0, 50)}...</small>` : ''}
                            </div>
                        </div>
                    </td>
                    <td>${movie.release_year || '-'}</td>
                    <td>${movie.language || '-'}</td>
                    <td>${movie.duration ? `${movie.duration}分钟` : '-'}</td>
                    <td>${movie.director || '-'}</td>
                    <td>${movie.genres ? movie.genres.map(g => `<span class="badge bg-secondary me-1">${g}</span>`).join('') : '-'}</td>
                    <td>
                        <div class="rating-stars">
                            ${generateStarRating(movie.avg_score)}
                        </div>
                        <small class="text-muted">${movie.avg_score || '暂无'}</small>
                    </td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary" onclick="editMovie(${movie.movie_id})" title="编辑">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-outline-danger" onclick="deleteMovie(${movie.movie_id})" title="删除">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');
            
            renderPagination(data.total, page, 'movies');
        } else {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" class="text-center py-4 text-muted">
                        <i class="fas fa-film fa-2x mb-3 d-block"></i>
                        暂无电影数据
                    </td>
                </tr>
            `;
        }
    } catch (error) {
        console.error('加载电影失败:', error);
        showAlert('加载电影数据失败', 'danger');
    }
}

// 渲染分页
function renderPagination(totalItems, currentPage, type) {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    const pagination = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // 上一页
    if (currentPage > 1) {
        html += `<li class="page-item"><a class="page-link" href="javascript:void(0)" onclick="changePage(${currentPage - 1}, '${type}')">上一页</a></li>`;
    }
    
    // 动态计算要显示的页码范围 (显示当前页的前后2页)
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
        html += `<li class="page-item"><a class="page-link" href="javascript:void(0)" onclick="changePage(1, '${type}')">1</a></li>`;
        if (startPage > 2) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }

    // 页码
    for (let i = startPage; i <= endPage; i++) {
        if (i === currentPage) {
            html += `<li class="page-item active"><a class="page-link" href="javascript:void(0)">${i}</a></li>`;
        } else {
            html += `<li class="page-item"><a class="page-link" href="javascript:void(0)" onclick="changePage(${i}, '${type}')">${i}</a></li>`;
        }
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        html += `<li class="page-item"><a class="page-link" href="javascript:void(0)" onclick="changePage(${totalPages}, '${type}')">${totalPages}</a></li>`;
    }

    // 下一页
    if (currentPage < totalPages) {
        html += `<li class="page-item"><a class="page-link" href="javascript:void(0)" onclick="changePage(${currentPage + 1}, '${type}')">下一页</a></li>`;
    }
    
    pagination.innerHTML = html;
}

// 切换页面
function changePage(page, type) {
    currentPage = page;
    switch (type) {
        case 'movies':
            loadMovies(page);
            break;
        // 可以添加其他类型的分页处理
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM 加载完成，开始初始化仪表板...');

    // 初始化仪表板数据
    if (document.getElementById('dataChart')) {
        console.log('检测到仪表板页面，开始加载数据...');

        // 先加载统计数据
        loadDashboardStats();

        // 然后加载其他数据
        setTimeout(() => {
            loadChartData();
            loadRecentActivities();
            loadTopMovies();
            loadNewUsers();
        }, 100);

        // 刷新按钮
        document.getElementById('refreshBtn')?.addEventListener('click', function() {
            console.log('手动刷新数据...');
            loadDashboardStats();
            loadChartData();
            loadRecentActivities();
            loadTopMovies();
            loadNewUsers();
            showAlert('数据已刷新', 'success');
        });
    }

    // 导出按钮
    document.getElementById('exportBtn')?.addEventListener('click', async function() {
        try {
            showAlert('正在生成数据报告，请稍候...', 'info');
            
            // 获取需要导出的数据
            const [statsRes, topMoviesRes, recentUsersRes, activitiesRes] = await Promise.all([
                fetch('/api/dashboard/stats'),
                fetch('/api/movies/top?limit=5'),
                fetch('/api/users/recent?limit=5'),
                fetch('/api/dashboard/recent-activities')
            ]);
            
            const stats = await statsRes.json();
            const topMovies = await topMoviesRes.json();
            const recentUsers = await recentUsersRes.json();
            const activities = await activitiesRes.json();
            
            // 构建 CSV 内容
            let csv = '\uFEFF'; // 添加 BOM 头，防止中文乱码
            csv += `=== 电影系统数据报告 ===\n生成时间,${new Date().toLocaleString()}\n\n`;
            
            // 1. 核心统计
            csv += `--- 核心统计 ---\n`;
            csv += `指标,数值\n`;
            csv += `总电影数,${stats.total_movies || 0}\n`;
            csv += `总用户数,${stats.total_users || 0}\n`;
            csv += `总评分数,${stats.total_ratings || 0}\n`;
            csv += `总播放记录,${stats.total_history || 0}\n\n`;
            
            // 2. 热门电影
            csv += `--- 热门电影 Top 5 ---\n`;
            csv += `排名,电影名称,平均评分\n`;
            if (topMovies.movies && topMovies.movies.length > 0) {
                topMovies.movies.forEach((movie, index) => {
                    const title = movie.title.replace(/,/g, '，'); // 处理逗号
                    csv += `${index + 1},${title},${movie.avg_score || '暂无'}\n`;
                });
            } else {
                csv += `暂无数据\n`;
            }
            csv += `\n`;
            
            // 3. 最新注册用户
            csv += `--- 最新注册用户 ---\n`;
            csv += `用户名,注册时间\n`;
            if (recentUsers.users && recentUsers.users.length > 0) {
                recentUsers.users.forEach(user => {
                    csv += `${user.username},${user.register_date || '未知'}\n`;
                });
            } else {
                csv += `暂无数据\n`;
            }
            csv += `\n`;
            
            // 4. 最近活动
            csv += `--- 最近活动 ---\n`;
            csv += `时间,活动类型,详情\n`;
            if (activities.activities && activities.activities.length > 0) {
                activities.activities.forEach(act => {
                    const title = (act.title || '').replace(/,/g, '，');
                    csv += `${act.time},${act.type},${title}\n`;
                });
            } else {
                csv += `暂无数据\n`;
            }
            
            // 创建 Blob 并下载
            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            
            const dateStr = new Date().toISOString().split('T')[0];
            link.setAttribute('href', url);
            link.setAttribute('download', `电影系统报告_${dateStr}.csv`);
            link.style.visibility = 'hidden';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            showAlert('报告导出成功！', 'success');
        } catch (error) {
            console.error('导出失败:', error);
            showAlert('导出报告失败，请稍后重试', 'danger');
        }
    });
});

// 电影编辑和删除功能（需要在具体页面中实现）
async function editMovie(movieId) {
    // 实现编辑电影逻辑
    showAlert(`编辑电影 ID: ${movieId}`, 'info');
}

async function deleteMovie(movieId) {
    if (confirm('确定要删除这部电影吗？此操作不可撤销。')) {
        try {
            const response = await fetch(`/api/movies/${movieId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                showAlert('电影删除成功', 'success');
                loadMovies(currentPage);
            } else {
                showAlert('删除失败', 'danger');
            }
        } catch (error) {
            console.error('删除电影失败:', error);
            showAlert('删除失败', 'danger');
        }
    }
}

