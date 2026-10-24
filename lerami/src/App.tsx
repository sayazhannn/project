import { FormEvent, useState } from 'react'
import { ArrowUpRight, Instagram, MapPin, MessageCircle, Phone, Plus } from 'lucide-react'
import {
  business as b,
  contacts,
  faq,
  form as f,
  gallery,
  hero,
  process,
  services,
} from './content'
import { useReveal } from './useReveal'

const waBase = `https://wa.me/${b.whatsapp}`
const wa = (text: string) => `${waBase}?text=${encodeURIComponent(text)}`
const telHref = `tel:+${b.whatsapp}`

function WaButton({ label, className = '' }: { label: string; className?: string }) {
  return (
    <a
      className={`btn btn-primary ${className}`}
      href={wa('Здравствуйте! Хочу записаться в Lerami.')}
      target="_blank"
      rel="noopener"
    >
      <MessageCircle size={18} strokeWidth={1.5} aria-hidden="true" />
      {label}
    </a>
  )
}

function Header() {
  return (
    <header className="sticky top-0 z-30 border-b border-ink/10 bg-bg">
      <div className="wrap flex h-16 items-center justify-between px-5 md:px-10">
        <a href="#top" className="font-serif text-2xl font-semibold tracking-wide">
          {b.name}
        </a>
        <nav aria-label="Основная" className="hidden gap-8 text-sm font-medium md:flex">
          <a href="#services" className="hover:text-accent">Услуги</a>
          <a href="#process" className="hover:text-accent">Как проходит</a>
          <a href="#faq" className="hover:text-accent">Вопросы</a>
          <a href="#contacts" className="hover:text-accent">Контакты</a>
        </nav>
        <a
          className="btn btn-primary !min-h-[44px] !px-4"
          href={wa('Здравствуйте! Хочу записаться в Lerami.')}
          target="_blank"
          rel="noopener"
        >
          <MessageCircle size={18} strokeWidth={1.5} aria-hidden="true" />
          <span className="hidden sm:inline">Записаться</span>
          <span className="sm:hidden">WhatsApp</span>
        </a>
      </div>
    </header>
  )
}

/** Композиция из форм палитры вместо фото: арки и круг, как в журнальной вёрстке. */
function HeroArt() {
  return (
    <svg
      viewBox="0 0 400 500"
      role="img"
      aria-label="Абстрактная композиция из арок и круга в тёплых тонах"
      className="h-full w-full"
    >
      <rect width="400" height="500" fill="#E9DFD3" />
      <path d="M40 500V230a110 110 0 0 1 220 0V500Z" fill="#9A4A3A" />
      <path d="M150 500V300a90 90 0 0 1 180 0V500Z" fill="#231A17" />
      <circle cx="300" cy="110" r="52" fill="#F6F0E8" />
      <path d="M0 440h400" stroke="#231A17" strokeOpacity=".25" />
    </svg>
  )
}

function Hero() {
  return (
    <section id="top" className="section !pt-10 md:!pt-16">
      <div className="wrap grid items-end gap-10 md:grid-cols-12 md:gap-8">
        <div className="md:col-span-7">
          <p className="eyebrow reveal">{hero.eyebrow}</p>
          <h1 className="reveal mt-5 font-serif text-[2.75rem] font-medium leading-[0.98] md:text-7xl lg:text-[6rem]">
            {hero.title}
          </h1>
          <p className="reveal mt-6 max-w-md text-base leading-relaxed text-mute md:text-lg">{hero.lead}</p>
          <div className="reveal mt-8 flex flex-col gap-3 sm:flex-row">
            <WaButton label={hero.cta} />
            <a className="btn btn-ghost" href="#services">{hero.secondary}</a>
          </div>
        </div>
        <div className="reveal aspect-[4/5] w-full max-w-sm self-stretch md:col-span-5 md:max-w-none md:aspect-auto md:min-h-[520px]">
          <HeroArt />
        </div>
      </div>
    </section>
  )
}

function Services() {
  return (
    <section id="services" className="section line">
      <div className="wrap grid gap-10 md:grid-cols-12 md:gap-8">
        <div className="md:col-span-4">
          <h2 className="h2 reveal">{services.title}</h2>
          <p className="reveal mt-5 max-w-xs text-sm leading-relaxed text-mute">{services.intro}</p>
        </div>
        <ul className="md:col-span-8">
          {services.items.map((s, i) => (
            <li key={s.name} className="reveal line grid grid-cols-[2.5rem_1fr] gap-4 py-6 first:border-t-0 md:py-8">
              <span className="font-serif text-xl text-accent">{String(i + 1).padStart(2, '0')}</span>
              <div>
                <h3 className="font-serif text-2xl font-medium md:text-3xl">{s.name}</h3>
                <p className="mt-2 max-w-md text-sm leading-relaxed text-mute">{s.note}</p>
              </div>
            </li>
          ))}
          <li className="reveal pt-4">
            <WaButton label={services.cta} />
          </li>
        </ul>
      </div>
    </section>
  )
}

function Process() {
  return (
    <section id="process" className="section bg-ink text-bg">
      <div className="wrap">
        <h2 className="h2 reveal max-w-xl">{process.title}</h2>
        <ol className="mt-12 grid gap-10 md:mt-16 md:grid-cols-3 md:gap-0">
          {process.steps.map((s, i) => (
            <li
              key={s.title}
              className={`reveal border-t border-bg/25 pt-6 md:pr-10 ${i === 1 ? 'md:mt-12' : ''} ${i === 2 ? 'md:mt-24' : ''}`}
            >
              <span className="font-serif text-5xl text-[#D9A89B]">{i + 1}</span>
              <h3 className="mt-4 font-serif text-2xl font-medium">{s.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-bg/80">{s.text}</p>
            </li>
          ))}
        </ol>
        <div className="reveal mt-14">
          <a
            className="btn bg-bg text-ink hover:bg-accent hover:text-bg"
            href={wa('Здравствуйте! Хочу записаться в Lerami.')}
            target="_blank"
            rel="noopener"
          >
            <MessageCircle size={18} strokeWidth={1.5} aria-hidden="true" />
            {process.cta}
          </a>
        </div>
      </div>
    </section>
  )
}

function Gallery() {
  if (gallery.length === 0) return null
  return (
    <section id="works" className="section">
      <div className="wrap">
        <h2 className="h2 reveal">Работы</h2>
        <div className="mt-10 grid grid-cols-2 gap-3 md:grid-cols-3 md:gap-5">
          {gallery.map((g) => (
            <img
              key={g.src}
              src={g.src}
              alt={g.alt}
              loading="lazy"
              style={{ aspectRatio: g.ratio }}
              className="reveal w-full object-cover"
            />
          ))}
        </div>
      </div>
    </section>
  )
}

function Faq() {
  return (
    <section id="faq" className="section">
      <div className="wrap grid gap-10 md:grid-cols-12 md:gap-8">
        <h2 className="h2 reveal md:col-span-4">{faq.title}</h2>
        <div className="md:col-span-8">
          {faq.items.map((it) => (
            <details key={it.q} className="reveal line group py-5 first:border-t-0">
              <summary className="flex min-h-[44px] cursor-pointer list-none items-center justify-between gap-4 font-serif text-xl font-medium md:text-2xl">
                {it.q}
                <Plus size={22} strokeWidth={1.5} aria-hidden="true" className="shrink-0 transition-transform group-open:rotate-45" />
              </summary>
              <p className="mt-3 max-w-xl text-sm leading-relaxed text-mute">{it.a}</p>
            </details>
          ))}
        </div>
      </div>
    </section>
  )
}

function LeadForm() {
  const [errors, setErrors] = useState<{ name?: string; phone?: string }>({})

  function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const d = new FormData(e.currentTarget)
    const name = String(d.get('name') || '').trim()
    const phone = String(d.get('phone') || '').trim()
    const service = String(d.get('service') || '').trim()
    const comment = String(d.get('comment') || '').trim()
    const next: { name?: string; phone?: string } = {}
    if (name.length < 2) next.name = 'Укажите имя'
    if (phone.replace(/\D/g, '').length < 10) next.phone = 'Укажите номер телефона'
    setErrors(next)
    if (Object.keys(next).length) return
    const lines = [
      'Здравствуйте! Хочу записаться в Lerami.',
      `Имя: ${name}`,
      `Телефон: ${phone}`,
      service && `Услуга: ${service}`,
      comment && `Пожелания: ${comment}`,
    ].filter(Boolean)
    window.open(wa(lines.join('\n')), '_blank', 'noopener')
  }

  const field =
    'mt-2 block min-h-[48px] w-full border border-ink/30 bg-bg px-4 text-base placeholder:text-mute/70 focus:border-accent'

  return (
    <form onSubmit={onSubmit} noValidate className="reveal grid gap-5">
      <div>
        <label htmlFor="f-name" className="text-sm font-semibold">{f.fields.name}</label>
        <input id="f-name" name="name" autoComplete="name" className={field} aria-invalid={!!errors.name} aria-describedby="e-name" />
        <p id="e-name" role="alert" className="mt-1 min-h-[1.25rem] text-sm text-accent">{errors.name}</p>
      </div>
      <div>
        <label htmlFor="f-phone" className="text-sm font-semibold">{f.fields.phone}</label>
        <input id="f-phone" name="phone" type="tel" inputMode="tel" autoComplete="tel" className={field} aria-invalid={!!errors.phone} aria-describedby="e-phone" />
        <p id="e-phone" role="alert" className="mt-1 min-h-[1.25rem] text-sm text-accent">{errors.phone}</p>
      </div>
      <div>
        <label htmlFor="f-service" className="text-sm font-semibold">{f.fields.service}</label>
        <select id="f-service" name="service" className={field} defaultValue="">
          <option value="">Выберу позже</option>
          {services.items.map((s) => (
            <option key={s.name} value={s.name}>{s.name}</option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="f-comment" className="text-sm font-semibold">{f.fields.comment}</label>
        <textarea id="f-comment" name="comment" rows={3} className={`${field} py-3`} />
      </div>
      <button type="submit" className="btn btn-primary w-full sm:w-auto">
        <MessageCircle size={18} strokeWidth={1.5} aria-hidden="true" />
        {f.submit}
      </button>
    </form>
  )
}

function Contacts() {
  return (
    <section id="contacts" className="section line bg-sand">
      <div className="wrap grid gap-12 md:grid-cols-12 md:gap-8">
        <div className="md:col-span-5">
          <h2 className="h2 reveal">{f.title}</h2>
          <p className="reveal mt-5 max-w-sm text-sm leading-relaxed text-mute">{f.lead}</p>
          <div className="mt-10">
            <LeadForm />
          </div>
        </div>
        <div className="md:col-span-6 md:col-start-7">
          <h2 className="h2 reveal">{contacts.title}</h2>
          <ul className="reveal mt-8 grid gap-1 text-base">
            <li>
              <a className="flex min-h-[48px] items-center gap-3 hover:text-accent" href={telHref}>
                <Phone size={20} strokeWidth={1.5} aria-hidden="true" />
                {b.phone}
              </a>
            </li>
            <li>
              <a className="flex min-h-[48px] items-center gap-3 hover:text-accent" href={waBase} target="_blank" rel="noopener">
                <MessageCircle size={20} strokeWidth={1.5} aria-hidden="true" />
                WhatsApp
              </a>
            </li>
            <li>
              <a className="flex min-h-[48px] items-center gap-3 hover:text-accent" href={b.instagram} target="_blank" rel="noopener">
                <Instagram size={20} strokeWidth={1.5} aria-hidden="true" />
                {b.instagramHandle}
              </a>
            </li>
            <li className="flex min-h-[48px] items-center gap-3">
              <MapPin size={20} strokeWidth={1.5} aria-hidden="true" />
              {b.city}{b.address ? `, ${b.address}` : ''}
            </li>
            {b.hours && <li className="pl-8 text-mute">{b.hours}</li>}
          </ul>
          <a
            className="reveal mt-8 flex min-h-[200px] items-end justify-between border border-ink/25 bg-bg p-6 transition-colors hover:border-accent"
            href={b.twoGis}
            target="_blank"
            rel="noopener"
          >
            <span className="max-w-[12rem] font-serif text-2xl font-medium leading-tight">{contacts.mapLabel}</span>
            <ArrowUpRight size={28} strokeWidth={1.5} aria-hidden="true" className="text-accent" />
          </a>
        </div>
      </div>
    </section>
  )
}

function Footer() {
  return (
    <footer className="px-5 pb-28 pt-10 text-sm text-mute md:px-10 md:pb-10">
      <div className="wrap flex flex-col justify-between gap-3 sm:flex-row">
        <span>© {new Date().getFullYear()} {b.name}, {b.city}</span>
        <a href={b.instagram} target="_blank" rel="noopener" className="hover:text-accent">{b.instagramHandle}</a>
      </div>
    </footer>
  )
}

function MobileBar() {
  return (
    <div className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-2 border-t border-ink/15 bg-bg md:hidden" role="group" aria-label="Быстрая связь">
      <a className="flex min-h-[56px] items-center justify-center gap-2 text-sm font-semibold" href={telHref}>
        <Phone size={18} strokeWidth={1.5} aria-hidden="true" />
        Позвонить
      </a>
      <a
        className="flex min-h-[56px] items-center justify-center gap-2 bg-accent text-sm font-semibold text-bg"
        href={wa('Здравствуйте! Хочу записаться в Lerami.')}
        target="_blank"
        rel="noopener"
      >
        <MessageCircle size={18} strokeWidth={1.5} aria-hidden="true" />
        WhatsApp
      </a>
    </div>
  )
}

export default function App() {
  useReveal()
  return (
    <>
      <a href="#services" className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:bg-bg focus:p-3">
        К услугам
      </a>
      <Header />
      <main>
        <Hero />
        <Services />
        <Process />
        <Gallery />
        <Faq />
        <Contacts />
      </main>
      <Footer />
      <MobileBar />
    </>
  )
}
