// Dashboard Configuration
const CONFIG = {
    dataPath: 'data/dashboard_data.json',
    refreshInterval: 300000, // 5 minutes
    scheduleTimesIST: ['09:30', '14:30', '19:30'],
    users: ['ajay', 'shweta', 'yogeshwari']
};

// Global state
let dashboardData = null;
let currentUser = 'all';

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
    setupUserTabs();
    updateNextRun();
    setInterval(updateNextRun, 60000);
});

// Setup User Tab Click Handlers
function setupUserTabs() {
    const tabs = document.querySelectorAll('.user-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Update active state
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Update current user and refresh display
            currentUser = tab.dataset.user;
            if (dashboardData) {
                updateDashboard(dashboardData);
            }
        });
    });
}

// Load Dashboard Data
async function loadDashboardData() {
    try {
        const response = await fetch(CONFIG.dataPath);
        if (!response.ok) {
            throw new Error('Data not found');
        }
        dashboardData = await response.json();
        updateDashboard(dashboardData);
    } catch (error) {
        console.log('Loading sample data...', error);
        dashboardData = getSampleData();
        updateDashboard(dashboardData);
    }
}

// Calculate aggregated stats for all users
function getAggregatedStats(data) {
    if (!data.users) return data.stats || {};
    
    const stats = {
        jobsToday: 0,
        totalApplications: 0,
        emailsSent: 0,
        companiesFound: 0,
        hrContacts: 0,
        responseRate: 0
    };
    
    let totalEmails = 0;
    let totalReplies = 0;
    
    Object.values(data.users).forEach(userData => {
        if (userData.stats) {
            stats.jobsToday += userData.stats.jobsToday || 0;
            stats.totalApplications += userData.stats.totalApplications || 0;
            stats.emailsSent += userData.stats.emailsSent || 0;
            stats.companiesFound += userData.stats.companiesFound || 0;
            stats.hrContacts += userData.stats.hrContacts || 0;
            totalEmails += userData.stats.emailsSent || 0;
            totalReplies += (userData.stats.emailsSent || 0) * (userData.stats.responseRate || 0) / 100;
        }
    });
    
    stats.responseRate = totalEmails > 0 ? Math.round(totalReplies / totalEmails * 100) : 0;
    
    return stats;
}

// Update Dashboard with Data
function updateDashboard(data) {
    // Update last updated timestamp
    document.getElementById('last-updated').textContent = 
        `Last updated: ${data.lastUpdated || new Date().toLocaleString()}`;
    
    // Update user tab counts
    updateUserTabCounts(data);
    
    // Get stats based on current filter
    let stats;
    if (currentUser === 'all') {
        stats = data.users ? getAggregatedStats(data) : data.stats;
    } else {
        stats = data.users?.[currentUser]?.stats || data.stats;
    }
    
    // Update stats
    animateNumber('jobs-count', stats?.jobsToday || 0);
    animateNumber('applications-count', stats?.totalApplications || 0);
    animateNumber('emails-count', stats?.emailsSent || 0);
    animateNumber('companies-count', stats?.companiesFound || 0);
    animateNumber('hr-count', stats?.hrContacts || 0);
    
    const responseRate = stats?.responseRate || 0;
    document.getElementById('response-rate').textContent = `${responseRate}%`;
    
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
    
    // Update charts
    updateApplicationsChart(timeSeriesData);
    updateStatusChart(statusData);
    
    // Filter activities by user
    const filteredJobs = filterByUser(data.recentJobs || [], currentUser);
    const filteredEmails = filterByUser(data.recentEmails || [], currentUser);
    const filteredCompanies = filterByUser(data.companies || [], currentUser);
    
    // Update recent activities
    updateRecentJobs(filteredJobs);
    updateRecentEmails(filteredEmails);
    
    // Update companies table
    updateCompaniesTable(filteredCompanies);
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
            if (!dateMap[item.date]) {
                dateMap[item.date] = 0;
            }
            dateMap[item.date] += item.count;
        });
    });
    
    return Object.entries(dateMap)
        .map(([date, count]) => ({ date, count }))
        .sort((a, b) => a.date.localeCompare(b.date));
}

// Merge status data from all users
function mergeStatusData(users) {
    const merged = {
        applied: 0,
        contacted: 0,
        interviewing: 0,
        rejected: 0,
        offered: 0
    };
    
    Object.values(users).forEach(userData => {
        const status = userData.applicationStatus || {};
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
let applicationsChart = null;
function updateApplicationsChart(data) {
    const ctx = document.getElementById('applicationsChart').getContext('2d');
    
    if (applicationsChart) {
        applicationsChart.destroy();
    }
    
    const labels = data.map(d => d.date);
    const values = data.map(d => d.count);
    
    applicationsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Applications',
                data: values,
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
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                }
            }
        }
    });
}

// Update Application Status Chart
let statusChart = null;
function updateStatusChart(data) {
    const ctx = document.getElementById('statusChart').getContext('2d');
    
    if (statusChart) {
        statusChart.destroy();
    }
    
    statusChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Applied', 'Contacted', 'Interviewing', 'Rejected', 'Offered'],
            datasets: [{
                data: [
                    data.applied || 0,
                    data.contacted || 0,
                    data.interviewing || 0,
                    data.rejected || 0,
                    data.offered || 0
                ],
                backgroundColor: [
                    '#3b82f6',
                    '#f59e0b',
                    '#10b981',
                    '#ef4444',
                    '#8b5cf6'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#f8fafc',
                        padding: 20
                    }
                }
            },
            cutout: '60%'
        }
    });
}

// Update Recent Jobs List
function updateRecentJobs(jobs) {
    const container = document.getElementById('recent-jobs');
    
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
    
    if (emails.length === 0) {
        container.innerHTML = '<div class="loading">No emails sent yet</div>';
        return;
    }
    
    container.innerHTML = emails.slice(0, 10).map(email => `
        <div class="activity-item">
            <div class="activity-item-content">
                <div class="activity-item-title">${escapeHtml(email.recipient)}</div>
                <div class="activity-item-meta">
                    ${email.user ? `<span class="user-badge ${email.user}">${email.user}</span> • ` : ''}
                    ${escapeHtml(email.company)} • ${escapeHtml(email.date)}
                </div>
            </div>
            <span class="activity-item-badge ${email.opened ? 'badge-success' : 'badge-pending'}">
                ${email.opened ? 'Opened' : 'Sent'}
            </span>
        </div>
    `).join('');
}

// Update Companies Table
function updateCompaniesTable(companies) {
    const tbody = document.getElementById('companies-tbody');
    
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
            <td>
                <span class="status-pill status-${(company.status || 'applied').toLowerCase()}">
                    ${escapeHtml(company.status || 'Discovered')}
                </span>
            </td>
        </tr>
    `).join('');
}

// Calculate Next Run Time
function updateNextRun() {
    const now = new Date();
    const istOffset = 5.5 * 60 * 60 * 1000;
    const nowIST = new Date(now.getTime() + istOffset);
    
    const currentTime = nowIST.getHours() * 60 + nowIST.getMinutes();
    const scheduleTimes = CONFIG.scheduleTimesIST.map(t => {
        const [h, m] = t.split(':').map(Number);
        return h * 60 + m;
    });
    
    let nextRunMinutes = null;
    for (const time of scheduleTimes) {
        if (time > currentTime) {
            nextRunMinutes = time;
            break;
        }
    }
    
    if (nextRunMinutes === null) {
        nextRunMinutes = scheduleTimes[0];
        const hours = Math.floor(nextRunMinutes / 60);
        const mins = nextRunMinutes % 60;
        document.getElementById('next-run').textContent = 
            `Tomorrow at ${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')} IST`;
    } else {
        const hours = Math.floor(nextRunMinutes / 60);
        const mins = nextRunMinutes % 60;
        const diffMinutes = nextRunMinutes - currentTime;
        
        if (diffMinutes < 60) {
            document.getElementById('next-run').textContent = 
                `In ${diffMinutes} minutes (${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')} IST)`;
        } else {
            const diffHours = Math.floor(diffMinutes / 60);
            const remainingMins = diffMinutes % 60;
            document.getElementById('next-run').textContent = 
                `In ${diffHours}h ${remainingMins}m (${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')} IST)`;
        }
    }
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
        users: {
            ajay: {
                stats: {
                    jobsToday: 23,
                    totalApplications: 128,
                    emailsSent: 95,
                    companiesFound: 42,
                    hrContacts: 67,
                    responseRate: 14
                },
                applicationsOverTime: [
                    { date: 'Dec 25', count: 8 },
                    { date: 'Dec 26', count: 12 },
                    { date: 'Dec 27', count: 9 },
                    { date: 'Dec 28', count: 15 },
                    { date: 'Dec 29', count: 14 },
                    { date: 'Dec 30', count: 18 },
                    { date: 'Dec 31', count: 23 }
                ],
                applicationStatus: {
                    applied: 90,
                    contacted: 22,
                    interviewing: 8,
                    rejected: 6,
                    offered: 2
                }
            },
            shweta: {
                stats: {
                    jobsToday: 15,
                    totalApplications: 85,
                    emailsSent: 62,
                    companiesFound: 28,
                    hrContacts: 45,
                    responseRate: 11
                },
                applicationsOverTime: [
                    { date: 'Dec 25', count: 5 },
                    { date: 'Dec 26', count: 8 },
                    { date: 'Dec 27', count: 6 },
                    { date: 'Dec 28', count: 10 },
                    { date: 'Dec 29', count: 9 },
                    { date: 'Dec 30', count: 12 },
                    { date: 'Dec 31', count: 15 }
                ],
                applicationStatus: {
                    applied: 60,
                    contacted: 15,
                    interviewing: 5,
                    rejected: 4,
                    offered: 1
                }
            },
            yogeshwari: {
                stats: {
                    jobsToday: 9,
                    totalApplications: 43,
                    emailsSent: 32,
                    companiesFound: 18,
                    hrContacts: 22,
                    responseRate: 9
                },
                applicationsOverTime: [
                    { date: 'Dec 25', count: 2 },
                    { date: 'Dec 26', count: 4 },
                    { date: 'Dec 27', count: 3 },
                    { date: 'Dec 28', count: 6 },
                    { date: 'Dec 29', count: 5 },
                    { date: 'Dec 30', count: 7 },
                    { date: 'Dec 31', count: 9 }
                ],
                applicationStatus: {
                    applied: 30,
                    contacted: 8,
                    interviewing: 2,
                    rejected: 2,
                    offered: 1
                }
            }
        },
        recentJobs: [
            { title: 'Senior Data Scientist', company: 'TechCorp', location: 'Bangalore', source: 'LinkedIn', user: 'ajay' },
            { title: 'ML Engineer', company: 'AI Solutions', location: 'Hyderabad', source: 'Naukri', user: 'shweta' },
            { title: 'Data Analyst', company: 'FinTech Ltd', location: 'Mumbai', source: 'Indeed', user: 'yogeshwari' },
            { title: 'Python Developer', company: 'StartupXYZ', location: 'Remote', source: 'LinkedIn', user: 'ajay' },
            { title: 'AI Research Engineer', company: 'DeepMind India', location: 'Bangalore', source: 'Company', user: 'shweta' },
            { title: 'Backend Developer', company: 'CloudTech', location: 'Pune', source: 'LinkedIn', user: 'ajay' },
            { title: 'Full Stack Developer', company: 'WebApps Inc', location: 'Chennai', source: 'Naukri', user: 'yogeshwari' }
        ],
        recentEmails: [
            { recipient: 'hr@techcorp.com', company: 'TechCorp', date: 'Dec 31, 2025', opened: true, user: 'ajay' },
            { recipient: 'recruiter@aisolutions.com', company: 'AI Solutions', date: 'Dec 31, 2025', opened: false, user: 'shweta' },
            { recipient: 'talent@fintech.com', company: 'FinTech Ltd', date: 'Dec 30, 2025', opened: true, user: 'yogeshwari' },
            { recipient: 'hiring@startup.io', company: 'StartupXYZ', date: 'Dec 30, 2025', opened: false, user: 'ajay' },
            { recipient: 'jobs@cloudtech.com', company: 'CloudTech', date: 'Dec 30, 2025', opened: true, user: 'shweta' }
        ],
        companies: [
            { name: 'TechCorp', hrContact: 'Priya Sharma', email: 'priya.sharma@techcorp.com', status: 'Contacted', user: 'ajay' },
            { name: 'AI Solutions', hrContact: 'Rahul Verma', email: 'rahul@aisolutions.com', status: 'Applied', user: 'shweta' },
            { name: 'FinTech Ltd', hrContact: 'Anjali Patel', email: 'anjali.patel@fintech.com', status: 'Responded', user: 'yogeshwari' },
            { name: 'StartupXYZ', hrContact: '-', email: 'careers@startup.io', status: 'Applied', user: 'ajay' },
            { name: 'DataDriven Inc', hrContact: 'Vikram Singh', email: 'vikram@datadriven.com', status: 'Contacted', user: 'shweta' },
            { name: 'CloudTech', hrContact: 'Sneha Reddy', email: 'sneha@cloudtech.com', status: 'Interviewing', user: 'ajay' }
        ]
    };
}
