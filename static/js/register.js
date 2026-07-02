document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('form');
    const emailInput = document.getElementById('email');
    const phoneInput = document.getElementById('phone');
    const passwordInput = document.getElementById('password');

    function setValid(input) {
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
    }

    function setInvalid(input) {
        input.classList.remove('is-valid');
        input.classList.add('is-invalid');
    }

    function validateEmail() {
        const value = emailInput.value.trim();
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!emailRegex.test(value)) {
            setInvalid(emailInput);
            return false;
        }

        setValid(emailInput);
        return true;
    }

    function validatePhone() {
        const value = phoneInput.value.trim();

        if (value.startsWith('+7')) {
            const digits = value.replace(/\D/g, '');

            if (digits.length === 11 && digits.startsWith('7')) {
                setValid(phoneInput);
                return true;
            }

            setInvalid(phoneInput);
            return false;
        }

        if (value.startsWith('8')) {
            const digits = value.replace(/\D/g, '');

            if (digits.length === 11 && digits.startsWith('8')) {
                setValid(phoneInput);
                return true;
            }

            setInvalid(phoneInput);
            return false;
        }

        setInvalid(phoneInput);
        return false;
    }

    function validatePassword() {
        const value = passwordInput.value;

        if (value.length < 8) {
            setInvalid(passwordInput);
            return false;
        }

        setValid(passwordInput);
        return true;
    }

    emailInput.addEventListener('input', validateEmail);
    phoneInput.addEventListener('input', validatePhone);
    passwordInput.addEventListener('input', validatePassword);

    form.addEventListener('submit', function (event) {
        const isEmailValid = validateEmail();
        const isPhoneValid = validatePhone();
        const isPasswordValid = validatePassword();

        if (!isEmailValid || !isPhoneValid || !isPasswordValid) {
            event.preventDefault();
        }
    });
});