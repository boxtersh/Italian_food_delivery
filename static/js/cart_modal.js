function openRemoveModal(dishName, actionUrl) {
    const backdrop = document.getElementById('removeModalBackdrop');
    const body = document.getElementById('removeModalBody');
    const form = document.getElementById('removeForm');

    body.textContent = `Вы уверены, что хотите удалить «${dishName}»?`;
    form.action = actionUrl;
    backdrop.classList.add('show');
}

function closeRemoveModal() {
    document.getElementById('removeModalBackdrop').classList.remove('show');
}

function openClearModal(actionUrl) {
    const backdrop = document.getElementById('clearModalBackdrop');
    const form = document.getElementById('clearForm');

    form.action = actionUrl;
    backdrop.classList.add('show');
}

function closeClearModal() {
    document.getElementById('clearModalBackdrop').classList.remove('show');
}

const backdrops = [
    document.getElementById('removeModalBackdrop'),
    document.getElementById('clearModalBackdrop')
];

backdrops.forEach(backdrop => {
    if (backdrop) {
        backdrop.addEventListener('click', (e) => {
            if (e.target === backdrop) {
                backdrop.classList.remove('show');
            }
        });
    }
});
