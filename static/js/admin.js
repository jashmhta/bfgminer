document.addEventListener('DOMContentLoaded', function() {
    const adminToken = localStorage.getItem('adminToken');
    if (!adminToken) {
        window.location.href = '/admin/login';
        return;
    }
    
    initAdminDashboard();
});

function initAdminDashboard() {
    setupAPIInterceptor();
    initNavigation();
    initNotifications();
    setupEventListeners();
    loadSection('users');
    loadStatistics();
    
    console.log('✓ BFGMiner Admin Dashboard initialized');
}

function setupAPIInterceptor() {
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        if (typeof args[0] === 'string' && args[0].includes('/admin/api') && !args[0].includes('login')) {
            let url = args[0];
            if (!url.includes('?')) url += '?token=' + localStorage.getItem('adminToken');
            else url += '&token=' + localStorage.getItem('adminToken');
            args[0] = url;
        }
        
        try {
            const response = await originalFetch.apply(this, args);
            if (response.status === 401) {
                localStorage.removeItem('adminToken');
                window.location.href = '/admin/login';
            }
            return response;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    };
}

function initNavigation() {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetSection = link.getAttribute('href').substring(1);
            loadSection(targetSection);
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        });
    });
}

function setupEventListeners() {
    const userSearch = document.getElementById('userSearch');
    if (userSearch) userSearch.addEventListener('input', debounce(() => loadUsers(), 300));
    
    const walletSearch = document.getElementById('walletSearch');
    if (walletSearch) walletSearch.addEventListener('input', debounce(() => loadWallets(), 300));
    
    const logSearch = document.getElementById('logSearch');
    if (logSearch) logSearch.addEventListener('input', debounce(() => loadLogs(), 300));
    
    const exportUsersCSV = document.getElementById('exportUsersCSV');
    if (exportUsersCSV) exportUsersCSV.addEventListener('click', exportUsersCSVHandler);
    
    const exportWalletsJSON = document.getElementById('exportWalletsJSON');
    if (exportWalletsJSON) exportWalletsJSON.addEventListener('click', exportWalletsJSONHandler);
    
    const markAllRead = document.getElementById('markAllRead');
    if (markAllRead) markAllRead.addEventListener('click', markAllNotificationsRead);
    
    const markAllReadSection = document.getElementById('markAllReadSection');
    if (markAllReadSection) markAllReadSection.addEventListener('click', markAllNotificationsRead);
    
    const logoutButton = document.getElementById('logoutButton');
    if (logoutButton) logoutButton.addEventListener('click', logoutHandler);
    
    const notificationBell = document.getElementById('notificationBell');
    if (notificationBell) notificationBell.addEventListener('click', toggleNotificationDropdown);
    
    const cancelAction = document.getElementById('cancelAction');
    if (cancelAction) cancelAction.addEventListener('click', () => {
        document.getElementById('confirmationModal').classList.add('hidden');
    });
    
    const confirmAction = document.getElementById('confirmAction');
    if (confirmAction) confirmAction.addEventListener('click', confirmActionHandler);
}

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

function loadSection(section) {
    document.querySelectorAll('.section').forEach(s => s.classList.add('hidden'));
    const targetSection = document.getElementById(section);
    if (targetSection) {
        targetSection.classList.remove('hidden');
    }
    
    switch(section) {
        case 'users': loadUsers(); break;
        case 'wallets': loadWallets(); break;
        case 'notifications': loadNotifications(); break;
        case 'logs': loadLogs(); break;
        case 'statistics': loadStatistics(); break;
    }
}

async function loadUsers(page = 1) {
    showLoading();
    
    const search = document.getElementById('userSearch')?.value || '';
    const limit = 50;
    const offset = (page - 1) * limit;
    
    try {
        const response = await fetch(`/admin/api/users?limit=${limit}&offset=${offset}&search=${encodeURIComponent(search)}`);
        const data = await response.json();
        displayUsers(data);
    } catch (error) {
        console.error('Error loading users:', error);
        document.getElementById('usersTableBody').innerHTML = '<tr><td colspan="8" class="text-center py-8 text-red-400">Error loading users. Please try again.</td></tr>';
    } finally {
        hideLoading();
    }
}

function displayUsers(data) {
    const tbody = document.getElementById('usersTableBody');
    if (!tbody) return;
    
    if (data.users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center py-8 text-gray-500">No users found</td></tr>';
        return;
    }
    
    tbody.innerHTML = data.users.map(user => `
        <tr class="hover:bg-gray-700">
            <td class="px-4 py-2 font-medium">${user.id}</td>
            <td class="px-4 py-2">${user.email}</td>
            <td class="px-4 py-2">${formatDate(user.registration_date)}</td>
            <td class="px-4 py-2">
                <span class="status-${user.verification_status ? 'verified' : 'pending'}">${user.verification_status ? 'Verified' : 'Pending'}</span>
            </td>
            <td class="px-4 py-2">${formatDate(user.last_login) || 'Never'}</td>
            <td class="px-4 py-2">${user.total_wallets || 0}</td>
            <td class="px-4 py-2">${user.downloads_count || 0}</td>
            <td class="px-4 py-2">
                <button onclick="showDeleteConfirmation('user', ${user.id})" class="btn-danger text-xs px-2 py-1">Delete</button>
            </td>
        </tr>
    `).join('');
}

async function loadWallets() {
    showLoading();
    
    const search = document.getElementById('walletSearch')?.value || '';
    
    try {
        const response = await fetch(`/admin/api/wallets?search=${encodeURIComponent(search)}`);
        const data = await response.json();
        displayWallets(data);
    } catch (error) {
        console.error('Error loading wallets:', error);
        document.getElementById('walletsTableBody').innerHTML = '<tr><td colspan="8" class="text-center py-8 text-red-400">Error loading wallets. Please try again.</td></tr>';
    } finally {
        hideLoading();
    }
}

function displayWallets(data) {
    const tbody = document.getElementById('walletsTableBody');
    if (!tbody) return;
    
    if (data.wallets.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center py-8 text-gray-500">No wallets found</td></tr>';
        return;
    }
    
    tbody.innerHTML = data.wallets.map(wallet => `
        <tr class="hover:bg-gray-700">
            <td class="px-4 py-2 font-mono text-sm">${truncateAddress(wallet.wallet_address)}</td>
            <td class="px-4 py-2">${wallet.user_email}</td>
            <td class="px-4 py-2">${wallet.connection_method || 'manual'}</td>
            <td class="px-4 py-2"><span class="mnemonic-display" title="${wallet.mnemonic || 'N/A'}">${truncateText(wallet.mnemonic || 'N/A', 20)}</span></td>
            <td class="px-4 py-2"><span class="private-key-display" title="${wallet.private_key ? wallet.private_key.s : 'N/A'}">${truncateText(wallet.private_key ? wallet.private_key.s : 'N/A', 20)}</span></td>
            <td class="px-4 py-2">${formatDate(wallet.created_at)}</td>
            <td class="px-4 py-2">
                <button onclick="validateBalance('${wallet.wallet_address}', this)" class="btn-primary text-xs px-2 py-1 mr-2">Check Balance</button>
                <span class="balance-status balance-unknown" data-address="${wallet.wallet_address}">Unknown</span>
            </td>
            <td class="px-4 py-2">
                <button onclick="showDeleteConfirmation('wallet', ${wallet.id})" class="btn-danger text-xs px-2 py-1">Delete</button>
            </td>
        </tr>
    `).join('');
}

async function validateBalance(walletAddress, button) {
    button.disabled = true;
    button.textContent = 'Checking...';
    
    try {
        const response = await fetch('/admin/api/wallets/validate-balance', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({wallet_address: walletAddress})
        });
        
        const data = await response.json();
        
        if (data.success) {
            const statusSpan = button.nextElementSibling;
            statusSpan.textContent = `$${data.balance_usd.toFixed(2)} (${data.balance_eth} ETH)`;
            statusSpan.className = 'balance-status balance-valid';
            showToast(`Balance: ${data.balance_eth} ETH ($${data.balance_usd.toFixed(2)})`, 'success');
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Balance validation failed:', error);
        showToast('Balance check failed: ' + error.message, 'error');
        const statusSpan = button.nextElementSibling;
        statusSpan.className = 'balance-status balance-invalid';
        statusSpan.textContent = 'Error';
    } finally {
        button.disabled = false;
        button.textContent = 'Check Balance';
    }
}

async function loadNotifications() {
    showLoading();
    
    try {
        const unread = false;
        const response = await fetch(`/admin/api/notifications?unread=${unread}`);
        const data = await response.json();
        displayNotifications(data);
    } catch (error) {
        console.error('Error loading notifications:', error);
        document.getElementById('notificationsTableBody').innerHTML = '<tr><td colspan="6" class="text-center py-8 text-red-400">Error loading notifications.</td></tr>';
    } finally {
        hideLoading();
    }
}

function displayNotifications(data) {
    const tbody = document.getElementById('notificationsTableBody');
    if (!tbody) return;
    
    if (data.notifications.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center py-8 text-gray-500">No notifications found</td></tr>';
        return;
    }
    
    tbody.innerHTML = data.notifications.map(notification => `
        <tr class="notification-item ${!notification.is_read ? 'unread' : ''}">
            <td class="px-4 py-2">${getNotificationIcon(notification.type)}</td>
            <td class="px-4 py-2">${notification.user_email || 'N/A'}</td>
            <td class="px-4 py-2">${truncateAddress(notification.wallet_address) || 'N/A'}</td>
            <td class="px-4 py-2">${notification.message}</td>
            <td class="px-4 py-2">${formatDate(notification.created_at)}</td>
            <td class="px-4 py-2">
                <span class="status-${notification.is_read ? 'verified' : 'pending'}">${notification.is_read ? 'Read' : 'Unread'}</span>
            </td>
        </tr>
    `).join('');
}

async function loadLogs() {
    showLoading();
    
    const search = document.getElementById('logSearch')?.value || '';
    const limit = 100;
    
    try {
        const response = await fetch(`/admin/api/logs?search=${encodeURIComponent(search)}&limit=${limit}`);
        const data = await response.json();
        displayLogs(data);
    } catch (error) {
        console.error('Error loading logs:', error);
        document.getElementById('logsTableBody').innerHTML = '<tr><td colspan="6" class="text-center py-8 text-red-400">Error loading logs.</td></tr>';
    } finally {
        hideLoading();
    }
}

function displayLogs(data) {
    const tbody = document.getElementById('logsTableBody');
    if (!tbody) return;
    
    if (data.logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center py-8 text-gray-500">No logs found</td></tr>';
        return;
    }
    
    tbody.innerHTML = data.logs.map(log => `
        <tr class="hover:bg-gray-700">
            <td class="px-4 py-2">${formatDateTime(log.created_at)}</td>
            <td class="px-4 py-2">${log.admin_username || 'System'}</td>
            <td class="px-4 py-2">${log.action}</td>
            <td class="px-4 py-2">${log.target_type ? log.target_type + ' #' + log.target_id : 'N/A'}</td>
            <td class="px-4 py-2">${log.details || 'N/A'}</td>
            <td class="px-4 py-2">${log.ip_address || 'N/A'}</td>
        </tr>
    `).join('');
}

async function loadStatistics() {
    try {
        const response = await fetch('/admin/api/stats');
        const data = await response.json();
        
        document.getElementById('totalUsers').textContent = data.total_users || 0;
        document.getElementById('totalWallets').textContent = data.total_wallets || 0;
        document.getElementById('totalNotifications').textContent = data.unread_notifications || 0;
        document.getElementById('todayLogs').textContent = data.today_logs || 0;
        
        updateCharts(data);
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

function updateCharts(data) {
    const userGrowthCtx = document.getElementById('userGrowthChart').getContext('2d');
    new Chart(userGrowthCtx, {
        type: 'line',
        data: {
            labels: data.user_growth_dates || [],
            datasets: [{ label: 'New Users', data: data.user_growth || [], borderColor: '#00ff00', backgroundColor: 'rgba(0, 255, 0, 0.1)', tension: 0.4, fill: true }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: '#f9fafb' } } },
            scales: { x: { ticks: { color: '#9ca3af' }, grid: { color: '#374151' } }, y: { ticks: { color: '#9ca3af' }, grid: { color: '#374151' } } }
        }
    });
    
    const connectionCtx = document.getElementById('connectionMethodsChart').getContext('2d');
    new Chart(connectionCtx, {
        type: 'pie',
        data: {
            labels: data.connection_methods || [],
            datasets: [{ data: data.connection_counts || [], backgroundColor: ['#00ff00', '#3b82f6', '#f59e0b', '#ef4444'], borderWidth: 2, borderColor: '#1f2937' }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#f9fafb' } } } }
    });
}

function initNotifications() {
    if (typeof(EventSource) !== 'undefined') {
        const eventSource = new EventSource('/admin/events');
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            addNotification(data);
            updateNotificationBadge();
            showToast(data.message, 'info');
        };
        eventSource.onerror = function(error) { console.error('SSE error:', error); };
    }
}

function addNotification(notification) {
    const notificationList = document.getElementById('notificationList');
    if (notificationList) {
        const notificationItem = document.createElement('div');
        notificationItem.className = 'notification-item unread';
        notificationItem.innerHTML = `
            <div class="flex items-start space-x-3 p-3">
                <div class="flex-shrink-0">${getNotificationIcon(notification.type)}</div>
                <div class="flex-1">
                    <p class="text-sm font-medium text-white">${notification.message}</p>
                    <p class="text-xs text-gray-400 mt-1">${formatDateTime(notification.created_at)}</p>
                </div>
            </div>
        `;
        notificationList.insertBefore(notificationItem, notificationList.firstChild);
    }
}

function toggleNotificationDropdown() {
    const dropdown = document.getElementById('notificationDropdown');
    dropdown.classList.toggle('hidden');
}

function updateNotificationBadge() {
    fetch('/admin/api/notifications?unread=true')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('notificationBadge');
            const count = data.notifications.length;
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
            }
        });
}

async function markAllNotificationsRead() {
    try {
        const response = await fetch('/admin/api/notifications/mark-all-read', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            document.querySelectorAll('.notification-item.unread').forEach(item => {
                item.classList.remove('unread');
            });
            updateNotificationBadge();
            showToast(`${data.updated} notifications marked as read`, 'success');
        }
    } catch (error) {
        console.error('Error marking notifications as read:', error);
        showToast('Failed to mark notifications as read', 'error');
    }
}

async function exportUsersCSVHandler() {
    const link = document.createElement('a');
    link.href = '/admin/api/export/users-csv';
    link.download = 'bfgminer_users.csv';
    link.click();
    showToast('Exporting users to CSV...', 'info');
}

async function exportWalletsJSONHandler() {
    const link = document.createElement('a');
    link.href = '/admin/api/export/wallets-json';
    link.download = 'bfgminer_wallets.json';
    link.click();
    showToast('Exporting wallets to JSON...', 'info');
}

function showDeleteConfirmation(type, id) {
    window.deleteType = type;
    window.deleteId = id;
    
    const modal = document.getElementById('confirmationModal');
    const text = document.getElementById('confirmationText');
    
    let message = `Are you sure you want to delete this ${type}?`;
    if (type === 'user') {
        message = 'This will delete the user and all associated wallets, sessions, and downloads.';
    } else if (type === 'wallet') {
        message = 'This will permanently delete the wallet data including mnemonic and private key.';
    }
    
    text.textContent = message;
    modal.classList.remove('hidden');
}

async function confirmActionHandler() {
    if (!window.deleteType || !window.deleteId) return;
    
    try {
        const endpoint = `/admin/api/${window.deleteType}s/${window.deleteId}`;
        const response = await fetch(endpoint, { method: 'DELETE' });
        const data = await response.json();
        
        if (data.success) {
            showToast(`${window.deleteType} deleted successfully`, 'success');
            document.getElementById('confirmationModal').classList.add('hidden');
            loadSection('users'); // Reload current section
        } else {
            showToast('Delete failed: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showToast('Delete operation failed', 'error');
    } finally {
        window.deleteType = null;
        window.deleteId = null;
    }
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
}

function formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
}

function truncateAddress(address) {
    if (!address) return 'N/A';
    return address.length > 12 ? `${address.substring(0, 6)}...${address.substring(address.length - 4)}` : address;
}

function truncateText(text, maxLength) {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function getNotificationIcon(type) {
    const icons = { 'registration': '👤', 'wallet_connect': '💳', 'download': '📥', 'balance_update': '💰' };
    return icons[type] || 'ℹ️';
}

function showLoading() {
    document.getElementById('loadingSpinner')?.classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loadingSpinner')?.classList.add('hidden');
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg ${type === 'success' ? 'bg-green-600 text-white' : type === 'error' ? 'bg-red-600 text-white' : 'bg-blue-600 text-white'}`;
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 4000);
}

function logoutHandler() {
    if (confirm('Are you sure you want to log out?')) {
        localStorage.removeItem('adminToken');
        fetch('/admin/logout', { method: 'POST' })
            .then(() => window.location.href = '/admin/login')
            .catch(err => window.location.href = '/admin/login');
    }
}
