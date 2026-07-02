document.addEventListener("DOMContentLoaded", function () {
    const toastContainer = document.getElementById("toastContainer");

    function showAddToCartToast(dishName) {
        const toast = document.createElement("div");
        toast.className = "cart-toast";
        toast.innerHTML = `
            <div class="cart-toast-icon">✓</div>
            <div class="cart-toast-content">
                <div class="cart-toast-title">Добавлено в корзину</div>
                <div class="cart-toast-text">${dishName} добавлена</div>
            </div>
            <button type="button" class="cart-toast-close" aria-label="Закрыть">×</button>
        `;

        toastContainer.appendChild(toast);

        requestAnimationFrame(() => {
            toast.classList.add("show");
        });

        const autoRemove = setTimeout(() => {
            hideToast(toast);
        }, 2600);

        const closeBtn = toast.querySelector(".cart-toast-close");
        closeBtn.addEventListener("click", () => {
            clearTimeout(autoRemove);
            hideToast(toast);
        });
    }

    function hideToast(toast) {
        toast.classList.remove("show");
        toast.classList.add("hide");

        setTimeout(() => {
            toast.remove();
        }, 300);
    }

    document.querySelectorAll(".js-add-to-cart-form").forEach((form) => {
        form.addEventListener("submit", function () {
            const dishNameInput = form.querySelector('input[name="dish_name"]');
            const dishName = dishNameInput ? dishNameInput.value : "Блюдо";
            showAddToCartToast(dishName);
        });
    });
});