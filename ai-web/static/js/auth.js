/**
 * AI-WRTS SYSTEM - AUTH MODULE JAVASCRIPT
 * Version: 2.0
 * Dùng chung cho tất cả auth pages
 */

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function() {
    initAuthModule();
});

function initAuthModule() {
    initPasswordToggle();
    initPasswordStrength();
    initFormValidation();
    initAvatarUpload();
    initRememberMe();
    initFormSubmit();
}

// ===== PASSWORD VISIBILITY TOGGLE =====
function initPasswordToggle() {
    const toggleButtons = document.querySelectorAll('.password-toggle-btn');
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const input = this.parentElement.querySelector('.form-control');
            const icon = this.querySelector('i');
            
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
                this.setAttribute('aria-label', 'Ẩn mật khẩu');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
                this.setAttribute('aria-label', 'Hiện mật khẩu');
            }
        });
    });
}

// ===== PASSWORD STRENGTH METER =====
function initPasswordStrength() {
    const passwordInputs = document.querySelectorAll('input[name="password"], input[name="new_password"]');
    
    passwordInputs.forEach(input => {
        // Create strength meter if it doesn't exist
        if (!input.parentElement.querySelector('.password-strength')) {
            const strengthMeter = createPasswordStrengthMeter();
            input.parentElement.appendChild(strengthMeter);
        }
        
        input.addEventListener('input', function() {
            updatePasswordStrength(this);
        });
    });
}

function createPasswordStrengthMeter() {
    const div = document.createElement('div');
    div.className = 'password-strength';
    div.innerHTML = `
        <div class="password-strength-label">Độ mạnh mật khẩu: <span class="strength-text">-</span></div>
        <div class="password-strength-bar">
            <div class="password-strength-fill"></div>
        </div>
    `;
    return div;
}

function updatePasswordStrength(input) {
    const password = input.value;
    const strength = calculatePasswordStrength(password);
    
    const strengthFill = input.parentElement.querySelector('.password-strength-fill');
    const strengthText = input.parentElement.querySelector('.strength-text');
    
    if (!strengthFill || !strengthText) return;
    
    // Remove all classes
    strengthFill.classList.remove('weak', 'medium', 'strong');
    
    if (password.length === 0) {
        strengthText.textContent = '-';
        strengthFill.style.width = '0';
    } else if (strength < 3) {
        strengthText.textContent = 'Yếu';
        strengthFill.classList.add('weak');
    } else if (strength < 4) {
        strengthText.textContent = 'Trung bình';
        strengthFill.classList.add('medium');
    } else {
        strengthText.textContent = 'Mạnh';
        strengthFill.classList.add('strong');
    }
}

function calculatePasswordStrength(password) {
    let strength = 0;
    
    // Length check
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    
    // Character variety checks
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;
    
    return Math.min(strength, 5);
}

// ===== FORM VALIDATION =====
function initFormValidation() {
    const forms = document.querySelectorAll('.auth-form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        });
        
        // Real-time validation
        const inputs = form.querySelectorAll('.form-control, .form-select');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid')) {
                    validateField(this);
                }
            });
        });
    });
}

function validateField(field) {
    const isValid = field.checkValidity();
    
    if (isValid) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
    } else {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
    }
    
    // Custom validations
    if (field.name === 'confirm_password') {
        validatePasswordMatch(field);
    }
    
    if (field.type === 'email') {
        validateEmail(field);
    }
    
    if (field.name === 'username') {
        validateUsername(field);
    }
}

function validatePasswordMatch(confirmField) {
    const passwordField = document.querySelector('input[name="password"], input[name="new_password"]');
    
    if (!passwordField) return;
    
    if (confirmField.value !== passwordField.value) {
        confirmField.setCustomValidity('Mật khẩu không khớp');
        confirmField.classList.add('is-invalid');
        
        // Update error message
        let feedback = confirmField.nextElementSibling;
        if (!feedback || !feedback.classList.contains('invalid-feedback')) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            confirmField.parentElement.appendChild(feedback);
        }
        feedback.textContent = 'Mật khẩu xác nhận không khớp';
    } else {
        confirmField.setCustomValidity('');
        confirmField.classList.remove('is-invalid');
        confirmField.classList.add('is-valid');
    }
}

function validateEmail(field) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (!emailRegex.test(field.value) && field.value.length > 0) {
        field.setCustomValidity('Email không hợp lệ');
    } else {
        field.setCustomValidity('');
    }
}

function validateUsername(field) {
    const username = field.value;
    
    // Username rules: 3-50 chars, alphanumeric and underscore only
    if (username.length < 3) {
        field.setCustomValidity('Username phải có ít nhất 3 ký tự');
    } else if (!/^[a-zA-Z0-9_]+$/.test(username)) {
        field.setCustomValidity('Username chỉ được chứa chữ, số và dấu gạch dưới');
    } else {
        field.setCustomValidity('');
    }
}

// ===== AVATAR UPLOAD =====
function initAvatarUpload() {
    const avatarInput = document.querySelector('.profile-avatar-upload input[type="file"]');
    
    if (avatarInput) {
        avatarInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            
            if (file) {
                // Validate file size (max 5MB)
                if (file.size > 5 * 1024 * 1024) {
                    showToast('File ảnh không được vượt quá 5MB', 'error');
                    this.value = '';
                    return;
                }
                
                // Validate file type
                if (!file.type.startsWith('image/')) {
                    showToast('Vui lòng chọn file ảnh', 'error');
                    this.value = '';
                    return;
                }
                
                // Preview image
                const reader = new FileReader();
                reader.onload = function(e) {
                    const avatarImg = document.querySelector('.profile-avatar img');
                    if (avatarImg) {
                        avatarImg.src = e.target.result;
                    } else {
                        const avatar = document.querySelector('.profile-avatar');
                        avatar.innerHTML = `<img src="${e.target.result}" alt="Avatar">`;
                    }
                    
                    showToast('Ảnh đã được chọn. Nhấn Lưu để cập nhật.', 'info');
                };
                reader.readAsDataURL(file);
            }
        });
    }
}

// ===== REMEMBER ME =====
function initRememberMe() {
    const rememberCheckbox = document.querySelector('input[name="remember"]');
    
    if (rememberCheckbox) {
        // Load saved username if exists
        const savedUsername = localStorage.getItem('rememberedUsername');
        if (savedUsername) {
            const usernameInput = document.querySelector('input[name="username"]');
            if (usernameInput) {
                usernameInput.value = savedUsername;
                rememberCheckbox.checked = true;
            }
        }
        
        // Handle form submission
        const loginForm = rememberCheckbox.closest('form');
        if (loginForm) {
            loginForm.addEventListener('submit', function() {
                const usernameInput = this.querySelector('input[name="username"]');
                
                if (rememberCheckbox.checked) {
                    localStorage.setItem('rememberedUsername', usernameInput.value);
                } else {
                    localStorage.removeItem('rememberedUsername');
                }
            });
        }
    }
}

// ===== FORM SUBMIT WITH LOADING =====
function initFormSubmit() {
    const authForms = document.querySelectorAll('.auth-form');
    
    authForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                return;
            }
            
            const submitBtn = form.querySelector('.auth-submit-btn');
            if (submitBtn && !submitBtn.classList.contains('loading')) {
                submitBtn.classList.add('loading');
                submitBtn.disabled = true;
                
                // Re-enable after 5 seconds as fallback
                setTimeout(() => {
                    submitBtn.classList.remove('loading');
                    submitBtn.disabled = false;
                }, 5000);
            }
        });
    });
}

// ===== UTILITY FUNCTIONS =====

// Check if email exists (AJAX)
async function checkEmailExists(email) {
    try {
        const response = await fetch('/api/check-email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email: email })
        });
        
        const data = await response.json();
        return data.exists;
    } catch (error) {
        console.error('Error checking email:', error);
        return false;
    }
}

// Check if username exists (AJAX)
async function checkUsernameExists(username) {
    try {
        const response = await fetch('/api/check-username', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username: username })
        });
        
        const data = await response.json();
        return data.exists;
    } catch (error) {
        console.error('Error checking username:', error);
        return false;
    }
}

// Auto-fill username from email
function initEmailToUsername() {
    const emailInput = document.querySelector('input[name="email"]');
    const usernameInput = document.querySelector('input[name="username"]');
    
    if (emailInput && usernameInput) {
        emailInput.addEventListener('blur', function() {
            if (!usernameInput.value && this.value) {
                // Extract username from email (part before @)
                const suggestedUsername = this.value.split('@')[0].toLowerCase();
                usernameInput.value = suggestedUsername;
                validateField(usernameInput);
            }
        });
    }
}

// Show/hide password requirements
function togglePasswordRequirements() {
    const passwordInput = document.querySelector('input[name="password"]');
    
    if (passwordInput) {
        const requirements = document.createElement('div');
        requirements.className = 'password-requirements';
        requirements.innerHTML = `
            <small class="text-muted">
                <i class="fas fa-info-circle"></i> Mật khẩu phải có:
                <ul>
                    <li>Ít nhất 8 ký tự</li>
                    <li>Chữ hoa và chữ thường</li>
                    <li>Ít nhất 1 số</li>
                    <li>Ít nhất 1 ký tự đặc biệt</li>
                </ul>
            </small>
        `;
        
        passwordInput.parentElement.appendChild(requirements);
        
        passwordInput.addEventListener('focus', function() {
            requirements.style.display = 'block';
        });
        
        passwordInput.addEventListener('blur', function() {
            setTimeout(() => {
                requirements.style.display = 'none';
            }, 200);
        });
    }
}

// Initialize optional features
if (document.querySelector('.auth-form')) {
    initEmailToUsername();
}

// Export functions for external use
window.authModule = {
    validateField,
    checkEmailExists,
    checkUsernameExists,
    calculatePasswordStrength
};