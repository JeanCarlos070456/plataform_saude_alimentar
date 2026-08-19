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

    const carousel = document.querySelector('[data-hero-carousel]');
    if (carousel) {
        const slides = Array.from(carousel.querySelectorAll('[data-hero-slide]'));
        const dots = Array.from(carousel.querySelectorAll('[data-hero-dot]'));
        const previousButton = carousel.querySelector('[data-hero-prev]');
        const nextButton = carousel.querySelector('[data-hero-next]');
        const interval = Number(carousel.dataset.interval || 5000);
        const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        let currentIndex = 0;
        let timer = null;

        const showSlide = (index) => {
            if (!slides.length) return;
            currentIndex = (index + slides.length) % slides.length;
            slides.forEach((slide, position) => {
                const active = position === currentIndex;
                slide.classList.toggle('is-active', active);
                slide.setAttribute('aria-hidden', String(!active));
            });
            dots.forEach((dot, position) => {
                const active = position === currentIndex;
                dot.classList.toggle('is-active', active);
                dot.setAttribute('aria-current', String(active));
            });
        };

        const stopAutoPlay = () => {
            if (timer) window.clearInterval(timer);
            timer = null;
        };

        const startAutoPlay = () => {
            stopAutoPlay();
            if (reduceMotion || slides.length <= 1) return;
            timer = window.setInterval(() => showSlide(currentIndex + 1), interval);
        };

        previousButton?.addEventListener('click', () => {
            showSlide(currentIndex - 1);
            startAutoPlay();
        });
        nextButton?.addEventListener('click', () => {
            showSlide(currentIndex + 1);
            startAutoPlay();
        });
        dots.forEach((dot) => {
            dot.addEventListener('click', () => {
                showSlide(Number(dot.dataset.heroDot || 0));
                startAutoPlay();
            });
        });
        carousel.addEventListener('mouseenter', stopAutoPlay);
        carousel.addEventListener('mouseleave', startAutoPlay);
        carousel.addEventListener('focusin', stopAutoPlay);
        carousel.addEventListener('focusout', startAutoPlay);
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) stopAutoPlay();
            else startAutoPlay();
        });

        showSlide(0);
        startAutoPlay();
    }

    const year = document.querySelector('[data-current-year]');
    if (year) year.textContent = String(new Date().getFullYear());
})();
