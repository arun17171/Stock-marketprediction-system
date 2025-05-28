/* static/js/main.js */

document.addEventListener('DOMContentLoaded', function() {
    // Enable tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Enable popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Stock Symbol Auto-Capitalize
    const stockSymbolInput = document.getElementById('id_stock_symbol');
    if (stockSymbolInput) {
        stockSymbolInput.addEventListener('blur', function() {
            this.value = this.value.toUpperCase();
        });
    }
    
    // Form validation
    const predictionForm = document.querySelector('form[action="/predict/"]');
    if (predictionForm) {
        predictionForm.addEventListener('submit', function(event) {
            const stockSymbol = document.getElementById('id_stock_symbol').value.trim();
            if (!stockSymbol) {
                event.preventDefault();
                alert('Please enter a stock symbol');
                return false;
            }
            
            // Show loading spinner
            const submitButton = this.querySelector('button[type="submit"]');
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
            submitButton.disabled = true;
        });
    }
});

// Function to format currency
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(value);
}

// Function to format large numbers with commas
function formatNumber(value) {
    return new Intl.NumberFormat('en-US').format(value);
}

// Function to format dates
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-US', options);
}