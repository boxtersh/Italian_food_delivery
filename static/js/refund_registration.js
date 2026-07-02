document.addEventListener('DOMContentLoaded', () => {
    const returnBtn = document.querySelector('.js-return-to-register');
        if (returnBtn) {
            returnBtn.addEventListener('click', (e) => {
            e.preventDefault();


        const modal = document.getElementById('authModal');
        if (modal) {
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
            }

        const registerTabBtn = document.querySelector('[data-auth-tab="register"]');
        const loginTabBtn = document.querySelector('[data-auth-tab="login"]');
        const loginForm = document.getElementById('loginForm');
        const registerForm = document.getElementById('registerForm');

        if (registerTabBtn && loginTabBtn && registerForm && loginForm) {
            loginTabBtn.classList.remove('active');
            registerTabBtn.classList.add('active');

            loginForm.classList.add('hidden');
            registerForm.classList.remove('hidden');

            const title = document.getElementById('authModalTitle');
        if (title) title.textContent = 'Регистрация';
      }
    });
  }
});