let authToken = null;


// UTILITY: Show/hide loading and error
function setLoading(visible) {
    document.getElementById('loading').style.display = visible ? 'block' : 'none';
}
function setError(msg) {
    const error = document.getElementById('error');
    error.textContent = msg ? msg : '';
    error.style.display = msg ? 'block' : 'none';
}

// MAIN: Fetch and display payments
async function loadPayments(page = 1) {
    setLoading(true);
    setError('');

    const params = new URLSearchParams();
    params.append('page', page);
    params.append('per_page', 10);

    const search = document.getElementById('search').value.trim();
    const status = document.getElementById('filterStatus').value;
    const category = document.getElementById('filterCategory').value;
    const sortBy = document.getElementById('sortBy').value;
    const sortOrder = document.getElementById('sortOrder').value;

    if (search) params.append('search', search);
    if (status) params.append('status', status);
    if (category) params.append('category', category);
    if (sortBy) params.append('sort_by', sortBy);
    if (sortOrder) params.append('sort_order', sortOrder);

    if (!authToken) {
        setLoading(false);
        setError('Auth token missing');
        return;
    }

    try {
        const response = await fetch(`http://localhost:5000/api/payments?${params}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        if (response.ok && data.status === 'success') {
            displayPayments(data.data.payments);
            renderPagination(data.data.pagination);
        } else {
            setError(data.message || 'Failed to load payments');
        }
    } catch (err) {
        setError(err.message || 'Server error');
    } finally {
        setLoading(false);
    }
}

// RENDER: Display payments table
function displayPayments(payments) {
    const tbody = document.getElementById('paymentsTableBody');
    if (!tbody) return;

    if (!payments || payments.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="no-data">No payments found.</td></tr>';
        return;
    }

    tbody.innerHTML = payments.map(payment => `
        <tr data-id="${payment.id}">
            <td>${payment.payment_name}</td>
            <td>${payment.description || '-'}</td>
            <td>${Number(payment.amount).toFixed(2)}</td>
            <td>${payment.category}</td>
            <td>${new Date(payment.deadline).toLocaleDateString()}</td>
            <td>
                <span class="status ${payment.status}">${payment.status}</span>
            </td>
            <td>
                <select class="change-status-dropdown">
                    <option value="pending" ${payment.status === 'pending' ? 'selected' : ''}>Pending</option>
                    <option value="paid" ${payment.status === 'paid' ? 'selected' : ''}>Paid</option>
                    <option value="overdue" ${payment.status === 'overdue' ? 'selected' : ''}>Overdue</option>
                    <option value="cancelled" ${payment.status === 'cancelled' ? 'selected' : ''}>Cancelled</option>
                </select>
                <button type="button" class="update-status-btn">Update</button>
                <button type="button" class="delete-btn">Delete</button>
            </td>
        </tr>
    `).join('');

    // Add/update event listeners after DOM update
    document.querySelectorAll('.update-status-btn').forEach(btn => {
        btn.addEventListener('click', async e => {
            const row = e.target.closest('tr');
            const id = row.dataset.id;
            const newStatus = row.querySelector('.change-status-dropdown').value;
            await updateStatus(id, newStatus);
        });
    });
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', async e => {
            const row = e.target.closest('tr');
            const id = row.dataset.id;
            await deletePayment(id);
        });
    });
}

// ADD PAYMENT
document.getElementById('addPaymentForm').addEventListener('submit', async e => {
    e.preventDefault();

    if (!authToken) {
        alert('Auth token missing!');
        return;
    }

    const payload = {
        payment_name: document.getElementById('payment_name').value.trim(),
        description: document.getElementById('description').value.trim(),
        amount: parseFloat(document.getElementById('amount').value),
        category: document.getElementById('addCategory').value,
        deadline: document.getElementById('deadline').value,
        status: document.getElementById('addStatus').value
    };

    try {
        const res = await fetch('http://localhost:5000/api/payments', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok && data.status === 'success') {
            alert('Payment added successfully!');
            e.target.reset();
            loadPayments(1); // Refresh first page
        } else {
            alert(data.message || 'Failed to add payment');
        }
    } catch (err) {
        alert(err.message || 'Server error while adding payment');
    }
});

// UPDATE STATUS
async function updateStatus(id, status) {
    if (!authToken) return alert('Auth token missing!');
    try {
        const res = await fetch(`http://localhost:5000/api/payment/${id}/status`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status })
        });
        const data = await res.json();
        if (res.ok && data.status === 'success') {
            alert('Status updated!');
            loadPayments(); // Reload current page
        } else {
            alert(data.message || 'Failed to update status');
        }
    } catch (err) {
        alert(err.message || 'Error updating status');
    }
}

// DELETE PAYMENT
async function deletePayment(id) {
    if (!authToken) return alert('Auth token missing!');
    if (!confirm('Are you sure you want to delete this payment?')) return;

    try {
        const res = await fetch(`http://localhost:5000/api/payments/${id}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        const data = await res.json();
        if (res.ok && data.status === 'success') {
            alert('Payment deleted successfully');
            loadPayments(); // Refresh list
        } else {
            alert(data.message || 'Failed to delete payment');
        }
    } catch (err) {
        alert(err.message || 'Error deleting payment');
    }
}

// FILTERS & SORT
document.getElementById('search').addEventListener('input', () => loadPayments(1));
document.getElementById('filterStatus').addEventListener('change', () => loadPayments(1));
document.getElementById('filterCategory').addEventListener('change', () => loadPayments(1));
document.getElementById('sortBy').addEventListener('change', () => loadPayments(1));
document.getElementById('sortOrder').addEventListener('change', () => loadPayments(1));

window.clearFilters = function() {
    document.getElementById('search').value = '';
    document.getElementById('filterStatus').value = '';
    document.getElementById('filterCategory').value = '';
    document.getElementById('sortBy').value = 'deadline';
    document.getElementById('sortOrder').value = 'asc';
    loadPayments(1);
};

// PAGINATION
function renderPagination(pagination) {
    const container = document.getElementById("pagination");
    if (!container || !pagination) return;

    container.innerHTML = '';

    if (pagination.has_prev) {
        const prevBtn = document.createElement("button");
        prevBtn.textContent = "Previous";
        prevBtn.onclick = () => loadPayments(pagination.prev_page);
        container.appendChild(prevBtn);
    }

    const current = document.createElement("span");
    current.textContent = `Page ${pagination.page} of ${pagination.total_pages}`;
    container.appendChild(current);

    if (pagination.has_next) {
        const nextBtn = document.createElement("button");
        nextBtn.textContent = "Next";
        nextBtn.onclick = () => loadPayments(pagination.next_page);
        container.appendChild(nextBtn);
    }
}

// INIT: Load token and first page
window.addEventListener('load', () => {
    authToken = localStorage.getItem('access_token');
    if (!authToken) {
        alert('Please login first to view payments');
        // Optionally redirect to login page...
        setError('Please log in.');
        setLoading(false);
    } else {
        loadPayments(1);
    }
});
