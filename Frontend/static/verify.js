document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('otp-form');
  const otpInput = document.getElementById('otp');
  const messageElem = document.getElementById('otp-message');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const otp = otpInput.value.trim();
    messageElem.textContent = '';

    if (!otp) {
      messageElem.textContent = 'Please enter the OTP.';
      return;
    }

    const identifier = localStorage.getItem('identifier');
    const type = localStorage.getItem('type');

    if (!identifier || !type) {
      messageElem.textContent = 'Missing login info. Go back and try again.';
      return;
    }

    const payload = { otp };
    if (type === 'email') {
      payload.email = identifier;
    } else if (type === 'phone') {
      payload.phone_number = identifier;
    }

    try {
      const response = await fetch('http://localhost:5000/api/auth/verify_otp', { 
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
        // ❌ DO NOT use credentials here — you're not using session cookies
      });

      const data = await response.json();

      if (data.status === 'success') {
        // Clear login identifier from storage
        localStorage.removeItem('identifier');
        localStorage.removeItem('type');

        // Store auth info
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user_id', data.user_id);

        window.location.href = 'dashboard.html';
      } else {
        messageElem.textContent = data.message || 'Verification failed.';
      }
    } catch (error) {
      messageElem.textContent = 'Server error. Please try again later.';
      console.error('Error verifying OTP:', error);
    }
  });
});
