"""Генератор сайтов: из описания компании (словарь) собирает одну самодостаточную HTML-страницу.

Запуск: python3 tools/build_sites.py
"""
from html import escape as e
from urllib.parse import quote

# ---------------------------------------------------------------- иконки (24×24, обводка)
ICONS = {
    'check': '<path d="M20 6 9 17l-5-5"/>',
    'clock': '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    'star': '<path d="M12 2l3.1 6.3 6.9 1-5 4.9 1.2 6.8L12 17.8 5.8 21l1.2-6.8-5-4.9 6.9-1z"/>',
    'shield': '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
    'heart': '<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1.1L12 21l7.8-7.6 1-1.1a5.5 5.5 0 0 0 0-7.7z"/>',
    'pin': '<path d="M21 10c0 7-9 13-9 13S3 17 3 10a9 9 0 1 1 18 0z"/><circle cx="12" cy="10" r="3"/>',
    'users': '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/>',
    'gift': '<path d="M20 12v10H4V12M2 7h20v5H2zM12 22V7M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7zM12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z"/>',
    'award': '<circle cx="12" cy="8" r="7"/><path d="M8.2 13.9 7 23l5-3 5 3-1.2-9.1"/>',
    'sparkle': '<path d="M12 3l1.9 5.8L20 11l-6.1 2.2L12 19l-1.9-5.8L4 11l6.1-2.2z"/><path d="M19 3v4M17 5h4"/>',
    'leaf': '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.5 19 2c1 2 2 4.2 2 8 0 5.5-4.8 10-10 10z"/><path d="M2 21c0-3 1.9-5.4 5.1-6"/>',
    'truck': '<path d="M1 3h15v13H1zM16 8h4l3 3v5h-7z"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>',
    'card': '<rect x="1" y="4" width="22" height="16" rx="2"/><path d="M1 10h22"/>',
    'chat': '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    'tooth': '<path d="M7 3c-3 0-4 3-3.5 6 .4 2.5 1.5 4 2 7 .4 2.5 1 5 2.5 5s1.6-3 2-5 1-3 2-3 1.6 1 2 3 .5 5 2 5 2.1-2.5 2.5-5c.5-3 1.6-4.5 2-7 .5-3-.5-6-3.5-6-2 0-3 1-5 1S9 3 7 3z"/>',
    'scissors': '<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M20 4 8.1 15.9M14.5 14.5 20 20M8.1 8.1 12 12"/>',
    'drop': '<path d="M12 2.7l5.7 5.6a8 8 0 1 1-11.3 0z"/>',
    'dumbbell': '<path d="M6.5 6.5v11M17.5 6.5v11M3 9v6M21 9v6M6.5 12h11"/>',
    'music': '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>',
    'book': '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V2H6.5A2.5 2.5 0 0 0 4 4.5v15z"/><path d="M20 17v5H6.5A2.5 2.5 0 0 1 4 19.5"/>',
    'car': '<path d="M5 17H3v-5l2-5h14l2 5v5h-2M5 12h14M9 17h6"/><circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/>',
    'wrench': '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.8-3.8a6 6 0 0 1-7.9 7.9l-6.9 6.9a2.1 2.1 0 0 1-3-3l6.9-6.9a6 6 0 0 1 7.9-7.9z"/>',
    'home': '<path d="M3 10.5 12 3l9 7.5V21H3zM9 21v-6h6v6"/>',
    'cup': '<path d="M17 8h1a4 4 0 1 1 0 8h-1M3 8h14v9a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4zM6 2v3M10 2v3M14 2v3"/>',
    'cake': '<path d="M20 21v-9a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v9M4 16c2 0 2-1.5 4-1.5s2 1.5 4 1.5 2-1.5 4-1.5 2 1.5 4 1.5M2 21h20M12 10V6"/><path d="M12 2.5c.8.8 1 1.6 0 2.5-1-.9-.8-1.7 0-2.5z"/>',
    'pizza': '<path d="M12 2 2.5 20.5h19zM5 15c4-2 10-2 14 0"/><circle cx="12" cy="10" r="1"/><circle cx="9" cy="17" r="1"/><circle cx="15" cy="17" r="1"/>',
    'fish': '<path d="M6.5 12c3-5 9-6.5 14.5 0-5.5 6.5-11.5 5-14.5 0zM6.5 12 2 8v8z"/><circle cx="16.5" cy="11" r=".6"/>',
    'camera': '<path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/>',
    'flower': '<circle cx="12" cy="6.5" r="3.5"/><circle cx="17.5" cy="12" r="3.5"/><circle cx="12" cy="17.5" r="3.5"/><circle cx="6.5" cy="12" r="3.5"/><circle cx="12" cy="12" r="1.6"/>',
    'plane': '<path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/>',
    'paw': '<circle cx="4.5" cy="9" r="2"/><circle cx="9" cy="4.5" r="2"/><circle cx="15" cy="4.5" r="2"/><circle cx="19.5" cy="9" r="2"/><path d="M8 15c-2 3-1 6 2 6h4c3 0 4-3 2-6-1.5-2-2.5-3.5-4-3.5S9.5 13 8 15z"/>',
    'phone': '<rect x="5" y="2" width="14" height="20" rx="2"/><path d="M12 18h.01"/>',
    'scale': '<path d="M12 3v18M5 21h14M3 7h18M6 7l-3 7a3 3 0 0 0 6 0zM18 7l-3 7a3 3 0 0 0 6 0z"/>',
    'calc': '<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M8 6h8M8 11h.01M12 11h.01M16 11h.01M8 15h.01M12 15h.01M16 15h.01M8 19h8"/>',
    'shirt': '<path d="M20.4 3.5 16 2a4 4 0 0 1-8 0L3.6 3.5a2 2 0 0 0-1.3 2.2l.6 3.5a1 1 0 0 0 1 .8H6v10a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V10h2.2a1 1 0 0 0 1-.8l.6-3.5a2 2 0 0 0-1.4-2.2z"/>',
    'brush': '<path d="M9.1 11.2 18.5 2a2.1 2.1 0 0 1 3 3l-9.3 9.4"/><path d="M7 14a3 3 0 0 0-3 3c0 1.3-2 2-2 2s2 2 5 2a4 4 0 0 0 4-4 3 3 0 0 0-4-3z"/>',
    'eye': '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    'user': '<circle cx="12" cy="7" r="4"/><path d="M5 21v-2a7 7 0 0 1 14 0v2"/>',
    'sun': '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    'key': '<circle cx="7.5" cy="15.5" r="5.5"/><path d="M11.5 11.5 21 2M17 6l3 3M14.5 8.5l2.5 2.5"/>',
    'mic': '<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M19 10a7 7 0 0 1-14 0M12 17v5"/>',
    'code': '<path d="M16 18l6-6-6-6M8 6l-6 6 6 6"/>',
    'fire': '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.4-.5-2-1-3-1.1-2.1-.2-4 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.2.4-2.3 1-3.3a2.5 2.5 0 0 0 2.5 2.8z"/>',
    'bolt': '<path d="M13 2 3 14h9l-1 8 10-12h-9z"/>',
    'sofa': '<path d="M20 9V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v3M2 11a2 2 0 0 1 4 0v3h12v-3a2 2 0 0 1 4 0v6H2zM4 17v3M20 17v3"/>',
    'glasses': '<circle cx="6" cy="15" r="4"/><circle cx="18" cy="15" r="4"/><path d="M10 15h4M2 15l2-8h2M22 15l-2-8h-2"/>',
    'balloon': '<path d="M12 2a6 6 0 0 0-6 6c0 4 3 7 6 8 3-1 6-4 6-8a6 6 0 0 0-6-6zM12 16l-1 2h2zM12 18c0 2-2 2-2 4"/>',
    'spray': '<path d="M9 13h6v9H9zM10 13V9h4v4M14 10h3l2-2M3 3h.01M7 5h.01M3 7h.01M7 9h.01M3 11h.01"/>',
    'tire': '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/><path d="M12 2v6M12 16v6M2 12h6M16 12h6"/>',
    'wave': '<path d="M2 6c2 0 2 2 4 2s2-2 4-2 2 2 4 2 2-2 4-2 2 2 4 2M2 12c2 0 2 2 4 2s2-2 4-2 2 2 4 2 2-2 4-2 2 2 4 2M2 18c2 0 2 2 4 2s2-2 4-2 2 2 4 2 2-2 4-2 2 2 4 2"/>',
    'globe': '<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20"/>',
    'wheel': '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="2"/><path d="M12 14v8M10.3 11 2.5 9M13.7 11l7.8-2"/>',
    'doc': '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h5"/>',
    'bed': '<path d="M2 4v16M2 8h18a2 2 0 0 1 2 2v10M2 17h20"/><circle cx="7" cy="12" r="2"/>',
    'needle': '<path d="M3 21 15 9M14 4l6 6M17 3l4 4-9 9-4-4z"/>',
    'hand': '<path d="M18 11V6a2 2 0 0 0-4 0v5M14 10V4a2 2 0 0 0-4 0v6M10 10.5V6a2 2 0 0 0-4 0v8"/><path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.9-6-2.4l-3.6-3.6a2 2 0 0 1 2.8-2.8L7 15"/>',
    'map': '<path d="M1 6v16l7-4 8 4 7-4V2l-7 4-8-4z"/><path d="M8 2v16M16 6v16"/>',
}


def icon(name, cls='ico'):
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            f'{ICONS[name]}</svg>')


WA_ICON = ('<svg class="wa-ico" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2z"/>'
           '<path fill="currentColor" d="M16.5 14.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.2-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5c-.2 0-.5.1-.7.3-.2.3-.9.9-.9 2.2s.9 2.5 1 2.7c.1.2 1.8 2.8 4.4 3.9 1.6.7 2.3.8 3.1.6.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.2-1.2-.1-.1-.3-.2-.5-.3z"/></svg>')

# ---------------------------------------------------------------- стили оформления
SKINS = {
    # шрифт заголовков, шрифт текста, радиус, начертание заголовков, регистр, межбуквенный интервал
    'editorial':  dict(display='Cormorant Garamond', body='Manrope', r='6px', hw=500, ht='none', hs='-0.01em', scale=1.12),
    'luxe':       dict(display='Playfair Display', body='Jost', r='2px', hw=500, ht='none', hs='0', scale=1.0),
    'bold':       dict(display='Unbounded', body='Manrope', r='26px', hw=700, ht='uppercase', hs='-0.02em', scale=.86),
    'soft':       dict(display='Nunito', body='Nunito', r='30px', hw=800, ht='none', hs='-0.01em', scale=1.0),
    'clean':      dict(display='Onest', body='Onest', r='18px', hw=700, ht='none', hs='-0.03em', scale=.95),
    'industrial': dict(display='Oswald', body='Golos Text', r='4px', hw=700, ht='uppercase', hs='0', scale=1.05),
}

FONT_WEIGHTS = {
    'Cormorant Garamond': 'ital,wght@0,500;0,600;1,500', 'Playfair Display': 'ital,wght@0,500;0,700;1,500',
    'Literata': 'ital,opsz,wght@0,7..72,500;0,7..72,700;1,7..72,500', 'Prata': '', 'Lora': 'ital,wght@0,500;0,600;1,500',
    'Spectral': 'ital,wght@0,500;0,600;1,500', 'Forum': '', 'Unbounded': 'wght@500;700;800',
    'Montserrat': 'wght@500;700;800', 'Rubik': 'wght@500;700;800', 'Manrope': 'wght@400;500;600;700;800',
    'Nunito': 'wght@400;600;700;800', 'Comfortaa': 'wght@500;700', 'Onest': 'wght@400;500;600;700',
    'Golos Text': 'wght@400;500;600;700', 'Oswald': 'wght@500;600;700', 'Russo One': '',
    'Roboto Condensed': 'wght@500;700', 'Jost': 'wght@300;400;500;600', 'Nunito Sans': 'wght@400;600;700',
    'Commissioner': 'wght@400;500;600', 'Exo 2': 'wght@400;500;600;700', 'Raleway': 'wght@400;500;600;700;800',
    'PT Sans': 'wght@400;700', 'Yeseva One': '', 'Alice': '', 'Tenor Sans': '', 'Philosopher': 'wght@400;700',
}

MODES = {
    'booking': dict(cta='Записаться', form='Онлайн-запись', live='Ближайшая запись', date='Дата визита',
                    hello='Здравствуйте! Хочу записаться', per='Хочу записаться: ', svc='Услуга', send='Записаться в WhatsApp'),
    'order':   dict(cta='Заказать', form='Оформить заказ', live='Доставка', date='Дата доставки',
                    hello='Здравствуйте! Хочу сделать заказ', per='Хочу заказать: ', svc='Что заказать', send='Отправить заказ в WhatsApp'),
    'request': dict(cta='Оставить заявку', form='Заявка', live='Выезд мастера', date='Удобная дата',
                    hello='Здравствуйте! Хочу оставить заявку', per='Интересует: ', svc='Услуга', send='Отправить заявку в WhatsApp'),
}

DEFAULT_STEPS = {
    'booking': [('Выберите услугу', 'Посмотрите цены ниже или спросите администратора.'),
                ('Напишите в WhatsApp', 'Форма соберёт сообщение сама — останется нажать «Отправить».'),
                ('Подтверждение', 'Администратор ответит в течение 15 минут и закрепит время.'),
                ('Приходите', 'Напомним о визите за день, а после — подскажем по уходу.')],
    'order':   [('Выберите', 'Позиции и цены — в меню ниже.'),
                ('Напишите в WhatsApp', 'Форма соберёт заказ в одно сообщение.'),
                ('Подтверждение', 'Уточним детали, время и способ оплаты.'),
                ('Получите', 'Доставим или подготовим к самовывозу точно ко времени.')],
    'request': [('Заявка', 'Опишите задачу в форме — она уйдёт в WhatsApp.'),
                ('Консультация', 'Перезвоним, уточним детали и назовём ориентир по цене.'),
                ('Договор', 'Фиксируем объём работ, сроки и стоимость.'),
                ('Результат', 'Выполняем работу и даём гарантию.')],
}

COMMON_FAQ = [('Как можно оплатить?', 'Наличными, картой и через Kaspi QR. Для юрлиц — по счёту.')]


def mix(fg, pct, base):
    return f'color-mix(in srgb, {fg} {pct}%, {base})'


def lum(hex_):
    h = hex_.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def wa_link(phone, text):
    return f'https://wa.me/{phone}?text={quote(text)}'


def fonts_url(families):
    parts = []
    for fam in dict.fromkeys(families):
        w = FONT_WEIGHTS.get(fam, '')
        parts.append('family=' + fam.replace(' ', '+') + (f':{w}' if w else ''))
    return 'https://fonts.googleapis.com/css2?' + '&'.join(parts) + '&display=swap'


# ---------------------------------------------------------------- CSS и JS (общие для всех сайтов)
CSS = r"""
*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;overflow-x:clip}
html.lenis,html.lenis body{height:auto}
.lenis.lenis-smooth{scroll-behavior:auto!important}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--body);font-size:17px;line-height:1.6;overflow-x:clip;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
img,svg{max-width:100%}
h1,h2,h3{margin:0;font-family:var(--display);font-weight:var(--hw);text-transform:var(--ht);letter-spacing:var(--hs);line-height:1.04;text-wrap:balance}
p{margin:0}
button,input,select,textarea{font:inherit;color:inherit}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
.ico{width:24px;height:24px;flex:none}
.wa-ico{width:20px;height:20px;flex:none}
.wrap{width:100%;max-width:1240px;margin:0 auto;padding-left:max(20px,5vw);padding-right:max(20px,5vw)}
.eyebrow{display:inline-flex;align-items:center;gap:10px;font-size:13px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)}
.eyebrow::before{content:"";width:28px;height:1px;background:currentColor}
.sec{padding:110px 0}
.sec-head{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;gap:20px 40px;margin-bottom:50px}
.sec-head h2{font-size:calc(clamp(36px,5.2vw,72px)*var(--scale));max-width:820px;margin-top:14px}
.sec-head p{max-width:420px;color:var(--muted)}
.sec-head h2 em,.hero h1 em{font-style:var(--em-style);color:var(--accent)}

/* кнопки */
.btn{position:relative;display:inline-flex;align-items:center;justify-content:center;gap:10px;padding:16px 26px;border:0;border-radius:var(--rb);background:var(--accent);color:var(--on-accent);font-weight:600;font-size:15px;line-height:1.2;cursor:pointer;overflow:hidden;isolation:isolate;transition:transform .45s var(--ease),color .4s,box-shadow .4s}
.btn::before{content:"";position:absolute;inset:0;z-index:-1;background:var(--fg);transform:translateY(101%);transition:transform .55s var(--ease)}
.btn:hover::before{transform:none}
.btn:hover{color:var(--bg)}
.btn--ghost{background:transparent;color:var(--fg);box-shadow:inset 0 0 0 1px var(--line-strong)}
.btn--wa{background:#25D366;color:#fff}
.btn--wa::before{background:#128C4B}
.btn--wa:hover{color:#fff}
.btn--small{padding:11px 18px;font-size:14px}

/* шапка */
.nav{position:fixed;top:0;left:0;right:0;z-index:50;padding:16px 0;transition:transform .6s var(--ease),background .4s,box-shadow .4s}
.nav.is-scrolled{background:color-mix(in srgb,var(--bg) 86%,transparent);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);box-shadow:0 1px 0 var(--line)}
.nav.is-hidden{transform:translateY(-110%)}
.nav .wrap{display:flex;align-items:center;justify-content:space-between;gap:20px}
.logo{display:flex;align-items:center;gap:10px;font-family:var(--display);font-weight:var(--hw);font-size:22px;text-transform:var(--ht);letter-spacing:var(--hs);white-space:nowrap}
.logo__mark{width:38px;height:38px;border-radius:calc(var(--r)*.6 + 4px);display:grid;place-items:center;background:var(--accent);color:var(--on-accent)}
.logo__mark .ico{width:20px;height:20px}
.nav__links{display:flex;gap:28px;font-size:15px;font-weight:500}
.nav__links a{position:relative}
.nav__links a::after{content:"";position:absolute;left:0;bottom:-4px;width:100%;height:1px;background:currentColor;transform:scaleX(0);transform-origin:right;transition:transform .5s var(--ease)}
.nav__links a:hover::after{transform:scaleX(1);transform-origin:left}
@media (max-width:900px){.nav__links{display:none}}
@media (max-width:420px){.nav .btn span{display:none}.nav .btn{padding:11px}}

/* первый экран */
.hero{position:relative;padding:150px 0 90px;overflow:hidden}
.hero__bg{position:absolute;inset:0;z-index:-1;pointer-events:none}
.hero__bg span{position:absolute;border-radius:50%;filter:blur(70px);opacity:var(--blob-o);animation:blob 16s ease-in-out infinite alternate}
.hero__bg span:nth-child(1){width:42vw;height:42vw;background:var(--accent);top:-14vw;right:-12vw}
.hero__bg span:nth-child(2){width:30vw;height:30vw;background:var(--accent2);bottom:-12vw;left:-10vw;animation-delay:-6s}
@keyframes blob{to{translate:4vw 3vw;scale:1.15}}
.hero .wrap{display:grid;grid-template-columns:1.08fr .92fr;gap:56px;align-items:center}
@media (max-width:940px){.hero .wrap{grid-template-columns:1fr}}
.hero h1{font-size:calc(clamp(48px,7.4vw,112px)*var(--scale));margin:22px 0 26px}
.line-mask{display:block;overflow:hidden;padding-bottom:.08em}
.hero h1.h1--long{font-size:calc(clamp(42px,6.2vw,92px)*var(--scale))}
.hero h1.h1--xlong{font-size:calc(clamp(38px,5.2vw,78px)*var(--scale))}
.hero__sub{max-width:520px;font-size:19px;color:var(--muted)}
.hero__cta{display:flex;flex-wrap:wrap;gap:12px;margin:34px 0 34px}
.trust{display:flex;flex-wrap:wrap;align-items:center;gap:16px;font-size:14px;color:var(--muted)}
.avatars{display:flex}
.avatars i{width:36px;height:36px;border-radius:50%;border:2px solid var(--bg);margin-left:-10px;display:grid;place-items:center;font-style:normal;font-size:13px;font-weight:700;color:var(--on-accent);background:var(--accent)}
.avatars i:first-child{margin-left:0}
.avatars i:nth-child(2){background:var(--accent2);color:var(--fg)}
.avatars i:nth-child(3){background:var(--fg);color:var(--bg)}
.trust b{color:var(--fg);font-size:16px}
.stars{color:#F5B301;letter-spacing:2px}

.visual{position:relative;justify-self:center;width:min(500px,100%);aspect-ratio:1}
.visual__panel{position:absolute;inset:6% 6% 6% 6%;border-radius:calc(var(--r)*2 + 8px);overflow:hidden;background:radial-gradient(circle at 30% 25%,var(--accent2),transparent 55%),radial-gradient(circle at 75% 80%,var(--accent),transparent 60%),var(--surface-2);box-shadow:var(--panel-shadow)}
.visual__panel::after{content:"";position:absolute;inset:0;background:var(--panel-overlay)}
.visual__ring{position:absolute;inset:16%;animation:spin 40s linear infinite}
.visual__ring circle{fill:none;stroke:var(--on-panel);stroke-opacity:.35;stroke-width:1;stroke-dasharray:3 7}
.visual__ring text{font:600 10px var(--body);letter-spacing:4px;fill:var(--on-panel);text-transform:uppercase;opacity:.75}
@keyframes spin{to{transform:rotate(360deg)}}
.visual__icon{position:absolute;inset:0;display:grid;place-items:center;color:var(--on-panel);z-index:1}
.visual__icon .ico{width:34%;height:34%;stroke-width:1.1;animation:float 6s ease-in-out infinite}
@keyframes float{50%{transform:translateY(-12px)}}
.chip{position:absolute;z-index:2;display:flex;align-items:center;gap:12px;padding:14px 18px;border-radius:calc(var(--r)*.6 + 8px);background:var(--card);color:var(--fg);box-shadow:0 24px 50px -24px rgba(0,0,0,.45);font-size:14px;line-height:1.3;animation:float 7s ease-in-out infinite}
.chip small{display:block;color:var(--muted);font-size:12px}
.chip b{font-size:16px}
.chip--1{left:-4%;top:12%}
.chip--2{right:-3%;top:44%;animation-delay:-2s}
.chip--3{left:4%;bottom:6%;animation-delay:-4s}
.dot{width:10px;height:10px;border-radius:50%;background:#22C55E;box-shadow:0 0 0 0 rgba(34,197,94,.6);animation:ping 2s infinite}
@keyframes ping{70%{box-shadow:0 0 0 10px rgba(34,197,94,0)}100%{box-shadow:0 0 0 0 rgba(34,197,94,0)}}
@media (max-width:520px){.chip{padding:10px 12px;font-size:12px}.chip b{font-size:14px}.chip--1{left:0}.chip--2{right:0}}

/* бегущая строка */
.marquee{overflow:hidden;white-space:nowrap;background:var(--fg);color:var(--bg);padding:20px 0}
.marquee__track{display:inline-flex;align-items:center;gap:40px;padding-right:40px;animation:marquee 34s linear infinite;font-family:var(--display);font-weight:var(--hw);text-transform:var(--ht);font-size:calc(clamp(22px,3vw,36px)*var(--scale))}
.marquee__track i{color:var(--accent);font-style:normal;font-size:.6em}
@keyframes marquee{to{transform:translateX(-50%)}}

/* о нас */
.about__grid{display:grid;grid-template-columns:1.25fr 1fr;gap:60px;align-items:start}
@media (max-width:900px){.about__grid{grid-template-columns:1fr}}
.about__text{font-family:var(--display);font-weight:var(--about-w);font-size:calc(clamp(26px,3.2vw,42px)*var(--scale));line-height:1.25;text-transform:none;letter-spacing:var(--hs)}
.hl{display:flex;gap:18px;padding:22px 0;border-bottom:1px solid var(--line)}
.hl:first-child{padding-top:0}
.hl__ico{width:48px;height:48px;border-radius:calc(var(--r)*.5 + 6px);display:grid;place-items:center;background:var(--soft-accent);color:var(--accent);flex:none}
.hl h3{font-family:var(--body);font-weight:700;font-size:18px;text-transform:none;letter-spacing:0;margin-bottom:4px}
.hl p{color:var(--muted);font-size:15px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:70px}
@media (max-width:820px){.stats{grid-template-columns:1fr 1fr}}
.stat{padding:28px 24px;border-radius:var(--r);background:var(--card);border:1px solid var(--line)}
.stat strong{display:block;font-family:var(--display);font-weight:var(--hw);font-size:calc(clamp(40px,4.6vw,64px)*var(--scale));line-height:1;color:var(--accent);margin-bottom:8px;font-variant-numeric:tabular-nums;white-space:nowrap}
.stat>span{color:var(--muted);font-size:15px}

/* услуги */
.tabs{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:28px}
.tabs button{padding:11px 20px;border-radius:999px;border:1px solid var(--line-strong);background:transparent;cursor:pointer;font-weight:600;font-size:15px;transition:background .35s,color .35s,border-color .35s}
.tabs button[aria-selected="true"]{background:var(--fg);color:var(--bg);border-color:var(--fg)}
.panel[hidden]{display:none}
.panel{animation:fade .6s var(--ease)}
@keyframes fade{from{opacity:0;transform:translateY(12px)}}
.svc{display:grid;grid-template-columns:1fr auto auto;gap:6px 24px;align-items:center;padding:22px 0;border-bottom:1px solid var(--line);transition:padding .5s var(--ease)}
.svc:hover{padding-left:12px}
.svc h3{font-family:var(--body);font-weight:700;font-size:19px;text-transform:none;letter-spacing:0}
.svc p{color:var(--muted);font-size:15px;margin-top:4px}
.svc__price{font-family:var(--display);font-weight:var(--hw);font-size:calc(24px*var(--scale));white-space:nowrap;font-variant-numeric:tabular-nums}
.svc__go{display:inline-flex;align-items:center;gap:8px;padding:10px 14px;border-radius:999px;background:var(--soft-accent);color:var(--accent-ink);font-size:14px;font-weight:600;white-space:nowrap;transition:background .3s,color .3s}
.svc__go:hover{background:#25D366;color:#fff}
.svc__go .wa-ico{width:16px;height:16px}
@media (max-width:640px){.svc{grid-template-columns:1fr auto}.svc__go{grid-column:1/-1;justify-self:start}}
.note{margin-top:22px;color:var(--muted);font-size:14px}

/* акция */
.promo{position:relative;overflow:hidden;border-radius:calc(var(--r)*1.5 + 6px);padding:clamp(32px,5vw,64px);background:var(--accent);color:var(--on-accent);display:grid;grid-template-columns:1.4fr auto;gap:30px;align-items:center}
@media (max-width:800px){.promo{grid-template-columns:1fr}}
.promo h2{font-size:calc(clamp(30px,4.2vw,58px)*var(--scale))}
.promo p{margin-top:12px;opacity:.85;max-width:560px}
.promo::after{content:"";position:absolute;right:-80px;top:-80px;width:260px;height:260px;border-radius:50%;border:40px solid currentColor;opacity:.08;animation:spin 30s linear infinite}
.promo .btn{background:var(--on-accent);color:var(--accent)}
.promo .btn::before{background:var(--fg)}
.promo .btn:hover{color:var(--bg)}

/* преимущества */
.adv{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
@media (max-width:900px){.adv{grid-template-columns:1fr 1fr}}
@media (max-width:560px){.adv{grid-template-columns:1fr}}
.adv__item{padding:30px 26px;border-radius:var(--r);background:var(--card);border:1px solid var(--line);transition:transform .5s var(--ease),box-shadow .5s var(--ease),border-color .4s}
.adv__item:hover{transform:translateY(-6px);box-shadow:0 30px 60px -36px rgba(0,0,0,.4);border-color:var(--accent)}
.adv__item .hl__ico{margin-bottom:20px;transition:transform .6s var(--ease)}
.adv__item:hover .hl__ico{transform:rotate(-10deg) scale(1.1)}
.adv__item h3{font-family:var(--body);font-weight:700;font-size:19px;text-transform:none;letter-spacing:0;margin-bottom:8px}
.adv__item p{color:var(--muted);font-size:15px}

/* этапы */
.steps{position:relative;display:grid;grid-template-columns:repeat(4,1fr);gap:20px;counter-reset:s}
@media (max-width:900px){.steps{grid-template-columns:1fr 1fr}}
@media (max-width:520px){.steps{grid-template-columns:1fr}}
.steps::before{content:"";position:absolute;left:0;right:0;top:27px;height:2px;background:var(--line);z-index:-1}
@media (max-width:900px){.steps::before{display:none}}
.step{counter-increment:s}
.step::before{content:counter(s);display:grid;place-items:center;width:56px;height:56px;border-radius:50%;background:var(--bg);border:2px solid var(--accent);color:var(--accent);font-family:var(--display);font-weight:var(--hw);font-size:22px;margin-bottom:20px;transition:background .4s,color .4s}
.step:hover::before{background:var(--accent);color:var(--on-accent)}
.step h3{font-family:var(--body);font-weight:700;font-size:19px;text-transform:none;letter-spacing:0;margin-bottom:6px}
.step p{color:var(--muted);font-size:15px}

/* команда */
.team{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px}
.member{border-radius:var(--r);overflow:hidden;background:var(--card);border:1px solid var(--line)}
.member__img{aspect-ratio:4/4.4;display:grid;place-items:center;font-family:var(--display);font-weight:var(--hw);font-size:72px;color:var(--on-panel);background:radial-gradient(circle at 30% 20%,var(--accent2),transparent 60%),radial-gradient(circle at 80% 90%,var(--accent),transparent 65%),var(--surface-2);transition:transform .9s var(--ease)}
.member:hover .member__img{transform:scale(1.04)}
.member__info{padding:20px 22px 24px}
.member h3{font-family:var(--body);font-weight:700;font-size:19px;text-transform:none;letter-spacing:0}
.member p{color:var(--muted);font-size:14px;margin-top:4px}

/* отзывы */
.reviews{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
@media (max-width:900px){.reviews{grid-template-columns:1fr}}
.review{display:flex;flex-direction:column;gap:18px;padding:30px 28px;border-radius:var(--r);background:var(--card);border:1px solid var(--line)}
.review p{font-size:17px;flex:1}
.review footer{display:flex;align-items:center;gap:12px;font-size:14px}
.review footer i{width:40px;height:40px;border-radius:50%;display:grid;place-items:center;font-style:normal;font-weight:700;background:var(--soft-accent);color:var(--accent-ink)}
.review footer small{display:block;color:var(--muted)}

/* галерея */
.gallery{display:grid;grid-template-columns:repeat(3,1fr);grid-auto-rows:220px;gap:14px}
@media (max-width:760px){.gallery{grid-template-columns:1fr 1fr;grid-auto-rows:170px}}
.gallery figure{position:relative;margin:0;border-radius:var(--r);overflow:hidden;display:flex;align-items:flex-end;padding:18px;color:#fff}
.gallery figure:nth-child(1){grid-row:span 2}
.gallery figure:nth-child(5){grid-column:span 2}
@media (max-width:760px){.gallery figure:nth-child(5){grid-column:auto}}
.gallery figure::before{content:"";position:absolute;inset:0;background:var(--g);transition:transform 1s var(--ease)}
.gallery figure:hover::before{transform:scale(1.07)}
.gallery figure::after{content:"";position:absolute;inset:0;background:linear-gradient(transparent 45%,rgba(0,0,0,.45))}
.gallery figcaption{position:relative;z-index:1;font-weight:600;font-size:15px}
.gallery .ico{position:absolute;z-index:1;top:18px;right:18px;opacity:.7;width:30px;height:30px}

/* вопросы */
.faq{max-width:900px}
.faq details{border-bottom:1px solid var(--line)}
.faq summary{list-style:none;cursor:pointer;display:flex;justify-content:space-between;gap:20px;padding:24px 0;font-weight:600;font-size:19px}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:"+";flex:none;width:32px;height:32px;border-radius:50%;display:grid;place-items:center;background:var(--soft-accent);color:var(--accent-ink);font-size:20px;line-height:1;transition:transform .45s var(--ease)}
.faq details[open] summary::after{transform:rotate(45deg)}
.faq details p{color:var(--muted);padding:0 50px 24px 0;animation:fade .5s var(--ease)}

/* запись */
.book{display:grid;grid-template-columns:1fr 1.05fr;gap:50px;align-items:start}
@media (max-width:900px){.book{grid-template-columns:1fr}}
.book__info h2{font-size:calc(clamp(36px,4.8vw,66px)*var(--scale));margin:14px 0 18px}
.book__info>p{color:var(--muted);margin-bottom:30px}
.contacts{display:grid;gap:14px}
.contact{display:flex;gap:14px;align-items:flex-start}
.contact .hl__ico{width:44px;height:44px}
.contact small{display:block;color:var(--muted);font-size:13px}
.contact b{font-weight:600}
.hours{width:100%;border-collapse:collapse;font-size:15px;margin-top:4px}
.hours td{padding:3px 0}
.hours td:last-child{text-align:right;font-variant-numeric:tabular-nums;font-weight:600}
.form{padding:clamp(24px,4vw,40px);border-radius:calc(var(--r) + 8px);background:var(--card);border:1px solid var(--line);box-shadow:0 40px 80px -50px rgba(0,0,0,.45);display:grid;gap:16px}
.form h3{font-size:calc(28px*var(--scale));margin-bottom:4px}
.form__row{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media (max-width:480px){.form__row{grid-template-columns:1fr}}
.field label{display:block;font-size:13px;font-weight:600;color:var(--muted);margin-bottom:6px}
.field input,.field select,.field textarea{width:100%;padding:14px 16px;border-radius:calc(var(--r)*.5 + 6px);border:1px solid var(--line-strong);background:var(--bg);transition:border-color .3s,box-shadow .3s}
.field textarea{min-height:90px;resize:vertical}
.field input:focus,.field select:focus,.field textarea:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 4px var(--soft-accent)}
.form .btn{width:100%;padding:18px}
.form__hint{font-size:13px;color:var(--muted);text-align:center}
.preview{font-size:13px;color:var(--muted);background:var(--soft-accent);border-radius:calc(var(--r)*.5 + 6px);padding:12px 14px;white-space:pre-line}

/* карта */
.mapbox{position:relative;margin-top:28px;aspect-ratio:16/9;border-radius:var(--r);overflow:hidden;background:var(--surface-2)}
.mapbox>svg{width:100%;height:100%;display:block}
.mapbox .road{stroke:var(--bg);stroke-width:12;fill:none;stroke-linecap:round}
.mapbox .road--s{stroke-width:6}
.mapbox .river{stroke:var(--accent2);stroke-opacity:.5;stroke-width:16;fill:none}
.mapbox .pin{color:var(--accent)}
.mapbox .pulse{fill:var(--accent);opacity:.3;transform-box:fill-box;transform-origin:center;animation:pulse 2.2s ease-out infinite}
@keyframes pulse{from{transform:scale(.3);opacity:.5}to{transform:scale(2);opacity:0}}
.mapbox .btn{position:absolute;right:14px;bottom:14px}

footer.site{padding:60px 0 100px;border-top:1px solid var(--line);font-size:14px;color:var(--muted)}
footer.site .wrap{display:flex;flex-wrap:wrap;justify-content:space-between;gap:20px}
footer.site .logo{color:var(--fg)}

/* плавающая кнопка WhatsApp */
.wa-float{position:fixed;right:calc(18px + env(safe-area-inset-right,0px));bottom:calc(18px + env(safe-area-inset-bottom,0px));z-index:60;display:flex;align-items:center;gap:10px;padding:14px 18px 14px 14px;border-radius:999px;background:#25D366;color:#fff;font-weight:700;font-size:15px;box-shadow:0 16px 36px -12px rgba(18,140,75,.7);transition:transform .4s var(--ease)}
.wa-float:hover{transform:translateY(-3px) scale(1.03)}
.wa-float .wa-ico{width:28px;height:28px}
.wa-float::before{content:"";position:absolute;inset:0;border-radius:inherit;box-shadow:0 0 0 0 rgba(37,211,102,.55);animation:waping 2.4s infinite}
@keyframes waping{70%{box-shadow:0 0 0 16px rgba(37,211,102,0)}100%{box-shadow:0 0 0 0 rgba(37,211,102,0)}}
@media (max-width:600px){.wa-float span{display:none}.wa-float{padding:14px}}
.tag-note{position:fixed;left:calc(14px + env(safe-area-inset-left,0px));bottom:calc(14px + env(safe-area-inset-bottom,0px));z-index:59;padding:7px 12px;border-radius:999px;background:rgba(0,0,0,.72);color:#fff;font:500 12px/1.3 system-ui,sans-serif}

/* анимации появления: текст виден сразу, блоки только слегка сдвинуты */
.js [data-split] .char{display:inline-block;transform:translateY(105%);transition:transform 1s var(--ease);transition-delay:calc(var(--i)*30ms + .1s)}
.js.is-ready [data-split] .char{transform:none}
.split-word{display:inline-block;white-space:nowrap}
.js .reveal{transform:translateY(26px);opacity:.001;transition:opacity .9s var(--ease),transform 1.1s var(--ease);transition-delay:var(--d,0s)}
.js .reveal.is-in{opacity:1;transform:none}
.js.rest .reveal{opacity:1}
.js [data-words] .word{opacity:.3;transition:opacity .4s}
.js [data-words] .word.is-lit{opacity:1}
.magnetic,.tilt{will-change:transform}
.tilt{transition:transform .5s var(--ease),box-shadow .5s var(--ease),border-color .4s,opacity .9s var(--ease)}

/* особенности стилей */
.skin-luxe .eyebrow{color:var(--accent)}
.skin-luxe .stat,.skin-luxe .adv__item,.skin-luxe .review,.skin-luxe .member,.skin-luxe .form{background:transparent}
.skin-bold .marquee{background:var(--accent);color:var(--on-accent)}
.skin-bold .marquee__track i{color:var(--on-accent)}
.skin-soft .btn{box-shadow:0 6px 0 color-mix(in srgb,var(--accent) 60%,#000)}
.skin-soft .btn--ghost{box-shadow:inset 0 0 0 2px var(--line-strong)}
.skin-industrial .marquee{background:repeating-linear-gradient(-45deg,var(--accent) 0 22px,color-mix(in srgb,var(--accent) 85%,#000) 22px 44px);color:var(--on-accent)}
.skin-industrial .marquee__track i{color:var(--on-accent)}
.skin-industrial .eyebrow::before{height:6px;width:6px;background:var(--accent)}

@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}
  .js .reveal,.js [data-split] .char{opacity:1;transform:none}
  .js [data-words] .word{opacity:1}
}
"""

JS = r"""
(() => {
  const root = document.documentElement;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fine = matchMedia('(hover: hover) and (pointer: fine)').matches;
  root.classList.add('js');

  // Заголовок по буквам (слова не рвутся при переносе)
  document.querySelectorAll('[data-split]').forEach((el) => {
    const text = el.textContent; el.textContent = ''; el.setAttribute('aria-label', text);
    let i = 0;
    text.split(/(\s+)/).forEach((part) => {
      if (!part) return;
      if (/^\s+$/.test(part)) return el.appendChild(document.createTextNode(' '));
      const w = document.createElement('span'); w.className = 'split-word'; w.setAttribute('aria-hidden', 'true');
      [...part].forEach((ch) => { const s = document.createElement('span'); s.className = 'char'; s.style.setProperty('--i', i++); s.textContent = ch; w.appendChild(s); });
      el.appendChild(w);
    });
  });

  // Абзац, который «загорается» по словам
  const words = [];
  document.querySelectorAll('[data-words]').forEach((el) => {
    const walk = (node) => [...node.childNodes].forEach((c) => {
      if (c.nodeType !== 3) return walk(c);
      const f = document.createDocumentFragment();
      c.textContent.split(/(\s+)/).forEach((p) => {
        if (!p) return;
        if (/^\s+$/.test(p)) return f.appendChild(document.createTextNode(p));
        const s = document.createElement('span'); s.className = 'word'; s.textContent = p; f.appendChild(s); words.push(s);
      });
      c.replaceWith(f);
    });
    walk(el);
  });

  const ready = () => requestAnimationFrame(() => root.classList.add('is-ready'));
  (document.fonts ? Promise.race([document.fonts.ready, new Promise((r) => setTimeout(r, 1000))]) : Promise.resolve()).then(ready);
  // Если наблюдатель не сработает (превью, печать) — через 2.5 с показываем всё
  setTimeout(() => root.classList.add('rest'), 2500);

  let lenis = null;
  if (!reduce && window.Lenis) {
    lenis = new Lenis({ lerp: 0.09, smoothWheel: true });
    const raf = (t) => { lenis.raf(t); requestAnimationFrame(raf); };
    requestAnimationFrame(raf);
  }
  document.querySelectorAll('a[href^="#"]').forEach((a) => a.addEventListener('click', (ev) => {
    const id = a.getAttribute('href'); const t = id.length > 1 && document.querySelector(id);
    if (!t) return; ev.preventDefault();
    lenis ? lenis.scrollTo(t, { offset: -70, duration: 1.3 }) : t.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth' });
  }));

  const io = new IntersectionObserver((es) => es.forEach((en) => { if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); } }), { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
  document.querySelectorAll('.reveal').forEach((el) => io.observe(el));

  const fmt = (n, d) => n.toFixed(d).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  const cio = new IntersectionObserver((es) => es.forEach((en) => {
    if (!en.isIntersecting) return;
    const el = en.target, to = parseFloat(el.dataset.count), d = parseInt(el.dataset.decimals || '0', 10), dur = reduce ? 0 : 1800, t0 = performance.now();
    const tick = (now) => { const p = dur ? Math.min((now - t0) / dur, 1) : 1; el.textContent = fmt(to * (1 - Math.pow(1 - p, 4)), d); if (p < 1) requestAnimationFrame(tick); };
    requestAnimationFrame(tick); cio.unobserve(el);
  }), { threshold: 0.5 });
  document.querySelectorAll('[data-count]').forEach((el) => cio.observe(el));

  // Вкладки услуг
  document.querySelectorAll('[data-tabs]').forEach((box) => {
    const bs = box.querySelectorAll('[data-tab]'), ps = box.querySelectorAll('[data-panel]');
    bs.forEach((b) => b.addEventListener('click', () => {
      bs.forEach((x) => x.setAttribute('aria-selected', x === b));
      ps.forEach((p) => { p.hidden = p.dataset.panel !== b.dataset.tab; });
    }));
  });

  // Форма → сообщение в WhatsApp
  const form = document.getElementById('book-form');
  if (form) {
    const send = document.getElementById('f-send'), preview = document.getElementById('f-preview');
    const dateEl = document.getElementById('f-date');
    const today = new Date(); const iso = (d) => d.toISOString().slice(0, 10);
    dateEl.min = iso(today);
    const human = (v) => { if (!v) return ''; const [y, m, d] = v.split('-'); return `${d}.${m}.${y}`; };
    const build = () => {
      const v = (id) => document.getElementById(id).value.trim();
      const lines = [form.dataset.hello + ' в ' + form.dataset.name + '.'];
      if (v('f-service')) lines.push(form.dataset.svc + ': ' + v('f-service'));
      const when = [human(v('f-date')), v('f-time')].filter(Boolean).join(', ');
      if (when) lines.push('Когда: ' + when);
      if (v('f-name')) lines.push('Имя: ' + v('f-name'));
      if (v('f-comment')) lines.push('Комментарий: ' + v('f-comment'));
      const text = lines.join('\n');
      send.href = 'https://wa.me/' + form.dataset.phone + '?text=' + encodeURIComponent(text);
      preview.textContent = text;
    };
    form.addEventListener('input', build); form.addEventListener('change', build);
    form.addEventListener('submit', (ev) => ev.preventDefault());
    // Кнопки «Записаться» у услуг подставляют услугу в форму
    document.querySelectorAll('[data-pick]').forEach((a) => a.addEventListener('click', () => { document.getElementById('f-service').value = a.dataset.pick; build(); }));
    build();
  }

  // Шапка и параллакс
  const nav = document.querySelector('.nav'); const par = [...document.querySelectorAll('[data-speed]')]; let last = 0;
  const onScroll = () => {
    const y = window.scrollY;
    nav.classList.toggle('is-scrolled', y > 20); nav.classList.toggle('is-hidden', y > last && y > 600); last = y;
    if (!reduce && innerWidth > 900) par.forEach((el) => { el.style.translate = `0 ${y * parseFloat(el.dataset.speed)}px`; });
    const vh = innerHeight; words.forEach((w) => w.classList.toggle('is-lit', w.getBoundingClientRect().top < vh * 0.8));
  };
  lenis ? lenis.on('scroll', onScroll) : addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  if (!fine || reduce) return;
  document.querySelectorAll('.magnetic').forEach((b) => {
    b.addEventListener('mousemove', (ev) => { const r = b.getBoundingClientRect(); b.style.transform = `translate(${(ev.clientX - r.left - r.width / 2) * .22}px, ${(ev.clientY - r.top - r.height / 2) * .3}px)`; });
    b.addEventListener('mouseleave', () => { b.style.transform = ''; });
  });
  document.querySelectorAll('.tilt').forEach((c) => {
    c.addEventListener('mousemove', (ev) => { const r = c.getBoundingClientRect(); const px = (ev.clientX - r.left) / r.width - .5, py = (ev.clientY - r.top) / r.height - .5; c.style.transform = `perspective(900px) rotateY(${px * 6}deg) rotateX(${-py * 6}deg) translateY(-4px)`; });
    c.addEventListener('mouseleave', () => { c.style.transform = ''; });
  });
  // Карточки на первом экране слегка следуют за мышью
  const vis = document.querySelector('.visual');
  if (vis) addEventListener('mousemove', (ev) => {
    const x = ev.clientX / innerWidth - .5, y = ev.clientY / innerHeight - .5;
    vis.querySelectorAll('.chip').forEach((c, i) => { c.style.translate = `${x * (14 + i * 8)}px ${y * (14 + i * 8)}px`; });
  });
})();
"""


# ---------------------------------------------------------------- сборка страницы
def tokens(site):
    bg, fg, accent, accent2 = site['pal']
    skin = SKINS[site['skin']]
    dark = lum(bg) < 0.2
    on_accent = '#111111' if lum(accent) > 0.38 else '#FFFFFF'
    # контрастный цвет для текста акцента на светлом фоне
    accent_ink = accent if (dark or lum(accent) < 0.3) else mix(accent, 55, '#000')
    panel_dark = dark or site['skin'] in ('luxe', 'industrial')
    return {
        '--bg': bg, '--fg': fg, '--accent': accent, '--accent2': accent2,
        '--on-accent': on_accent,
        '--accent-ink': accent_ink,
        '--muted': mix(fg, 66, bg),
        '--line': mix(fg, 13, 'transparent'),
        '--line-strong': mix(fg, 26, 'transparent'),
        '--card': mix(fg, 6 if dark else 0, '#FFFFFF') if not dark else mix(fg, 6, bg),
        '--surface-2': mix(fg, 10, bg),
        '--soft-accent': mix(accent, 16, 'transparent'),
        '--on-panel': '#FFFFFF' if panel_dark or lum(accent) < 0.25 else fg,
        '--panel-shadow': '0 40px 80px -40px rgba(0,0,0,.55)',
        '--panel-overlay': 'repeating-linear-gradient(-45deg,rgba(255,255,255,.05) 0 2px,transparent 2px 14px)' if site['skin'] == 'industrial' else 'none',
        '--blob-o': '.22' if dark else '.35',
        '--display': f"'{site.get('display', skin['display'])}', Georgia, sans-serif",
        '--body': f"'{site.get('body', skin['body'])}', system-ui, sans-serif",
        '--hw': str(site.get('hw', skin['hw'])), '--ht': skin['ht'], '--hs': skin['hs'],
        '--about-w': '500' if skin['hw'] >= 700 else str(skin['hw']),
        '--r': skin['r'], '--rb': '999px' if site['skin'] in ('bold', 'soft', 'clean', 'editorial') else skin['r'],
        '--scale': str(site.get('scale', skin['scale'])),
        '--em-style': 'italic' if site['skin'] in ('editorial', 'luxe') else 'normal',
        '--ease': 'cubic-bezier(.22,1,.36,1)',
    }


def gradient(site, i):
    bg, fg, accent, accent2 = site['pal']
    angles = [135, 160, 200, 120, 210, 150]
    pairs = [(accent, accent2), (accent2, fg), (accent, fg), (accent2, accent), (fg, accent), (accent, accent2)]
    a, b = pairs[i % 6]
    return f'linear-gradient({angles[i % 6]}deg,{a},{b})'


def render(site, artifact=False):
    m = MODES[site['mode']]
    phone = site.get('wa', '77000000000')
    phone_h = site.get('phone', '+7 700 000 00 00')
    name = site['name']
    skin = SKINS[site['skin']]
    t = tokens(site)
    root_css = ':root{' + ';'.join(f'{k}:{v}' for k, v in t.items()) + '}'
    fams = [site.get('display', skin['display']), site.get('body', skin['body'])]
    wa_hello = wa_link(phone, f"{m['hello']} в {name}.")

    # ---------- первый экран
    lines = []
    for i, ln in enumerate(site['h1']):
        inner = f'<em data-split>{e(ln)}</em>' if i == site.get('em', 1) else f'<span data-split>{e(ln)}</span>'
        lines.append(f'<span class="line-mask">{inner}</span>')
    # Длинные заголовки уменьшаем, чтобы кнопка записи оставалась на первом экране
    total = sum(len(x) for x in site['h1'])
    h1_cls = ' class="h1--xlong"' if total > 34 else (' class="h1--long"' if total > 26 or max(len(x) for x in site['h1']) > 14 else '')
    initials = site.get('avatars', 'АМД')
    hero = f'''
<section class="hero" id="top">
  <div class="hero__bg" aria-hidden="true"><span></span><span></span></div>
  <div class="wrap">
    <div>
      <p class="eyebrow reveal">{e(site['niche'])} · Астана</p>
      <h1{h1_cls}>{''.join(lines)}</h1>
      <p class="hero__sub reveal" style="--d:.45s">{e(site['sub'])}</p>
      <div class="hero__cta reveal" style="--d:.55s">
        <a class="btn btn--wa magnetic" href="{e(wa_hello)}" target="_blank" rel="noopener">{WA_ICON}{e(m['cta'])} в WhatsApp</a>
        <a class="btn btn--ghost magnetic" href="#services">Услуги и цены</a>
      </div>
      <div class="trust reveal" style="--d:.65s">
        <div class="avatars" aria-hidden="true"><i>{initials[0]}</i><i>{initials[1]}</i><i>{initials[2]}</i></div>
        <div><b>{site['rating']}</b> <span class="stars">★★★★★</span><br>{site['reviews_n']} отзывов в 2ГИС</div>
      </div>
    </div>
    <div class="visual reveal" style="--d:.25s" data-speed="-0.05" aria-hidden="true">
      <div class="visual__panel">
        <svg class="visual__ring" viewBox="0 0 200 200"><defs><path id="ring" d="M100 100 m-82 0 a82 82 0 1 1 164 0 a82 82 0 1 1 -164 0"/></defs><circle cx="100" cy="100" r="94"/><text><textPath href="#ring">{e(site.get('ring', name + ' · ' + site['niche'] + ' · Астана · '))}</textPath></text></svg>
        <div class="visual__icon">{icon(site['icon'])}</div>
      </div>
      <div class="chip chip--1"><span class="dot"></span><div><small>{e(m['live'])}</small><b>{e(site['live'])}</b></div></div>
      <div class="chip chip--2"><div class="hl__ico" style="width:40px;height:40px">{icon('card')}</div><div><small>Цены</small><b>{e(site['price_from'])}</b></div></div>
      <div class="chip chip--3"><div class="hl__ico" style="width:40px;height:40px">{icon(site.get('chip_icon', 'award'))}</div><div><small>{e(site['badge'][0])}</small><b>{e(site['badge'][1])}</b></div></div>
    </div>
  </div>
</section>'''

    words = site.get('marquee') or [s.split('|')[0] for _, items in site['services'] for s in items][:6]
    track = ''.join(f'<span>{e(w)}</span><i>✦</i>' for w in words)
    marquee = f'<div class="marquee" aria-hidden="true"><div class="marquee__track">{track}{track}</div></div>'

    # ---------- о нас
    hls = ''.join(f'<div class="hl reveal" style="--d:{i * .08:.2f}s"><div class="hl__ico">{icon(ic)}</div><div><h3>{e(ti)}</h3><p>{e(tx)}</p></div></div>'
                  for i, (ic, ti, tx) in enumerate(site['hl']))
    stats = ''
    for i, st in enumerate(site['stats']):
        num, suf, label = st
        dec = 1 if isinstance(num, float) else 0
        stats += f'<div class="stat reveal" style="--d:{i * .08:.2f}s"><strong><span data-count="{num}" data-decimals="{dec}">{num}</span>{e(suf)}</strong><span>{e(label)}</span></div>'
    about = f'''
<section class="sec" id="about">
  <div class="wrap">
    <div class="about__grid">
      <div>
        <p class="eyebrow reveal">О нас</p>
        <p class="about__text" data-words style="margin-top:22px">{e(site['about'])}</p>
      </div>
      <div>{hls}</div>
    </div>
    <div class="stats">{stats}</div>
  </div>
</section>'''

    # ---------- услуги
    tabs, panels = '', ''
    all_services = []
    for ci, (cat, items) in enumerate(site['services']):
        tabs += f'<button type="button" data-tab="c{ci}" aria-selected="{"true" if ci == 0 else "false"}">{e(cat)}</button>'
        rows = ''
        for it in items:
            nm, desc, price = (it.split('|') + ['', ''])[:3]
            all_services.append(nm)
            link = wa_link(phone, f"{m['hello']} в {name}. {m['per']}{nm}")
            rows += (f'<div class="svc"><div><h3>{e(nm)}</h3>{f"<p>{e(desc)}</p>" if desc else ""}</div>'
                     f'<div class="svc__price">{e(price)}</div>'
                     f'<a class="svc__go" href="{e(link)}" target="_blank" rel="noopener" data-pick="{e(nm)}">{WA_ICON}{e(m["cta"])}</a></div>')
        panels += f'<div class="panel" data-panel="c{ci}"{"" if ci == 0 else " hidden"}>{rows}</div>'
    services = f'''
<section class="sec" id="services" style="padding-top:40px">
  <div class="wrap" data-tabs>
    <div class="sec-head">
      <div><p class="eyebrow reveal">Услуги и цены</p><h2 class="reveal">{site.get('svc_title', 'Что мы <em>делаем</em>')}</h2></div>
      <p class="reveal">{e(site.get('svc_note', 'Нажмите «' + m['cta'] + '» напротив услуги — откроется WhatsApp с готовым сообщением.'))}</p>
    </div>
    <div class="tabs reveal" role="tablist">{tabs}</div>
    {panels}
    <p class="note">{e(site.get('price_note', 'Цены указаны ориентировочно. Точную стоимость подтвердит администратор.'))}</p>
  </div>
</section>'''

    promo_t, promo_x = site['promo']
    promo = f'''
<section class="sec" style="padding:20px 0 40px">
  <div class="wrap"><div class="promo reveal">
    <div><h2>{e(promo_t)}</h2><p>{e(promo_x)}</p></div>
    <a class="btn magnetic" href="{e(wa_link(phone, f"{m['hello']} в {name}. Хочу воспользоваться акцией: {promo_t}"))}" target="_blank" rel="noopener">{WA_ICON}Получить в WhatsApp</a>
  </div></div>
</section>'''

    adv = ''.join(f'<article class="adv__item tilt reveal" style="--d:{(i % 3) * .08:.2f}s"><div class="hl__ico">{icon(ic)}</div><h3>{e(ti)}</h3><p>{e(tx)}</p></article>'
                  for i, (ic, ti, tx) in enumerate(site['adv']))
    advs = f'''
<section class="sec" id="why">
  <div class="wrap">
    <div class="sec-head"><div><p class="eyebrow reveal">Почему мы</p><h2 class="reveal">{site.get('adv_title', 'Почему выбирают <em>нас</em>')}</h2></div></div>
    <div class="adv">{adv}</div>
  </div>
</section>'''

    steps_data = site.get('steps') or DEFAULT_STEPS[site['mode']]
    steps = ''.join(f'<div class="step reveal" style="--d:{i * .1:.2f}s"><h3>{e(ti)}</h3><p>{e(tx)}</p></div>' for i, (ti, tx) in enumerate(steps_data))
    stepsec = f'''
<section class="sec" style="padding-top:20px">
  <div class="wrap">
    <div class="sec-head"><div><p class="eyebrow reveal">Как это работает</p><h2 class="reveal">Четыре <em>простых</em> шага</h2></div></div>
    <div class="steps">{steps}</div>
  </div>
</section>'''

    team = ''
    if site.get('team'):
        cards = ''.join(f'<article class="member tilt reveal" style="--d:{i * .08:.2f}s"><div class="member__img">{e("".join(w[0] for w in nm.split()[:2]))}</div><div class="member__info"><h3>{e(nm)}</h3><p>{e(role)}</p></div></article>'
                        for i, (nm, role) in enumerate(site['team']))
        team = f'''
<section class="sec" id="team" style="padding-top:20px">
  <div class="wrap">
    <div class="sec-head"><div><p class="eyebrow reveal">Команда</p><h2 class="reveal">{site.get('team_title', 'Люди, которым <em>доверяют</em>')}</h2></div><p class="reveal">Фото команды — из Instagram компании.</p></div>
    <div class="team">{cards}</div>
  </div>
</section>'''

    caps = site.get('gallery') or all_services[:6]
    gal_icons = site.get('gallery_icons') or [site['icon'], 'sparkle', 'heart', 'star', 'camera', site['icon']]
    figs = ''.join(f'<figure class="reveal" style="--g:{gradient(site, i)};--d:{(i % 3) * .08:.2f}s">{icon(gal_icons[i % len(gal_icons)])}<figcaption>{e(c)}</figcaption></figure>' for i, c in enumerate(caps[:6]))
    gallery = f'''
<section class="sec" id="gallery" style="padding-top:20px">
  <div class="wrap">
    <div class="sec-head"><div><p class="eyebrow reveal">Галерея</p><h2 class="reveal">{site.get('gallery_title', 'Наши <em>работы</em>')}</h2></div><p class="reveal">Сюда встанут реальные фото из Instagram {e(site.get('insta', ''))}.</p></div>
    <div class="gallery">{figs}</div>
  </div>
</section>'''

    revs = ''.join(f'<article class="review reveal" style="--d:{i * .08:.2f}s"><span class="stars">★★★★★</span><p>«{e(tx)}»</p><footer><i>{e(nm[0])}</i><div><b>{e(nm)}</b><small>{e(sv)}</small></div></footer></article>'
                   for i, (nm, sv, tx) in enumerate(site['reviews']))
    reviews = f'''
<section class="sec" id="reviews" style="padding-top:20px">
  <div class="wrap">
    <div class="sec-head"><div><p class="eyebrow reveal">Отзывы</p><h2 class="reveal">Что говорят <em>гости</em></h2></div><p class="reveal"><b style="color:var(--fg)">{site['rating']}</b> <span class="stars">★★★★★</span> · {site['reviews_n']} отзывов в 2ГИС. Ниже — примеры, замените на реальные.</p></div>
    <div class="reviews">{revs}</div>
  </div>
</section>'''

    faqs = ''.join(f'<details class="reveal"><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in site['faq'] + COMMON_FAQ)
    faq = f'''
<section class="sec" id="faq" style="padding-top:20px">
  <div class="wrap">
    <div class="sec-head"><div><p class="eyebrow reveal">Вопросы</p><h2 class="reveal">Частые <em>вопросы</em></h2></div></div>
    <div class="faq">{faqs}</div>
  </div>
</section>'''

    # ---------- запись + контакты
    opts = ''.join(f'<option>{e(s)}</option>' for s in all_services)
    times = site.get('times') or ['10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00']
    if site['mode'] == 'order':
        times = ['Как можно скорее'] + times
    topts = ''.join(f'<option>{e(x)}</option>' for x in times)
    hours = ''.join(f'<tr><td>{e(d)}</td><td>{e(h)}</td></tr>' for d, h in site['hours'])
    book = f'''
<section class="sec" id="contacts" style="padding-top:20px">
  <div class="wrap book">
    <div class="book__info">
      <p class="eyebrow reveal">Контакты</p>
      <h2 class="reveal">{site.get('book_title', 'Ждём <em>вас</em>')}</h2>
      <p class="reveal">{e(site.get('book_text', 'Заполните форму — она сразу откроет WhatsApp с готовым сообщением. Отвечаем в течение 15 минут в рабочее время.'))}</p>
      <div class="contacts reveal">
        <div class="contact"><div class="hl__ico">{icon('pin')}</div><div><small>Адрес</small><b>{e(site['addr'])}</b></div></div>
        <div class="contact"><div class="hl__ico">{icon('clock')}</div><div style="flex:1"><small>Часы работы</small><table class="hours">{hours}</table></div></div>
        <div class="contact"><div class="hl__ico">{icon('chat')}</div><div><small>Телефон и WhatsApp</small><b>{e(phone_h)}</b></div></div>
        <div class="contact"><div class="hl__ico">{icon('camera')}</div><div><small>Instagram</small><b>{e(site.get('insta', '@instagram'))}</b></div></div>
      </div>
      <div class="mapbox reveal" aria-label="Схема проезда">
        <svg viewBox="0 0 320 180" aria-hidden="true">
          <path class="river" d="M-10 30 C80 60 200 0 330 40"/>
          <path class="road" d="M-10 110 L330 90"/><path class="road" d="M120 -10 L150 190"/><path class="road road--s" d="M240 -10 L250 190"/><path class="road road--s" d="M-10 160 L330 150"/>
          <circle class="pulse" cx="192" cy="96" r="18"/>
          <g class="pin"><path d="M192 66c11 0 18 8 18 17 0 13-18 29-18 29s-18-16-18-29c0-9 7-17 18-17z" fill="currentColor"/><circle cx="192" cy="83" r="6" fill="#fff"/></g>
        </svg>
        <a class="btn btn--small" href="{e(site.get('gis', 'https://2gis.kz/astana'))}" target="_blank" rel="noopener">{icon('map')}Открыть в 2ГИС</a>
      </div>
    </div>
    <form class="form reveal" id="book-form" data-phone="{phone}" data-name="{e(name)}" data-hello="{e(m['hello'])}" data-svc="{e(m['svc'])}" style="--d:.1s">
      <h3>{e(m['form'])}</h3>
      <div class="field"><label for="f-name">Ваше имя</label><input id="f-name" type="text" placeholder="Например, Айгерим" autocomplete="name"></div>
      <div class="field"><label for="f-service">{e(m['svc'])}</label><select id="f-service"><option value="">Выберите из списка</option>{opts}</select></div>
      <div class="form__row">
        <div class="field"><label for="f-date">{e(m['date'])}</label><input id="f-date" type="date"></div>
        <div class="field"><label for="f-time">Время</label><select id="f-time"><option value="">Любое</option>{topts}</select></div>
      </div>
      <div class="field"><label for="f-comment">Комментарий</label><textarea id="f-comment" placeholder="{e(site.get('comment_ph', 'Пожелания, вопросы'))}"></textarea></div>
      <div class="preview" id="f-preview" aria-live="polite"></div>
      <a class="btn btn--wa" id="f-send" href="{e(wa_hello)}" target="_blank" rel="noopener">{WA_ICON}{e(m['send'])}</a>
      <p class="form__hint">Откроется личный чат WhatsApp с готовым текстом — останется нажать «Отправить».</p>
    </form>
  </div>
</section>'''

    nav = f'''
<header class="nav"><div class="wrap">
  <a href="#top" class="logo"><span class="logo__mark">{icon(site['icon'])}</span>{e(name)}</a>
  <nav class="nav__links"><a href="#about">О нас</a><a href="#services">Цены</a><a href="#reviews">Отзывы</a><a href="#contacts">Контакты</a></nav>
  <a class="btn btn--wa btn--small magnetic" href="{e(wa_hello)}" target="_blank" rel="noopener">{WA_ICON}<span>{e(m['cta'])}</span></a>
</div></header>'''

    footer = f'''
<footer class="site"><div class="wrap">
  <a href="#top" class="logo"><span class="logo__mark">{icon(site['icon'])}</span>{e(name)}</a>
  <div>{e(site['addr'])}<br>{e(phone_h)} · {e(site.get('insta', ''))}</div>
  <div>Шаблон сайта. Название и данные вымышленные.</div>
</div></footer>
<a class="wa-float" href="{e(wa_hello)}" target="_blank" rel="noopener" aria-label="Написать в WhatsApp">{WA_ICON}<span>Написать нам</span></a>'''

    body = (nav + '<main>' + hero + marquee + about + services + promo + advs + stepsec + team + gallery
            + reviews + faq + book + '</main>' + footer)
    title = site.get('title', f"{name} — {site['niche'].lower()}")
    if artifact:
        title = site.get('art_title', f"{site['niche']} {name}")
    head = (f'<title>{e(title)}</title>\n'
            f'<meta name="description" content="{e(site["sub"])}">\n'
            '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            f'<link href="{fonts_url(fams)}" rel="stylesheet">\n'
            f'<style>{root_css}{CSS}</style>\n')
    scripts = '<script src="https://unpkg.com/lenis@1.1.13/dist/lenis.min.js"></script>\n<script>' + JS + '</script>'
    body = f'<div class="skin-{site["skin"]}">{body}</div>'
    if artifact:
        return head + body + '\n' + scripts + '\n'
    return ('<!doctype html>\n<html lang="ru">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            + head + '</head>\n<body>\n' + body + '\n' + scripts + '\n</body>\n</html>\n')
