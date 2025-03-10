// Main JavaScript for Bank App

document.addEventListener('DOMContentLoaded', function() {
    // Enable tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Format currency inputs
    const currencyInputs = document.querySelectorAll('input[type="number"][step="0.01"]');
    currencyInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value) {
                this.value = parseFloat(this.value).toFixed(2);
            }
        });
    });

    // Account number validation
    const accountToInput = document.getElementById('account_to');
    if (accountToInput) {
        accountToInput.addEventListener('input', function() {
            this.value = this.value.toUpperCase();
            
            // Basic format validation (3-letter prefix followed by alphanumeric)
            const regex = /^[A-Z]{3}[A-Z0-9]+$/;
            if (this.value && !regex.test(this.value)) {
                this.classList.add('is-invalid');
                
                // Check if error message exists, if not create one
                let errorDiv = this.nextElementSibling.nextElementSibling;
                if (!errorDiv || !errorDiv.classList.contains('text-danger')) {
                    errorDiv = document.createElement('div');
                    errorDiv.classList.add('text-danger');
                    errorDiv.textContent = 'Account number must start with 3-letter bank prefix';
                    this.parentNode.insertBefore(errorDiv, this.nextElementSibling.nextElementSibling);
                }
            } else {
                this.classList.remove('is-invalid');
                
                // Remove error message if exists
                const errorDiv = this.nextElementSibling.nextElementSibling;
                if (errorDiv && errorDiv.classList.contains('text-danger')) {
                    errorDiv.remove();
                }
            }
        });
    }

    // Transaction table sorting
    const transactionTables = document.querySelectorAll('table');
    transactionTables.forEach(table => {
        const headers = table.querySelectorAll('th');
        headers.forEach((header, index) => {
            if (header.classList.contains('sortable')) {
                header.addEventListener('click', function() {
                    sortTable(table, index);
                });
                header.style.cursor = 'pointer';
                header.innerHTML += ' <span class="sort-icon">⇅</span>';
            }
        });
    });
});

// Function to sort tables
function sortTable(table, column) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const headers = table.querySelectorAll('th');
    
    // Determine sort direction
    const currentDirection = headers[column].getAttribute('data-sort') || 'asc';
    const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
    
    // Reset all headers
    headers.forEach(header => {
        header.setAttribute('data-sort', '');
        const icon = header.querySelector('.sort-icon');
        if (icon) icon.textContent = '⇅';
    });
    
    // Set new direction on current header
    headers[column].setAttribute('data-sort', newDirection);
    const icon = headers[column].querySelector('.sort-icon');
    if (icon) icon.textContent = newDirection === 'asc' ? '↑' : '↓';
    
    // Sort the rows
    rows.sort((a, b) => {
        const cellA = a.querySelectorAll('td')[column].textContent.trim();
        const cellB = b.querySelectorAll('td')[column].textContent.trim();
        
        // Check if content is a date
        if (isDate(cellA) && isDate(cellB)) {
            const dateA = new Date(cellA);
            const dateB = new Date(cellB);
            return newDirection === 'asc' ? dateA - dateB : dateB - dateA;
        }
        
        // Check if content is a number
        if (!isNaN(cellA) && !isNaN(cellB)) {
            return newDirection === 'asc' ? parseFloat(cellA) - parseFloat(cellB) : parseFloat(cellB) - parseFloat(cellA);
        }
        
        // Default string comparison
        return newDirection === 'asc' ? 
            cellA.localeCompare(cellB) : 
            cellB.localeCompare(cellA);
    });
    
    // Reappend rows in new order
    rows.forEach(row => tbody.appendChild(row));
}

// Helper function to check if a string is a date
function isDate(dateStr) {
    const regex = /^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}(:\d{2})?)?$/;
    return regex.test(dateStr) && !isNaN(new Date(dateStr).getTime());
}
