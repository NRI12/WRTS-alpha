/**
 * STUDENT MODULE JAVASCRIPT
 * File: static/js/student.js
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // =========================
    // ANIMATIONS
    // =========================
    
    /**
     * Animate statistics cards on load
     */
    function animateStatCards() {
        const statCards = document.querySelectorAll('.student-stat-card');
        statCards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                card.style.transition = 'all 0.5s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }
    
    /**
     * Animate cards on scroll
     */
    function animateCardsOnScroll() {
        const cards = document.querySelectorAll('.student-class-card, .student-routine-card, .student-assignment-card, .student-exam-card');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, {
            threshold: 0.1
        });
        
        cards.forEach(card => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'all 0.5s ease';
            observer.observe(card);
        });
    }
    
    // =========================
    // FILTERS
    // =========================
    
    /**
     * Auto-submit filter form on change
     */
    function initFilterAutoSubmit() {
        const filterSelects = document.querySelectorAll('.student-filter-select');
        filterSelects.forEach(select => {
            select.addEventListener('change', function() {
                this.closest('form').submit();
            });
        });
    }
    
    // =========================
    // TOOLTIPS & POPOVERS
    // =========================
    
    /**
     * Initialize Bootstrap tooltips
     */
    function initTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    /**
     * Initialize Bootstrap popovers
     */
    function initPopovers() {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }
    
    // =========================
    // COUNTDOWN TIMERS
    // =========================
    
    /**
     * Show countdown for deadlines
     */
    function initCountdownTimers() {
        const deadlineElements = document.querySelectorAll('[data-deadline]');
        
        deadlineElements.forEach(element => {
            const deadline = new Date(element.getAttribute('data-deadline'));
            
            function updateCountdown() {
                const now = new Date();
                const diff = deadline - now;
                
                if (diff <= 0) {
                    element.innerHTML = '<span class="student-deadline-warning">Đã hết hạn</span>';
                    return;
                }
                
                const days = Math.floor(diff / (1000 * 60 * 60 * 24));
                const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                
                if (days > 0) {
                    element.textContent = `Còn ${days} ngày ${hours} giờ`;
                } else if (hours > 0) {
                    element.textContent = `Còn ${hours} giờ ${minutes} phút`;
                } else {
                    element.textContent = `Còn ${minutes} phút`;
                }
                
                // Warning colors
                if (days === 0 && hours < 24) {
                    element.classList.add('student-deadline-warning');
                }
            }
            
            updateCountdown();
            setInterval(updateCountdown, 60000); // Update every minute
        });
    }
    
    // =========================
    // SEARCH & FILTER
    // =========================
    
    /**
     * Client-side search for cards
     */
    function initClientSearch() {
        const searchInput = document.getElementById('studentSearch');
        if (!searchInput) return;
        
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const cards = document.querySelectorAll('.student-class-card, .student-routine-card, .student-assignment-card');
            
            cards.forEach(card => {
                const text = card.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }
    
    // =========================
    // CONFIRMATION DIALOGS
    // =========================
    
    /**
     * Confirm before deleting or critical actions
     */
    function initConfirmDialogs() {
        const confirmButtons = document.querySelectorAll('[data-confirm]');
        
        confirmButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                const message = this.getAttribute('data-confirm') || 'Bạn có chắc chắn muốn thực hiện hành động này?';
                if (!confirm(message)) {
                    e.preventDefault();
                }
            });
        });
    }
    
    // =========================
    // SMOOTH SCROLL
    // =========================
    
    /**
     * Smooth scroll to anchor links
     */
    function initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                const href = this.getAttribute('href');
                if (href !== '#' && href !== '#!') {
                    e.preventDefault();
                    const target = document.querySelector(href);
                    if (target) {
                        target.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                }
            });
        });
    }
    
    // =========================
    // AUTO HIDE ALERTS
    // =========================
    
    /**
     * Auto hide success/error alerts after 5 seconds
     */
    function initAutoHideAlerts() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        
        alerts.forEach(alert => {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        });
    }
    
    // =========================
    // LOADING STATES
    // =========================
    
    /**
     * Show loading spinner on form submit
     */
    function initLoadingStates() {
        const forms = document.querySelectorAll('form[data-loading]');
        
        forms.forEach(form => {
            form.addEventListener('submit', function() {
                const submitBtn = this.querySelector('[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Đang xử lý...';
                }
            });
        });
    }
    
    // =========================
    // BACK TO TOP BUTTON
    // =========================
    
    /**
     * Show/hide back to top button
     */
    function initBackToTop() {
        const backToTopBtn = document.getElementById('backToTop');
        if (!backToTopBtn) return;
        
        window.addEventListener('scroll', function() {
            if (window.pageYOffset > 300) {
                backToTopBtn.style.display = 'block';
            } else {
                backToTopBtn.style.display = 'none';
            }
        });
        
        backToTopBtn.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
    
    // =========================
    // INITIALIZE ALL
    // =========================
    
    // Run animations
    animateStatCards();
    animateCardsOnScroll();
    
    // Initialize features
    initFilterAutoSubmit();
    initTooltips();
    initPopovers();
    initCountdownTimers();
    initClientSearch();
    initConfirmDialogs();
    initSmoothScroll();
    initAutoHideAlerts();
    initLoadingStates();
    initBackToTop();
    
    // Log initialization
    console.log('Student module initialized successfully');
});