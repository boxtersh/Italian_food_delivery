document.addEventListener("DOMContentLoaded", () => {
    const cartCountEls = document.querySelectorAll(".js-cart-badge");
    const logoutBtn = document.getElementById("logoutBtn");
    const addToCartForms = document.querySelectorAll(".js-add-to-cart-form");

    function updateCartCount(count) {
        cartCountEls.forEach((el) => {
            const numericCount = Number(count) || 0;
            el.textContent = numericCount;

            if (numericCount > 0) {
                el.style.display = "";
            } else {
                el.style.display = "none";
            }
        });
    }

    async function addToCart(dishId) {
        const formData = new FormData();
        formData.append("dish_id", dishId);

        try {
            const response = await fetch("/add-to-cart", {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                alert(data.error || "Ошибка при добавлении в корзину");
                return;
            }

            if (typeof data.cart_size !== "undefined") {
                updateCartCount(data.cart_size);
            }
        } catch (error) {
            console.error(error);
            alert("Не удалось добавить блюдо в корзину");
        }
    }

    addToCartForms.forEach((form) => {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const dishId =
                form.dataset.dishId ||
                form.querySelector('input[name="dish_id"]')?.value;

            if (!dishId) {
                console.error("dish_id не найден");
                return;
            }

            await addToCart(dishId);
        });
    });

    if (logoutBtn) {
        logoutBtn.addEventListener("click", async () => {
            try {
                const response = await fetch("/auth/logout", {
                    method: "POST"
                });

                const data = await response.json();

                if (!response.ok) {
                    alert(data.detail || "Ошибка выхода");
                    return;
                }

                window.location.reload();
            } catch (error) {
                console.error(error);
                alert("Не удалось выйти из аккаунта");
            }
        });
    }

    const params = new URLSearchParams(window.location.search);
    const authTab = params.get("auth");
    const returnFrom = params.get("return_from");

    if (authTab === "register" && returnFrom === "policy") {
        const modal = document.getElementById("authModal");
        const loginForm = document.getElementById("loginForm");
        const registerForm = document.getElementById("registerForm");
        const tabs = document.querySelectorAll(".auth-tab");
        const title = document.getElementById("authModalTitle");

        if (modal) {
            modal.classList.remove("hidden");
        }

        if (loginForm) {
            loginForm.classList.add("hidden");
        }

        if (registerForm) {
            registerForm.classList.remove("hidden");
        }

        tabs.forEach((tab) => {
            tab.classList.toggle("active", tab.dataset.authTab === "register");
        });

        if (title) {
            title.textContent = "Регистрация";
        }

        const cleanUrl = window.location.pathname;
        window.history.replaceState({}, document.title, cleanUrl);
    }
});