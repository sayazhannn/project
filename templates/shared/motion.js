// Общий движок анимаций для всех шаблонов.
// Подключается после lenis.min.js. Всё настраивается через классы и data-атрибуты:
//   [data-split]   — заголовок появляется по буквам
//   .reveal        — блок выезжает при прокрутке (задержка через style="--d:.2s")
//   [data-words]   — слова абзаца загораются по мере прокрутки
//   [data-count]   — счётчик: data-count="1500" data-decimals="1"
//   [data-speed]   — параллакс: data-speed="0.2"
//   .magnetic      — кнопка тянется к курсору
//   .tilt          — карточка наклоняется за курсором
//   .nav           — шапка прячется при прокрутке вниз
//   [data-tabs]    — вкладки: кнопки [data-tab="x"], панели [data-panel="x"]
(() => {
  const root = document.documentElement;
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  root.classList.add('js');

  // Буквы. Каждое слово — в отдельной обёртке, чтобы перенос строки не рвал слово посередине
  document.querySelectorAll('[data-split]').forEach((el) => {
    const text = el.textContent;
    el.textContent = '';
    el.setAttribute('aria-label', text);
    let i = 0;
    text.split(/(\s+)/).forEach((part) => {
      if (!part) return;
      if (/^\s+$/.test(part)) return el.appendChild(document.createTextNode(' '));
      const word = document.createElement('span');
      word.className = 'split-word';
      word.setAttribute('aria-hidden', 'true');
      [...part].forEach((ch) => {
        const span = document.createElement('span');
        span.className = 'char';
        span.style.setProperty('--i', i++);
        span.textContent = ch;
        word.appendChild(span);
      });
      el.appendChild(word);
    });
  });

  // Слова
  const words = [];
  document.querySelectorAll('[data-words]').forEach((el) => {
    const walk = (node) => {
      [...node.childNodes].forEach((child) => {
        if (child.nodeType !== Node.TEXT_NODE) return walk(child);
        const frag = document.createDocumentFragment();
        child.textContent.split(/(\s+)/).forEach((part) => {
          if (!part) return;
          if (/^\s+$/.test(part)) return frag.appendChild(document.createTextNode(part));
          const span = document.createElement('span');
          span.className = 'word';
          span.textContent = part;
          frag.appendChild(span);
          words.push(span);
        });
        child.replaceWith(frag);
      });
    };
    walk(el);
  });

  // Старт: показываем первый экран
  const ready = () => requestAnimationFrame(() => root.classList.add('is-ready'));
  if (document.fonts && document.fonts.ready) {
    Promise.race([document.fonts.ready, new Promise((r) => setTimeout(r, 1200))]).then(ready);
  } else {
    ready();
  }

  // Плавный скролл
  let lenis = null;
  if (!reduceMotion && window.Lenis) {
    lenis = new Lenis({ lerp: 0.09, smoothWheel: true });
    const raf = (time) => {
      lenis.raf(time);
      requestAnimationFrame(raf);
    };
    requestAnimationFrame(raf);
  }
  document.querySelectorAll('a[href^="#"]').forEach((a) => {
    a.addEventListener('click', (e) => {
      const id = a.getAttribute('href');
      const target = id.length > 1 && document.querySelector(id);
      if (!target) return;
      e.preventDefault();
      if (lenis) lenis.scrollTo(target, { offset: -20, duration: 1.3 });
      else target.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth' });
    });
  });

  // Появление при прокрутке
  const io = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('is-in');
      io.unobserve(entry.target);
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
  document.querySelectorAll('.reveal').forEach((el) => io.observe(el));

  // Счётчики
  const fmt = (n, decimals) =>
    n.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  const countIO = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const el = entry.target;
      const to = parseFloat(el.dataset.count);
      const decimals = parseInt(el.dataset.decimals || '0', 10);
      const duration = reduceMotion ? 0 : 1800;
      const t0 = performance.now();
      const tick = (now) => {
        const p = duration ? Math.min((now - t0) / duration, 1) : 1;
        el.textContent = fmt(to * (1 - Math.pow(1 - p, 4)), decimals);
        if (p < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
      countIO.unobserve(el);
    });
  }, { threshold: 0.5 });
  document.querySelectorAll('[data-count]').forEach((el) => countIO.observe(el));

  // Вкладки
  document.querySelectorAll('[data-tabs]').forEach((box) => {
    const buttons = box.querySelectorAll('[data-tab]');
    const panels = box.querySelectorAll('[data-panel]');
    buttons.forEach((btn) => {
      btn.addEventListener('click', () => {
        buttons.forEach((b) => b.setAttribute('aria-selected', b === btn));
        panels.forEach((p) => { p.hidden = p.dataset.panel !== btn.dataset.tab; });
      });
    });
  });

  // Шапка, параллакс, слова
  const nav = document.querySelector('.nav');
  const parallax = [...document.querySelectorAll('[data-speed]')];
  let lastY = 0;
  const onScroll = () => {
    const y = window.scrollY;
    if (nav) {
      nav.classList.toggle('is-scrolled', y > 20);
      nav.classList.toggle('is-hidden', y > lastY && y > 500);
    }
    lastY = y;
    if (!reduceMotion && window.innerWidth > 800) {
      parallax.forEach((el) => {
        // translate, а не transform — чтобы не мешать анимациям и появлению блока
        el.style.translate = `0 ${y * parseFloat(el.dataset.speed)}px`;
      });
    }
    const vh = window.innerHeight;
    words.forEach((w) => w.classList.toggle('is-lit', w.getBoundingClientRect().top < vh * 0.78));
  };
  if (lenis) lenis.on('scroll', onScroll);
  else window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  if (!finePointer || reduceMotion) return;

  document.querySelectorAll('.magnetic').forEach((btn) => {
    btn.addEventListener('mousemove', (e) => {
      const r = btn.getBoundingClientRect();
      const x = e.clientX - r.left - r.width / 2;
      const y = e.clientY - r.top - r.height / 2;
      btn.style.transform = `translate(${x * 0.25}px, ${y * 0.35}px)`;
    });
    btn.addEventListener('mouseleave', () => { btn.style.transform = ''; });
  });

  document.querySelectorAll('.tilt').forEach((card) => {
    card.addEventListener('mousemove', (e) => {
      const r = card.getBoundingClientRect();
      const px = (e.clientX - r.left) / r.width - 0.5;
      const py = (e.clientY - r.top) / r.height - 0.5;
      card.style.transform = `perspective(900px) rotateY(${px * 7}deg) rotateX(${-py * 7}deg) translateY(-4px)`;
    });
    card.addEventListener('mouseleave', () => { card.style.transform = ''; });
  });
})();
