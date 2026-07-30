(() => {
    const body = document.body;
    const menuButton = document.querySelector('[data-home-menu]');
    const navigation = document.querySelector('[data-home-nav]');
    const modal = document.querySelector('[data-gallery-modal]');
    const modalImage = modal?.querySelector('[data-modal-image]');
    const modalTitle = modal?.querySelector('[data-modal-title]');
    const modalText = modal?.querySelector('[data-modal-text]');

    const closeMenu = () => {
        body.classList.remove('home-menu-open');
        menuButton?.setAttribute('aria-expanded', 'false');
    };

    menuButton?.addEventListener('click', () => {
        const open = !body.classList.contains('home-menu-open');
        body.classList.toggle('home-menu-open', open);
        menuButton.setAttribute('aria-expanded', String(open));
    });

    navigation?.querySelectorAll('a').forEach((link) => {
        link.addEventListener('click', closeMenu);
    });

    document.querySelectorAll('[data-gallery-open]').forEach((button) => {
        button.addEventListener('click', () => {
            if (!modal || !modalImage || !modalTitle || !modalText) return;
            modalImage.src = button.dataset.image || '';
            modalImage.alt = button.dataset.alt || '';
            modalTitle.textContent = button.dataset.title || '';
            modalText.textContent = button.dataset.text || '';
            modal.showModal();
        });
    });

    modal?.querySelector('[data-modal-close]')?.addEventListener('click', () => modal.close());
    modal?.addEventListener('click', (event) => {
        if (event.target === modal) modal.close();
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closeMenu();
            if (modal?.open) modal.close();
        }
    });

    const year = document.querySelector('[data-current-year]');
    if (year) year.textContent = String(new Date().getFullYear());
})();
