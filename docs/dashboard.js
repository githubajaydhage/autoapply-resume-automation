// Dashboard Configuration (Enhanced)
const CONFIG = {
    dataPath: 'data/dashboard_data.json',
    refreshInterval: 300000, // 5 minutes
    autoRefresh: true,
    schedules: {
        shweta: ['10:00', '15:00', '20:00'],      // Shweta's times
        yogeshwari: ['10:30', '15:30', '20:30'],  // Yogeshwari's times
        ajay: ['Disabled']                         // Ajay's cron is disabled
    },
    users: ['ajay', 'shweta', 'yogeshwari']
};

// Global state
let dashboardData = null;
let currentUser = 'all';
let applicationsChart = null;
let statusChart = null;
let emailStatusChart = null;
let refreshTimer = null;
let countdownInterval = null;

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
    setupUserTabs();
    setupEventListeners();
    updateNextRun();
    startCountdown();
    
    // Auto-refresh
    if (CONFIG.autoRefresh) {
        startAutoRefresh();
    }
});

// Setup Event Listeners
function setupEventListeners() {
    // Export button
    const exportBtn = document.getElementById('export-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportToCSV);
    }
    
    // Refresh button
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            loadDashboardData();
            showToast('Dashboard refreshed!');
        });
    }
}

// Setup User Tab Click Handlers
function setupUserTabs() {
    const tabs = document.querySelectorAll('.user-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentUser = tab.dataset.user;
            if (dashboardData) {
                updateDashboard(dashboardData);
            }
        });
    });
}

// Start Auto Refresh
function startAutoRefresh() {
    if (refreshTimer) clearInterval(refreshTimer);
    refreshTimer = setInterval(() => {
        loadDashboardData();
        updateRefreshIndicator();
    }, CONFIG.refreshInterval);
    updateRefreshIndicator();
}

// Update Refresh Indicator
function updateRefreshIndicator() {
    const indicator = document.getElementById('auto-refresh-status');
    if (indicator) {
        indicator.textContent = `Auto-refresh: ${CONFIG.refreshInterval / 60000}min`;
    }
}

// Load Dashboard Data
async function loadDashboardData() {
    try {
        const response = await fetch(CONFIG.dataPath + '?t=' + Date.now());
        if (!response.ok) throw new Error('Data not found');
        dashboardData = await response.json();
        updateDashboard(dashboardData);
        checkAlerts(dashboardData);
    } catch (error) {
        console.log('Loading sample data...', error);
        dashboardData = getSampleData();
        updateDashboard(dashboardData);
    }
}

// Check and Display Alerts
function checkAlerts(data) {
    const alertsContainer = document.getElementById('alerts-container');
    if (!alertsContainer) return;
    
    let alerts = [];
    
    if (data.alerts?.highBounceRate) {
        alerts.push({
            type: 'warning',
            icon: '⚠️',
            message: `High bounce rate detected: ${data.alerts.bounceRateValue}% of emails are bouncing`
        });
    }
    
    if (data.alerts?.noJobsToday) {
        alerts.push({
            type: 'info',
            icon: '📋',
            message: 'No new jobs discovered today. Next scrape scheduled soon.'
        });
    }
    
    if (alerts.length > 0) {
        alertsContainer.innerHTML = alerts.map(alert => `
            <div class="alert alert-${alert.type}">
                <span class="alert-icon">${alert.icon}</span>
                <span class="alert-message">${alert.message}</span>
                <button class="alert-dismiss" onclick="this.parentElement.remove()">×</button>
            </div>
        `).join('');
        alertsContainer.style.display = 'block';
    } else {
        alertsContainer.style.display = 'none';
    }
}

// Calculate aggregated stats for all users
function getAggregatedStats(data) {
    if (!data.users) return data.stats || {};
    
    const stats = {
        jobsToday: 0,
        totalApplications: 0,
        emailsSent: 0,
        emailsSuccess: 0,
        emailsBounced: 0,
        companiesFound: 0,
        hrContacts: 0,
        responseRate: 0,
        bounceRate: 0,
        successRate: 0
    };
    
    let totalEmails = 0;
    
    Object.values(data.users).forEach(userData => {
        if (userData.stats) {
            stats.jobsToday += userData.stats.jobsToday || 0;
            stats.totalApplications += userData.stats.totalApplications || 0;
            stats.emailsSent += userData.stats.emailsSent || 0;
            stats.emailsSuccess += userData.stats.emailsSuccess || 0;
            stats.emailsBounced += userData.stats.emailsBounced || 0;
            stats.companiesFound += userData.stats.companiesFound || 0;
            stats.hrContacts += userData.stats.hrContacts || 0;
            totalEmails += userData.stats.emailsSent || 0;
        }
    });
    
    stats.bounceRate = totalEmails > 0 ? Math.round((stats.emailsBounced / totalEmails) * 100) : 0;
    stats.successRate = totalEmails > 0 ? Math.round((stats.emailsSuccess / totalEmails) * 100) : 0;
    
    return stats;
}

// Get aggregated trends
function getAggregatedTrends(data) {
    if (!data.users) return { change: 0, direction: 'same' };
    
    let totalToday = 0, totalYesterday = 0;
    
    Object.values(data.users).forEach(userData => {
        if (userData.trends) {
            totalToday += userData.trends.today || 0;
            totalYesterday += userData.trends.yesterday || 0;
        }
    });
    
    const change = totalYesterday > 0 
        ? Math.round(((totalToday - totalYesterday) / totalYesterday) * 100) 
        : (totalToday > 0 ? 100 : 0);
    
    return {
        today: totalToday,
        yesterday: totalYesterday,
        change: change,
        direction: change > 0 ? 'up' : (change < 0 ? 'down' : 'same')
    };
}

// Update Dashboard with Data
function updateDashboard(data) {
    // Update last updated timestamp
    document.getElementById('last-updated').textContent = 
        `Last updated: ${data.lastUpdated || new Date().toLocaleString()}`;
    
    // Update user tab counts
    updateUserTabCounts(data);
    
    // Get stats based on current filter
    let stats, trends;
    if (currentUser === 'all') {
        stats = data.users ? getAggregatedStats(data) : data.stats;
        trends = getAggregatedTrends(data);
    } else {
        stats = data.users?.[currentUser]?.stats || data.stats;
        trends = data.users?.[currentUser]?.trends || { direction: 'same', change: 0 };
    }
    
    // Update stats with animations
    animateNumber('jobs-count', stats?.jobsToday || 0);
    animateNumber('applications-count', stats?.totalApplications || 0);
    animateNumber('emails-count', stats?.emailsSent || 0);
    animateNumber('companies-count', stats?.companiesFound || 0);
    animateNumber('hr-count', stats?.hrContacts || 0);
    animateNumber('success-count', stats?.emailsSuccess || 0);
    animateNumber('bounced-count', stats?.emailsBounced || 0);
    
    // Update percentages
    const responseRate = stats?.responseRate || 0;
    document.getElementById('response-rate').textContent = `${responseRate}%`;
    
    const bounceRate = stats?.bounceRate || 0;
    const bounceEl = document.getElementById('bounce-rate');
    if (bounceEl) {
        bounceEl.textContent = `${bounceRate}%`;
        bounceEl.className = bounceRate > 20 ? 'stat-number danger' : 'stat-number';
    }
    
    const successRate = stats?.successRate || 0;
    const successEl = document.getElementById('success-rate');
    if (successEl) {
        successEl.textContent = `${successRate}%`;
    }
    
    // Update trend indicators
    updateTrendIndicator('applications-trend', trends);
    
    // Get time series data
    let timeSeriesData = [];
    if (currentUser === 'all' && data.users) {
        timeSeriesData = mergeTimeSeries(data.users);
    } else if (data.users?.[currentUser]) {
        timeSeriesData = data.users[currentUser].applicationsOverTime || [];
    } else {
        timeSeriesData = data.applicationsOverTime || [];
    }
    
    // Get status data
    let statusData = {};
    if (currentUser === 'all' && data.users) {
        statusData = mergeStatusData(data.users);
    } else if (data.users?.[currentUser]) {
        statusData = data.users[currentUser].applicationStatus || {};
    } else {
        statusData = data.applicationStatus || {};
    }
    
    // Get email status data
    let emailStatusData = {};
    if (currentUser === 'all' && data.users) {
        emailStatusData = mergeEmailStatusData(data.users);
    } else if (data.users?.[currentUser]) {
        emailStatusData = data.users[currentUser].emailStatus || {};
    }
    
    // Update charts
    updateApplicationsChart(timeSeriesData);
    updateStatusChart(statusData);
    updateEmailStatusChart(emailStatusData);
    
    // Update top companies
    updateTopCompanies(data.topCompanies || [], currentUser);
    
    // Filter activities by user
    const filteredJobs = filterByUser(data.recentJobs || [], currentUser);
    const filteredEmails = filterByUser(data.recentEmails || [], currentUser);
    const filteredCompanies = filterByUser(data.companies || [], currentUser);
    
    // Update recent activities
    updateRecentJobs(filteredJobs);
    updateRecentEmails(filteredEmails);
    updateCompaniesTable(filteredCompanies);
}

// Update trend indicator
function updateTrendIndicator(elementId, trends) {
    const el = document.getElementById(elementId);
    if (!el) return;
    
    const { direction, change } = trends;
    let icon = '→';
    let className = 'trend-same';
    
    if (direction === 'up') {
        icon = '↑';
        className = 'trend-up';
    } else if (direction === 'down') {
        icon = '↓';
        className = 'trend-down';
    }
    
    el.innerHTML = `<span class="${className}">${icon} ${Math.abs(change)}%</span>`;
}

// Update user tab counts
function updateUserTabCounts(data) {
    if (!data.users) return;
    
    let totalApplications = 0;
    CONFIG.users.forEach(user => {
        const count = data.users[user]?.stats?.totalApplications || 0;
        const countEl = document.getElementById(`count-${user}`);
        if (countEl) countEl.textContent = count;
        totalApplications += count;
    });
    
    const allCountEl = document.getElementById('count-all');
    if (allCountEl) allCountEl.textContent = totalApplications;
}

// Filter array by user
function filterByUser(items, user) {
    if (user === 'all') return items;
    return items.filter(item => item.user === user);
}

// Merge time series data from all users
function mergeTimeSeries(users) {
    const dateMap = {};
    
    Object.values(users).forEach(userData => {
        (userData.applicationsOverTime || []).forEach(item => {
            if (!dateMap[item.date]) dateMap[item.date] = 0;
            dateMap[item.date] += item.count;
        });
    });
    
    return Object.entries(dateMap)
        .map(([date, count]) => ({ date, count }))
        .sort((a, b) => a.date.localeCompare(b.date));
}

// Merge status data from all users
function mergeStatusData(users) {
    const merged = { applied: 0, contacted: 0, interviewing: 0, rejected: 0, offered: 0 };
    
    Object.values(users).forEach(userData => {
        const status = userData.applicationStatus || {};
        Object.keys(merged).forEach(key => {
            merged[key] += status[key] || 0;
        });
    });
    
    return merged;
}

// Merge email status data from all users
function mergeEmailStatusData(users) {
    const merged = { sent: 0, bounced: 0, opened: 0, replied: 0, failed: 0 };
    
    Object.values(users).forEach(userData => {
        const status = userData.emailStatus || {};
        Object.keys(merged).forEach(key => {
            merged[key] += status[key] || 0;
        });
    });
    
    return merged;
}

// Animate number counter
function animateNumber(elementId, targetValue) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const duration = 1000;
    const steps = 30;
    const stepValue = targetValue / steps;
    let current = 0;
    
    const interval = setInterval(() => {
        current += stepValue;
        if (current >= targetValue) {
            element.textContent = formatNumber(targetValue);
            clearInterval(interval);
        } else {
            element.textContent = formatNumber(Math.floor(current));
        }
    }, duration / steps);
}

// Format number with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// Update Applications Over Time Chart
function updateApplicationsChart(data) {
    const ctx = document.getElementById('applicationsChart')?.getContext('2d');
    if (!ctx) return;
    
    if (applicationsChart) applicationsChart.destroy();
    
    applicationsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => d.date),
            datasets: [{
                label: 'Applications',
                data: data.map(d => d.count),
                borderColor: '#6366f1',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: '#6366f1'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } },
                y: { beginAtZero: true, grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } }
            }
        }
    });
}

// Update Application Status Chart
function updateStatusChart(data) {
    const ctx = document.getElementById('statusChart')?.getContext('2d');
    if (!ctx) return;
    
    if (statusChart) statusChart.destroy();
    
    statusChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Applied', 'Contacted', 'Interviewing', 'Rejected', 'Offered'],
            datasets: [{
                data: [data.applied || 0, data.contacted || 0, data.interviewing || 0, data.rejected || 0, data.offered || 0],
                backgroundColor: ['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'right', labels: { color: '#f8fafc', padding: 20 } } },
            cutout: '60%'
        }
    });
}

// Update Email Status Chart
function updateEmailStatusChart(data) {
    const ctx = document.getElementById('emailStatusChart')?.getContext('2d');
    if (!ctx) return;
    
    if (emailStatusChart) emailStatusChart.destroy();
    
    emailStatusChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Sent', 'Bounced', 'Failed'],
            datasets: [{
                data: [data.sent || 0, data.bounced || 0, data.failed || 0],
                backgroundColor: ['#10b981', '#ef4444', '#6b7280'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'right', labels: { color: '#f8fafc', padding: 15 } } }
        }
    });
}

// Update Top Companies
function updateTopCompanies(companies, user) {
    const container = document.getElementById('top-companies');
    if (!container) return;
    
    const filtered = user === 'all' ? companies : companies.filter(c => c.user === user);
    
    if (filtered.length === 0) {
        container.innerHTML = '<div class="loading">No companies contacted yet</div>';
        return;
    }
    
    container.innerHTML = filtered.slice(0, 10).map((company, i) => `
        <div class="top-company-item">
            <span class="rank">#${i + 1}</span>
            <span class="company-name">${escapeHtml(company.name)}</span>
            <span class="email-count">${company.count} emails</span>
        </div>
    `).join('');
}

// Update Recent Jobs List
function updateRecentJobs(jobs) {
    const container = document.getElementById('recent-jobs');
    if (!container) return;
    
    if (jobs.length === 0) {
        container.innerHTML = '<div class="loading">No jobs discovered yet</div>';
        return;
    }
    
    container.innerHTML = jobs.slice(0, 10).map(job => `
        <div class="activity-item">
            <div class="activity-item-content">
                <div class="activity-item-title">${escapeHtml(job.title)}</div>
                <div class="activity-item-meta">
                    ${job.user ? `<span class="user-badge ${job.user}">${job.user}</span> • ` : ''}
                    ${escapeHtml(job.company)} • ${escapeHtml(job.location || 'Remote')}
                </div>
            </div>
            <span class="activity-item-badge badge-info">${escapeHtml(job.source || 'Job Board')}</span>
        </div>
    `).join('');
}

// Update Recent Emails List
function updateRecentEmails(emails) {
    const container = document.getElementById('recent-emails');
    if (!container) return;
    
    if (emails.length === 0) {
        container.innerHTML = '<div class="loading">No emails sent yet</div>';
        return;
    }
    
    container.innerHTML = emails.slice(0, 10).map(email => {
        const statusClass = email.status === 'bounced' ? 'badge-danger' : 
                           email.status === 'sent' ? 'badge-success' : 'badge-pending';
        const statusText = email.status === 'bounced' ? 'Bounced' :
                          email.opened ? 'Opened' : 'Sent';
        
        return `
            <div class="activity-item">
                <div class="activity-item-content">
                    <div class="activity-item-title">${escapeHtml(email.recipient)}</div>
                    <div class="activity-item-meta">
                        ${email.user ? `<span class="user-badge ${email.user}">${email.user}</span> • ` : ''}
                        ${escapeHtml(email.company || '')} ${email.jobTitle ? `• ${escapeHtml(email.jobTitle)}` : ''}
                        • ${escapeHtml(email.date)}
                    </div>
                </div>
                <span class="activity-item-badge ${statusClass}">${statusText}</span>
            </div>
        `;
    }).join('');
}

// Update Companies Table
function updateCompaniesTable(companies) {
    const tbody = document.getElementById('companies-tbody');
    if (!tbody) return;
    
    if (companies.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">No companies discovered yet</td></tr>';
        return;
    }
    
    tbody.innerHTML = companies.slice(0, 20).map(company => `
        <tr>
            <td><span class="user-badge ${company.user || ''}">${escapeHtml(company.user || '-')}</span></td>
            <td>${escapeHtml(company.name)}</td>
            <td>${escapeHtml(company.hrContact || '-')}</td>
            <td>${escapeHtml(company.email || '-')}</td>
            <td><span class="status-pill status-${(company.status || 'applied').toLowerCase()}">${escapeHtml(company.status || 'Discovered')}</span></td>
        </tr>
    `).join('');
}

// Start Countdown Timer
function startCountdown() {
    if (countdownInterval) clearInterval(countdownInterval);
    countdownInterval = setInterval(updateNextRun, 1000);
}

// Calculate Next Run Time with Countdown
function updateNextRun() {
    const now = new Date();
    const istOffset = 5.5 * 60 * 60 * 1000;
    const nowIST = new Date(now.getTime() + istOffset);
    const currentMinutes = nowIST.getHours() * 60 + nowIST.getMinutes();
    const currentSeconds = nowIST.getSeconds();
    
    let allTimes = [];
    Object.entries(CONFIG.schedules).forEach(([user, times]) => {
        times.forEach(t => {
            if (t !== 'Disabled' && t.includes(':')) {
                const [h, m] = t.split(':').map(Number);
                allTimes.push({ user, time: t, minutes: h * 60 + m });
            }
        });
    });
    
    allTimes.sort((a, b) => a.minutes - b.minutes);
    
    let nextRun = allTimes.find(t => t.minutes > currentMinutes);
    let isTomorrow = false;
    
    if (!nextRun && allTimes.length > 0) {
        nextRun = allTimes[0];
        isTomorrow = true;
    }
    
    const nextRunEl = document.getElementById('next-run');
    const countdownEl = document.getElementById('countdown-timer');
    
    if (nextRun) {
        let diffMinutes = nextRun.minutes - currentMinutes;
        if (isTomorrow) diffMinutes += 24 * 60;
        
        const diffSeconds = diffMinutes * 60 - currentSeconds;
        const hours = Math.floor(diffSeconds / 3600);
        const mins = Math.floor((diffSeconds % 3600) / 60);
        const secs = diffSeconds % 60;
        
        if (nextRunEl) {
            nextRunEl.textContent = `${isTomorrow ? 'Tomorrow ' : ''}${nextRun.time} IST (${nextRun.user})`;
        }
        
        if (countdownEl) {
            countdownEl.textContent = `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
        }
    }
}

// Export to CSV
function exportToCSV() {
    if (!dashboardData) {
        showToast('No data to export');
        return;
    }
    
    // Build CSV content
    let csv = 'User,Jobs Today,Applications,Emails Sent,Success,Bounced,Companies,Response Rate\n';
    
    CONFIG.users.forEach(user => {
        const stats = dashboardData.users?.[user]?.stats || {};
        csv += `${user},${stats.jobsToday || 0},${stats.totalApplications || 0},${stats.emailsSent || 0},${stats.emailsSuccess || 0},${stats.emailsBounced || 0},${stats.companiesFound || 0},${stats.responseRate || 0}%\n`;
    });
    
    // Add totals
    const totals = getAggregatedStats(dashboardData);
    csv += `\nTotal,${totals.jobsToday},${totals.totalApplications},${totals.emailsSent},${totals.emailsSuccess},${totals.emailsBounced},${totals.companiesFound},${totals.responseRate}%\n`;
    
    // Download
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `job-automation-report-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
    
    showToast('Report exported successfully!');
}

// Show Toast Notification
function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Sample Data for Demo/Development
function getSampleData() {
    return {
        lastUpdated: new Date().toLocaleString(),
        alerts: { highBounceRate: false, bounceRateValue: 5, noJobsToday: false },
        topCompanies: [
            { name: 'TechCorp', count: 12, user: 'ajay' },
            { name: 'AI Solutions', count: 8, user: 'shweta' },
            { name: 'FinTech Ltd', count: 6, user: 'yogeshwari' }
        ],
        users: {
            ajay: {
                stats: { jobsToday: 23, totalApplications: 128, emailsSent: 95, emailsSuccess: 90, emailsBounced: 5, companiesFound: 42, hrContacts: 67, responseRate: 14, bounceRate: 5, successRate: 95 },
                emailStatus: { sent: 90, bounced: 5, opened: 25, replied: 10, failed: 0 },
                trends: { today: 12, yesterday: 10, change: 20, direction: 'up' },
                applicationsOverTime: [{ date: 'Dec 25', count: 8 }, { date: 'Dec 26', count: 12 }, { date: 'Dec 27', count: 9 }, { date: 'Dec 28', count: 15 }, { date: 'Dec 29', count: 14 }, { date: 'Dec 30', count: 18 }, { date: 'Dec 31', count: 23 }],
                applicationStatus: { applied: 90, contacted: 22, interviewing: 8, rejected: 6, offered: 2 }
            },
            shweta: {
                stats: { jobsToday: 15, totalApplications: 85, emailsSent: 62, emailsSuccess: 58, emailsBounced: 4, companiesFound: 28, hrContacts: 45, responseRate: 11, bounceRate: 6, successRate: 94 },
                emailStatus: { sent: 58, bounced: 4, opened: 18, replied: 7, failed: 0 },
                trends: { today: 8, yesterday: 9, change: -11, direction: 'down' },
                applicationsOverTime: [{ date: 'Dec 25', count: 5 }, { date: 'Dec 26', count: 8 }, { date: 'Dec 27', count: 6 }, { date: 'Dec 28', count: 10 }, { date: 'Dec 29', count: 9 }, { date: 'Dec 30', count: 12 }, { date: 'Dec 31', count: 15 }],
                applicationStatus: { applied: 60, contacted: 15, interviewing: 5, rejected: 4, offered: 1 }
            },
            yogeshwari: {
                stats: { jobsToday: 9, totalApplications: 43, emailsSent: 32, emailsSuccess: 30, emailsBounced: 2, companiesFound: 18, hrContacts: 22, responseRate: 9, bounceRate: 6, successRate: 94 },
                emailStatus: { sent: 30, bounced: 2, opened: 8, replied: 3, failed: 0 },
                trends: { today: 5, yesterday: 5, change: 0, direction: 'same' },
                applicationsOverTime: [{ date: 'Dec 25', count: 2 }, { date: 'Dec 26', count: 4 }, { date: 'Dec 27', count: 3 }, { date: 'Dec 28', count: 6 }, { date: 'Dec 29', count: 5 }, { date: 'Dec 30', count: 7 }, { date: 'Dec 31', count: 9 }],
                applicationStatus: { applied: 30, contacted: 8, interviewing: 2, rejected: 2, offered: 1 }
            }
        },
        recentJobs: [
            { title: 'Senior Data Scientist', company: 'TechCorp', location: 'Bangalore', source: 'LinkedIn', user: 'ajay' },
            { title: 'ML Engineer', company: 'AI Solutions', location: 'Hyderabad', source: 'Naukri', user: 'shweta' },
            { title: 'Data Analyst', company: 'FinTech Ltd', location: 'Mumbai', source: 'Indeed', user: 'yogeshwari' }
        ],
        recentEmails: [
            { recipient: 'hr@techcorp.com', company: 'TechCorp', date: 'Dec 31, 14:30', status: 'sent', opened: true, user: 'ajay' },
            { recipient: 'careers@aisolutions.com', company: 'AI Solutions', date: 'Dec 31, 14:25', status: 'sent', opened: false, user: 'shweta' },
            { recipient: 'careers@kotak.com', company: 'Kotak', date: 'Dec 31, 14:20', status: 'bounced', opened: false, user: 'yogeshwari' }
        ],
        companies: [
            { name: 'TechCorp', hrContact: 'Priya Sharma', email: 'priya@techcorp.com', status: 'Contacted', user: 'ajay' }
        ]
    };
}
