document.addEventListener('DOMContentLoaded', () => {
    const selector = document.getElementById('edit-dish-selector');
    const form = document.getElementById('editDishForm');
    const idInput = document.getElementById('edit-dish-id');
    const nameInput = document.getElementById('edit-name');
    const priceInput = document.getElementById('edit-price');
    const descInput = document.getElementById('edit-description');
    const imageInput = document.getElementById('edit-image-url');
    const availCheckbox = document.getElementById('edit-is-available');

    selector.addEventListener('change', () => {
        const option = selector.options[selector.selectedIndex];
        if (!option.value) {
            form.reset();
            idInput.value = '';
            return;
        }

        idInput.value = option.value;
        nameInput.value = option.dataset.name || '';
        priceInput.value = option.dataset.price !== undefined ? option.dataset.price : '';
        descInput.value = option.dataset.description || '';
        imageInput.value = option.dataset.image || '';

        const isAvailable = option.dataset.available === 'True' || option.dataset.available === 'true';
        availCheckbox.checked = isAvailable;
    });
});
