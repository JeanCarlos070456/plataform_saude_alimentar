(() => {
    const body = document.body;
    document.querySelector('[data-sidebar-toggle]')?.addEventListener('click', () => {
        body.classList.toggle('manager-menu-open');
    });
    document.querySelectorAll('form[data-confirm]').forEach((form) => {
        form.addEventListener('submit', (event) => {
            const message = form.dataset.confirm || 'Confirmar esta operação?';
            if (!window.confirm(message)) event.preventDefault();
        });
    });
})();
