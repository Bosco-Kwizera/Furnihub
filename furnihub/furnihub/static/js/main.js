// Main JavaScript file for FurniHub

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        document.querySelectorAll('.alert').forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

// Quantity input validation
document.querySelectorAll('input[type="number"][name="quantity"]').forEach(function(input) {
    input.addEventListener('change', function() {
        var min = parseInt(this.min) || 1;
        var max = parseInt(this.max) || 999;
        var value = parseInt(this.value) || min;
        
        if (value < min) this.value = min;
        if (value > max) this.value = max;
    });
});

// Add to cart with AJAX
function addToCart(productId, quantity) {
    fetch(`/cart/add/${productId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `quantity=${quantity}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartCount(data.cart_count);
            showNotification('Product added to cart!', 'success');
        } else {
            showNotification(data.error || 'Error adding to cart', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error adding to cart', 'error');
    });
}

// Update cart count in navbar
function updateCartCount(count) {
    var cartBadge = document.querySelector('.navbar .fa-shopping-cart + .badge');
    if (cartBadge) {
        cartBadge.textContent = count;
        if (count === 0) {
            cartBadge.style.display = 'none';
        } else {
            cartBadge.style.display = 'inline';
        }
    }
}

// Show notification
function showNotification(message, type) {
    var notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    notification.style.zIndex = '9999';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(notification);
    
    setTimeout(function() {
        notification.remove();
    }, 3000);
}

// Get CSRF token from cookies
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Price range slider
var priceSlider = document.getElementById('priceRange');
if (priceSlider) {
    priceSlider.addEventListener('input', function() {
        document.getElementById('priceValue').textContent = '$' + this.value;
    });
}

// Image gallery zoom
document.querySelectorAll('.product-gallery .main-image img').forEach(function(img) {
    img.addEventListener('mousemove', function(e) {
        var bounds = this.getBoundingClientRect();
        var x = (e.clientX - bounds.left) / bounds.width * 100;
        var y = (e.clientY - bounds.top) / bounds.height * 100;
        this.style.transformOrigin = x + '% ' + y + '%';
        this.style.transform = 'scale(1.5)';
    });
    
    img.addEventListener('mouseleave', function() {
        this.style.transform = 'scale(1)';
    });
});

// Wishlist toggle
document.querySelectorAll('.wishlist-toggle').forEach(function(btn) {
    btn.addEventListener('click', function(e) {
        e.preventDefault();
        var productId = this.dataset.productId;
        
        fetch('/accounts/wishlist/toggle/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({product_id: productId})
        })
        .then(response => response.json())
        .then(data => {
            if (data.in_wishlist) {
                this.classList.add('active');
                showNotification('Added to wishlist', 'success');
            } else {
                this.classList.remove('active');
                showNotification('Removed from wishlist', 'info');
            }
        });
    });
});

// Loading spinner
function showLoading() {
    var spinner = document.querySelector('.spinner-overlay');
    if (spinner) {
        spinner.classList.add('show');
    }
}

function hideLoading() {
    var spinner = document.querySelector('.spinner-overlay');
    if (spinner) {
        spinner.classList.remove('show');
    }
}

// Show loading on form submit
document.querySelectorAll('form').forEach(function(form) {
    form.addEventListener('submit', function() {
        if (!this.classList.contains('no-loading')) {
            showLoading();
        }
    });
});

// Initialize all product cards
document.querySelectorAll('.product-card').forEach(function(card) {
    card.addEventListener('click', function(e) {
        // Don't redirect if clicking on form elements or buttons
        if (e.target.tagName === 'BUTTON' || e.target.tagName === 'A' || e.target.tagName === 'INPUT') {
            e.stopPropagation();
        }
    });
});

// Password strength meter
var passwordInput = document.getElementById('id_password');
if (passwordInput) {
    passwordInput.addEventListener('input', function() {
        var strength = checkPasswordStrength(this.value);
        updateStrengthMeter(strength);
    });
}

function checkPasswordStrength(password) {
    var strength = 0;
    if (password.length >= 8) strength++;
    if (password.match(/[a-z]+/)) strength++;
    if (password.match(/[A-Z]+/)) strength++;
    if (password.match(/[0-9]+/)) strength++;
    if (password.match(/[$@#&!]+/)) strength++;
    return strength;
}

function updateStrengthMeter(strength) {
    var meter = document.getElementById('password-strength');
    if (!meter) {
        meter = document.createElement('div');
        meter.id = 'password-strength';
        passwordInput.parentNode.appendChild(meter);
    }
    
    var colors = ['#dc3545', '#ffc107', '#ffc107', '#17a2b8', '#28a745'];
    var texts = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];
    
    meter.style.height = '5px';
    meter.style.width = (strength * 20) + '%';
    meter.style.backgroundColor = colors[strength - 1] || '#dc3545';
    meter.style.transition = 'all 0.3s';
    
    if (strength > 0) {
        meter.textContent = texts[strength - 1];
        meter.style.lineHeight = '20px';
        meter.style.fontSize = '12px';
        meter.style.color = '#fff';
        meter.style.textAlign = 'center';
    }
}