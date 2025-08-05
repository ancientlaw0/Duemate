document.getElementById('email-form').addEventListener('submit', async e => {
  e.preventDefault();
  const email = document.getElementById('email').value.trim();
  const messageElem = document.getElementById('email-message');
  messageElem.textContent = '';

  try {
    const response = await fetch('http://localhost:5000/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
      //credentials: 'include'
    });

    const data = await response.json();
    if (response.ok) {
      // ✅ Store email + type
      localStorage.setItem('identifier', email);
      localStorage.setItem('type', 'email');

      window.location.href = "verify.html";
    } else {
      messageElem.textContent = data.message || "Error";
    }
  } catch (err) {
    messageElem.textContent = 'Server error';
  }
});


document.getElementById('mobile-form').addEventListener('submit', async e => {
  e.preventDefault();
  const phone_number = document.getElementById('phone').value.trim();
  const messageElem = document.getElementById('mobile-message');
  messageElem.textContent = '';

  try {
    const response = await fetch('http://localhost:5000/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone_number }),
      //credentials: 'include'
    });

    const data = await response.json();
    if (response.ok) {
      // ✅ Store phone number + type
      localStorage.setItem('identifier', phone_number);
      localStorage.setItem('type', 'phone');

      window.location.href = "verify.html";
    } else {
      messageElem.textContent = data.message || "Error";
    }
  } catch (err) {
    messageElem.textContent = 'Server error';
  }
});
