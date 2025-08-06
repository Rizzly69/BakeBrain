// Smart Bakery Management - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize mobile menu
    initializeMobileMenu();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize real-time updates
    initializeRealTimeUpdates();
    
    // Initialize form validations
    initializeFormValidations();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize AI insights
    initializeAIInsights();
}

// Mobile menu functionality
function initializeMobileMenu() {
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const sidebar = document.querySelector('.sidebar');
    
    if (mobileMenuBtn && sidebar) {
        mobileMenuBtn.addEventListener('click', function() {
            sidebar.classList.toggle('open');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!sidebar.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        });
    }
}

// Tooltip functionality
function initializeTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(e) {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = e.target.getAttribute('data-tooltip');
    
    const rect = e.target.getBoundingClientRect();
    tooltip.style.position = 'fixed';
    tooltip.style.top = rect.top - 35 + 'px';
    tooltip.style.left = rect.left + rect.width / 2 + 'px';
    tooltip.style.transform = 'translateX(-50%)';
    tooltip.style.background = 'var(--bg-card)';
    tooltip.style.color = 'var(--text-primary)';
    tooltip.style.padding = '5px 10px';
    tooltip.style.borderRadius = '4px';
    tooltip.style.fontSize = '12px';
    tooltip.style.zIndex = '1000';
    tooltip.style.border = '1px solid var(--neon-cyan)';
    tooltip.style.boxShadow = 'var(--glow-cyan)';
    
    document.body.appendChild(tooltip);
    e.target.tooltipElement = tooltip;
}

function hideTooltip(e) {
    if (e.target.tooltipElement) {
        document.body.removeChild(e.target.tooltipElement);
        e.target.tooltipElement = null;
    }
}

// Real-time updates
function initializeRealTimeUpdates() {
    // Update timestamps
    updateTimestamps();
    setInterval(updateTimestamps, 60000); // Update every minute
    
    // Check for new notifications
    if (window.location.pathname === '/dashboard') {
        checkNotifications();
        setInterval(checkNotifications, 30000); // Check every 30 seconds
    }
}

function updateTimestamps() {
    const timestamps = document.querySelectorAll('.timestamp');
    
    timestamps.forEach(element => {
        const datetime = element.getAttribute('data-datetime');
        if (datetime) {
            element.textContent = formatRelativeTime(new Date(datetime));
        }
    });
}

function formatRelativeTime(date) {
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    
    return date.toLocaleDateString();
}

function checkNotifications() {
    // This would typically make an API call to check for new notifications
    // For now, we'll simulate with localStorage
    const lastCheck = localStorage.getItem('lastNotificationCheck');
    const now = new Date().getTime();
    
    if (!lastCheck || now - parseInt(lastCheck) > 300000) { // 5 minutes
        // Simulate notification check
        localStorage.setItem('lastNotificationCheck', now.toString());
    }
}

// Form validations
function initializeFormValidations() {
    const forms = document.querySelectorAll('form[data-validate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(form)) {
                e.preventDefault();
            }
        });
        
        // Real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(input);
            });
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    
    inputs.forEach(input => {
        if (!validateField(input)) {
            isValid = false;
        }
    });
    
    return isValid;
}

function validateField(field) {
    const value = field.value.trim();
    const isRequired = field.hasAttribute('required');
    let isValid = true;
    
    // Remove existing error messages
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
    
    // Check required fields
    if (isRequired && !value) {
        showFieldError(field, 'This field is required');
        isValid = false;
    }
    
    // Email validation
    if (field.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            showFieldError(field, 'Please enter a valid email address');
            isValid = false;
        }
    }
    
    // Number validation
    if (field.type === 'number' && value) {
        const min = field.getAttribute('min');
        const max = field.getAttribute('max');
        
        if (min && parseFloat(value) < parseFloat(min)) {
            showFieldError(field, `Value must be at least ${min}`);
            isValid = false;
        }
        
        if (max && parseFloat(value) > parseFloat(max)) {
            showFieldError(field, `Value must be no more than ${max}`);
            isValid = false;
        }
    }
    
    // Update field styling
    if (isValid) {
        field.classList.remove('error');
        field.classList.add('valid');
    } else {
        field.classList.add('error');
        field.classList.remove('valid');
    }
    
    return isValid;
}

function showFieldError(field, message) {
    const error = document.createElement('div');
    error.className = 'field-error';
    error.textContent = message;
    error.style.color = 'var(--error)';
    error.style.fontSize = '12px';
    error.style.marginTop = '5px';
    
    field.parentNode.appendChild(error);
}

// Search functionality
function initializeSearch() {
    const searchInputs = document.querySelectorAll('.search-input');
    
    searchInputs.forEach(input => {
        let timeout;
        
        input.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                performSearch(input);
            }, 300);
        });
    });
}

function performSearch(input) {
    const query = input.value.trim();
    const form = input.closest('form');
    
    if (form) {
        // Update URL with search parameter
        const url = new URL(window.location);
        if (query) {
            url.searchParams.set('search', query);
        } else {
            url.searchParams.delete('search');
        }
        
        // Navigate to new URL
        window.location.href = url.toString();
    }
}

// AI Insights functionality
function initializeAIInsights() {
    const refreshBtn = document.querySelector('.refresh-insights-btn');
    
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            refreshAIInsights();
        });
    }
    
    // Auto-refresh insights every 5 minutes on dashboard
    if (window.location.pathname === '/dashboard') {
        setInterval(refreshAIInsights, 300000);
    }
}

function refreshAIInsights() {
    const btn = document.querySelector('.refresh-insights-btn');
    const insightsContainer = document.querySelector('.ai-insights-container');
    
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="loading"></span> Refreshing...';
    }
    
    fetch('/api/insights/refresh', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('AI insights refreshed successfully', 'success');
            // Reload the page to show updated insights
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showNotification('Failed to refresh insights', 'error');
        }
    })
    .catch(error => {
        console.error('Error refreshing insights:', error);
        showNotification('Failed to refresh insights', 'error');
    })
    .finally(() => {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = 'Refresh Insights';
        }
    });
}

// Order status updates
function updateOrderStatus(orderId, newStatus) {
    const statusBadge = document.querySelector(`[data-order-id="${orderId}"] .status-badge`);
    
    if (statusBadge) {
        statusBadge.textContent = 'Updating...';
        statusBadge.className = 'badge';
    }
    
    fetch(`/api/order/${orderId}/status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (statusBadge) {
                statusBadge.textContent = newStatus.replace('_', ' ').toUpperCase();
                statusBadge.className = `badge badge-${getStatusClass(newStatus)}`;
            }
            showNotification('Order status updated successfully', 'success');
        } else {
            showNotification(data.message || 'Failed to update order status', 'error');
        }
    })
    .catch(error => {
        console.error('Error updating order status:', error);
        showNotification('Failed to update order status', 'error');
    });
}

function getStatusClass(status) {
    const statusClasses = {
        'PENDING': 'warning',
        'CONFIRMED': 'info',
        'IN_PREPARATION': 'info',
        'READY': 'success',
        'DELIVERED': 'success',
        'CANCELLED': 'danger'
    };
    
    return statusClasses[status] || 'info';
}

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button class="notification-close">&times;</button>
    `;
    
    // Styling
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.background = `var(--${type})`;
    notification.style.color = 'white';
    notification.style.padding = '15px 20px';
    notification.style.borderRadius = '8px';
    notification.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.3)';
    notification.style.zIndex = '10000';
    notification.style.minWidth = '300px';
    notification.style.animation = 'slideInRight 0.3s ease';
    
    // Close button functionality
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    });
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }
    }, 5000);
}

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatDate(date) {
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(new Date(date));
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(100%);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideOutRight {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
    
    .form-control.error {
        border-color: var(--error);
        box-shadow: 0 0 10px rgba(255, 68, 68, 0.3);
    }
    
    .form-control.valid {
        border-color: var(--success);
        box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
    }
`;
document.head.appendChild(style);
