(() => {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  // Разбиваем заголовок на буквы
  document.querySelectorAll('.split').forEach((el) => {
    const text = el.textContent;
    el.textContent = '';
    [...text].forEach((ch, i) => {
      const span = document.createElement('span');
      span.className = 'char';
      span.style.setProperty('--i', i);
      span.textContent = ch;
      el.appendChild(span);
    });
  });

  // Разбиваем абзац «О нас» на слова — они подсвечиваются по мере скролла
  const words = [];
  document.querySelectorAll('.words').forEach((el) => {
    const walk = (node) => {
      [...node.childNodes].forEach((child) => {
        if (child.nodeType === Node.TEXT_NODE) {
          const frag = document.createDocumentFragment();
          child.textContent.split(/(\s+)/).forEach((part) => {
            if (!part) return;
            if (/^\s+$/.test(part)) {
              frag.appendChild(document.createTextNode(part));
            } else {
              const span = document.createElement('span');
              span.className = 'word';
              span.textContent = part;
              frag.appendChild(span);
              words.push(span);
            }
          });
          child.replaceWith(frag);
        } else {
          walk(child);
        }
      });
    };
    walk(el);
  });

  // Плавный скролл
  let lenis = null;
  if (!reduceMotion && window.Lenis) {
    lenis = new Lenis({ lerp: 0.085, smoothWheel: true });
    document.querySelectorAll('a[href^="#"]').forEach((a) => {
      a.addEventListener('click', (e) => {
        const target = document.querySelector(a.getAttribute('href'));
        if (!target) return;
        e.preventDefault();
        lenis.scrollTo(target, { offset: -20, duration: 1.4 });
      });
    });
  }

  // Прелоадер
  const start = () => {
    document.querySelector('.loader').classList.add('is-done');
    document.body.classList.remove('is-loading');
    requestAnimationFrame(() => document.body.classList.add('is-ready'));
    revealHero();
  };
  const revealHero = () => {
    document.querySelectorAll('.hero .reveal').forEach((el) => el.classList.add('is-in'));
  };
  if (reduceMotion) {
    start();
  } else {
    window.addEventListener('load', () => setTimeout(start, 900));
    setTimeout(start, 3000); // на случай, если что-то грузится слишком долго
  }

  // Появление блоков при скролле
  const io = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-in');
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15, rootMargin: '0px 0px -60px 0px' });
  document.querySelectorAll('.reveal:not(.hero .reveal)').forEach((el) => io.observe(el));

  // Счётчики
  const formatNum = (n, decimals, sep) => {
    const fixed = n.toFixed(decimals);
    return sep ? fixed.replace(/\B(?=(\d{3})+(?!\d))/g, ' ') : fixed;
  };
  const countIO = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const el = entry.target;
      const to = parseFloat(el.dataset.to);
      const decimals = parseInt(el.dataset.decimals || '0', 10);
      const sep = el.dataset.sep === '1';
      const duration = reduceMotion ? 0 : 1800;
      const t0 = performance.now();
      const tick = (now) => {
        const p = duration ? Math.min((now - t0) / duration, 1) : 1;
        const eased = 1 - Math.pow(1 - p, 4);
        el.textContent = formatNum(to * eased, decimals, sep);
        if (p < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
      countIO.unobserve(el);
    });
  }, { threshold: 0.6 });
  document.querySelectorAll('.count').forEach((el) => countIO.observe(el));

  // Навигация: прячется при скролле вниз, появляется при скролле вверх
  const nav = document.querySelector('.nav');
  let lastY = 0;

  // Параллакс
  // На узком экране картинка стоит под текстом, поэтому двигаем только фон
  const parallax = [...document.querySelectorAll('[data-speed]')]
    .filter((el) => window.innerWidth > 900 || !el.classList.contains('hero__art'));

  const onScroll = (y) => {
    nav.classList.toggle('is-scrolled', y > 20);
    nav.classList.toggle('is-hidden', y > lastY && y > 400);
    lastY = y;

    if (!reduceMotion) {
      parallax.forEach((el) => {
        el.style.transform = `translate3d(0, ${y * parseFloat(el.dataset.speed)}px, 0)`;
      });
    }

    // Подсветка слов
    const vh = window.innerHeight;
    words.forEach((w) => {
      const top = w.getBoundingClientRect().top;
      w.classList.toggle('is-lit', top < vh * 0.75);
    });
  };

  if (lenis) {
    lenis.on('scroll', ({ scroll }) => onScroll(scroll));
    const raf = (time) => {
      lenis.raf(time);
      requestAnimationFrame(raf);
    };
    requestAnimationFrame(raf);
  } else {
    window.addEventListener('scroll', () => onScroll(window.scrollY), { passive: true });
  }
  onScroll(window.scrollY);

  if (!finePointer || reduceMotion) return;

  // Курсор
  const cursor = document.querySelector('.cursor');
  let mx = 0, my = 0, cx = 0, cy = 0;
  window.addEventListener('mousemove', (e) => {
    mx = e.clientX;
    my = e.clientY;
    cursor.classList.add('is-active');
  });
  const moveCursor = () => {
    cx += (mx - cx) * 0.18;
    cy += (my - cy) * 0.18;
    cursor.style.transform = `translate3d(${cx}px, ${cy}px, 0)`;
    requestAnimationFrame(moveCursor);
  };
  moveCursor();
  document.querySelectorAll('a, .dish').forEach((el) => {
    el.addEventListener('mouseenter', () => cursor.classList.add('is-hover'));
    el.addEventListener('mouseleave', () => cursor.classList.remove('is-hover'));
  });

  // Магнитные кнопки
  document.querySelectorAll('.magnetic').forEach((btn) => {
    btn.addEventListener('mousemove', (e) => {
      const r = btn.getBoundingClientRect();
      const x = e.clientX - r.left - r.width / 2;
      const y = e.clientY - r.top - r.height / 2;
      btn.style.transform = `translate(${x * 0.25}px, ${y * 0.35}px)`;
    });
    btn.addEventListener('mouseleave', () => { btn.style.transform = ''; });
  });

  // Наклон карточек меню
  document.querySelectorAll('.tilt').forEach((card) => {
    card.addEventListener('mousemove', (e) => {
      const r = card.getBoundingClientRect();
      const px = (e.clientX - r.left) / r.width - 0.5;
      const py = (e.clientY - r.top) / r.height - 0.5;
      card.style.transform = `perspective(900px) rotateY(${px * 8}deg) rotateX(${-py * 8}deg) translateY(-4px)`;
    });
    card.addEventListener('mouseleave', () => { card.style.transform = ''; });
  });
})();
