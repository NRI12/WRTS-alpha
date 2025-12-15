/**
 * AI-WRTS SYSTEM - MAIN JAVASCRIPT
 * Version: 2.0
 * Bootstrap 5.3 + AdminLTE Compatible
 */

// ===== GLOBAL VARIABLES =====
let toastTimeout;
const TOAST_DURATION = 5000;

// ===== DOCUMENT READY =====
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// ===== INITIALIZATION =====
function initializeApp() {
    initSidebar();
    initTooltips();
    initPopovers();
    initAlerts();
    initForms();
    initDataTables();
    initCharts();
    initScrollAnimations();
    initThemeToggle();
}

// ===== SIDEBAR =====
function initSidebar() {
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    const content = document.querySelector('.content-with-sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('sidebar-hidden');
            if (content) {
                content.classList.toggle('content-full');
            }
            
            // Save state to localStorage
            const isHidden = sidebar.classList.contains('sidebar-hidden');
            localStorage.setItem('sidebarHidden', isHidden);
        });
        
        // Restore sidebar state from localStorage
        const sidebarHidden = localStorage.getItem('sidebarHidden') === 'true';
        if (sidebarHidden) {
            sidebar.classList.add('sidebar-hidden');
            if (content) {
                content.classList.add('content-full');
            }
        }
    }
    
    // Mobile sidebar handling
    if (window.innerWidth < 992) {
        if (sidebar) {
            sidebar.classList.add('sidebar-hidden');
        }
    }
}

// ===== TOOLTIPS & POPOVERS =====
function initTooltips() {
    const tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function initPopovers() {
    const popoverTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="popover"]')
    );
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// ===== ALERTS =====
function initAlerts() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, TOAST_DURATION);
    });
}

// ===== TOAST NOTIFICATIONS =====
function showToast(message, type = 'info') {
    // Remove existing toast if any
    const existingToast = document.querySelector('.custom-toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `custom-toast toast-${type}`;
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas ${icons[type] || icons.info}"></i>
            <span>${message}</span>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    document.body.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Auto-remove after duration
    clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, TOAST_DURATION);
}

// ===== FORMS =====
function initForms() {
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Password visibility toggle
    const passwordToggles = document.querySelectorAll('.password-toggle');
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const input = this.previousElementSibling;
            const icon = this.querySelector('i');
            
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    });
    
    // File input preview
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const preview = this.nextElementSibling;
            if (preview && preview.classList.contains('file-preview')) {
                const file = this.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        preview.innerHTML = `
                            <img src="${e.target.result}" alt="Preview" style="max-width: 200px; max-height: 200px;">
                        `;
                    };
                    reader.readAsDataURL(file);
                }
            }
        });
    });
}

// ===== DATA TABLES =====
function initDataTables() {
    if (typeof $.fn.DataTable !== 'undefined') {
        $('.data-table').each(function() {
            if (!$.fn.DataTable.isDataTable(this)) {
                $(this).DataTable({
                    language: {
                        url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/vi.json'
                    },
                    pageLength: 10,
                    responsive: true,
                    order: [[0, 'desc']],
                    dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>rtip'
                });
            }
        });
    }
}

// ===== CHARTS =====
function initCharts() {
    if (typeof Chart !== 'undefined') {
        // Set default chart options
        Chart.defaults.font.family = 'Inter, sans-serif';
        Chart.defaults.color = '#6b7280';
        
        // Initialize charts based on canvas elements
        const chartElements = document.querySelectorAll('[data-chart]');
        chartElements.forEach(canvas => {
            const chartType = canvas.dataset.chartType || 'line';
            const chartData = JSON.parse(canvas.dataset.chartData || '{}');
            
            new Chart(canvas, {
                type: chartType,
                data: chartData,
                options: getChartOptions(chartType)
            });
        });
    }
}

function getChartOptions(type) {
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    padding: 15,
                    usePointStyle: true
                }
            }
        }
    };
    
    if (type === 'line' || type === 'bar') {
        commonOptions.scales = {
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                }
            },
            x: {
                grid: {
                    display: false
                }
            }
        };
    }
    
    return commonOptions;
}

// ===== SCROLL ANIMATIONS =====
function initScrollAnimations() {
    const animateOnScroll = document.querySelectorAll('.animate-on-scroll');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
            }
        });
    }, {
        threshold: 0.1
    });
    
    animateOnScroll.forEach(el => observer.observe(el));
}

// ===== THEME TOGGLE =====
function initThemeToggle() {
    const themeToggle = document.querySelector('.theme-toggle');
    
    if (themeToggle) {
        // Load saved theme
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            // Update icon
            const icon = this.querySelector('i');
            if (icon) {
                icon.classList.toggle('fa-moon');
                icon.classList.toggle('fa-sun');
            }
        });
    }
}

// ===== UTILITY FUNCTIONS =====

// Confirm dialog
function confirmAction(message, callback) {
    if (confirm(message)) {
        if (typeof callback === 'function') {
            callback();
        }
        return true;
    }
    return false;
}

// Loading overlay
function showLoading() {
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.innerHTML = `
        <div class="loading-spinner">
            <i class="fas fa-spinner fa-spin fa-3x"></i>
            <p>Đang xử lý...</p>
        </div>
    `;
    document.body.appendChild(overlay);
}

function hideLoading() {
    const overlay = document.querySelector('.loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// Format number
function formatNumber(num) {
    return new Intl.NumberFormat('vi-VN').format(num);
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: 'VND'
    }).format(amount);
}

// Format date
function formatDate(date) {
    return new Intl.DateTimeFormat('vi-VN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    }).format(new Date(date));
}

// Debounce function
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

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Đã sao chép vào clipboard!', 'success');
    }).catch(() => {
        showToast('Không thể sao chép!', 'error');
    });
}

// ===== AJAX HELPERS =====
async function fetchData(url, options = {}) {
    try {
        showLoading();
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        hideLoading();
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        hideLoading();
        showToast('Có lỗi xảy ra: ' + error.message, 'error');
        throw error;
    }
}

// ===== EXPORT GLOBAL FUNCTIONS =====
window.showToast = showToast;
window.confirmAction = confirmAction;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.formatNumber = formatNumber;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;
window.copyToClipboard = copyToClipboard;
window.fetchData = fetchData;