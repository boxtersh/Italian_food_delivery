document.addEventListener("DOMContentLoaded", () => {
    const authModal = document.getElementById("authModal");
    const openAuthModalBtn = document.getElementById("openAuthModalBtn");
    const closeButtons = document.querySelectorAll("[data-close-auth-modal]");

    const loginTabBtn = document.querySelector('[data-auth-tab="login"]');
    const registerTabBtn = document.querySelector('[data-auth-tab="register"]');

    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");
    const authMessage = document.getElementById("authMessage");

    function showMessage(text, type = "error") {
        if (!authMessage) return;
        authMessage.textContent = text;
        authMessage.classList.remove("hidden", "error", "success");
        authMessage.classList.add(type);
    }

    function clearMessage() {
        if (!authMessage) return;
        authMessage.textContent = "";
        authMessage.classList.add("hidden");
        authMessage.classList.remove("error", "success");
    }

    function openModal() {
        if (!authModal) return;
        authModal.classList.remove("hidden");
        document.body.style.overflow = "hidden";
        clearMessage();
    }

    function closeModal() {
        if (!authModal) return;
        authModal.classList.add("hidden");
        document.body.style.overflow = "";
        clearMessage();
    }

    function switchTab(tab) {
        clearMessage();

        if (tab === "login") {
            loginTabBtn?.classList.add("active");
            registerTabBtn?.classList.remove("active");
            loginForm?.classList.remove("hidden");
            registerForm?.classList.add("hidden");
        } else {
            registerTabBtn?.classList.add("active");
            loginTabBtn?.classList.remove("active");
            registerForm?.classList.remove("hidden");
            loginForm?.classList.add("hidden");
        }
    }

    function normalizeServerError(detail, fallbackText) {
        if (!detail) return fallbackText;

        if (typeof detail === "string") {
            return detail;
        }

        if (Array.isArray(detail)) {
            return detail
                .map((item) => {
                    if (typeof item === "string") return item;
                    if (item && typeof item === "object") {
                        return item.msg || item.message || item.detail || "Некорректные данные";
                    }
                    return "Некорректные данные";
                })
                .join("\n");
        }

        if (typeof detail === "object") {
            return detail.msg || detail.message || detail.detail || fallbackText;
        }

        return fallbackText;
    }

    function isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    function isValidPhone(phone) {
        const normalized = phone.replace(/\D/g, "");
        const startsCorrectly = phone.trim().startsWith("+7") || phone.trim().startsWith("8");
        return startsCorrectly && normalized.length === 11;
    }

    function isValidPassword(password) {
        return password.length >= 8;
    }

    openAuthModalBtn?.addEventListener("click", openModal);

    closeButtons.forEach((btn) => {
        btn.addEventListener("click", closeModal);
    });

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && authModal && !authModal.classList.contains("hidden")) {
            closeModal();
        }
    });

    loginTabBtn?.addEventListener("click", () => switchTab("login"));
    registerTabBtn?.addEventListener("click", () => switchTab("register"));

    loginForm?.addEventListener("submit", async (e) => {
        e.preventDefault();
        clearMessage();

        const formData = new FormData(loginForm);
        const payload = {
            email: String(formData.get("email") || "").trim(),
            password: String(formData.get("password") || "")
        };

        if (!payload.email) {
            showMessage("Введите email");
            return;
        }

        if (!isValidEmail(payload.email)) {
            showMessage("Введите корректный email");
            return;
        }

        if (!payload.password) {
            showMessage("Введите пароль");
            return;
        }

        try {
            const response = await fetch("/auth/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok) {
                showMessage(normalizeServerError(data.detail, "Ошибка входа"));
                return;
            }

            showMessage("Вход выполнен успешно", "success");

            setTimeout(() => {
                window.location.reload();
            }, 400);
        } catch (error) {
            console.error(error);
            showMessage("Не удалось выполнить вход (ошибка сети)");
        }
    });
        registerForm?.addEventListener("submit", async (e) => {
            e.preventDefault();
            clearMessage();

            const formData = new FormData(registerForm);

            const name = String(formData.get("name") || "").trim();
            const email = String(formData.get("email") || "").trim();
            const phone = String(formData.get("phone") || "").trim();
            const password = String(formData.get("password") || "");
            const passwordConfirm = String(formData.get("password_confirm") || "");

            if (!email || !isValidEmail(email)) {
                showMessage("Введите корректный email");
                return;
            }

            if (!phone || !isValidPhone(phone)) {
                showMessage("Телефон должен начинаться с +7 или 8 и содержать ровно 11 цифр");
                return;
            }

            if (!password || !isValidPassword(password)) {
                showMessage("Пароль должен содержать не менее 8 символов");
                return;
            }

            if (password !== passwordConfirm) {
                showMessage("Пароли не совпадают");
                return;
            }

            try {
                const response = await fetch("/auth/register", {
                    method: "POST",
                    body: formData
                });

                const data = await response.json();

                if (!response.ok || data.success === false) {
                    let msg = "Ошибка регистрации";

                    if (data.errors) {
                        if (data.errors.email) {
                            msg = data.errors.email;
                        } else if (data.errors.phone) {
                            msg = data.errors.phone;
                        } else if (data.errors.general) {
                            msg = Array.isArray(data.errors.general)
                                ? data.errors.general.join("\n")
                                : data.errors.general;
                        } else {
                            msg = Object.values(data.errors).flat().join("\n");
                        }
                    } else if (data.message) {
                        msg = data.message;
                    }

                    showMessage(msg);
                    return;
                }

                showMessage("Регистрация успешна", "success");

                setTimeout(() => {
                    window.location.href = data.redirect_url || "/";
                }, 400);

            } catch (error) {
                console.error(error);
                showMessage("Не удалось соединиться с сервером (ошибка сети)");
            }
        });
});
