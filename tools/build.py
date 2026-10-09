#!/usr/bin/env python3
"""Build The Pilates Room from content/.

    python3 tools/build.py

Everything factual — address, hours, rates, credentials, FAQs — lives in
content/site.json and is rendered into BOTH the visible page and the
schema.org markup, so the two can never drift apart. That matching is what
local search and the AI assistants actually reward.
"""
import html, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recipes as R

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(ROOT, 'content', 'site.json')))

# BASE lets one build serve either from a GitHub Pages subpath (staging) or
# from the domain root (launch). PREVIEW keeps the staging copy out of search
# so it can never compete with her live WordPress site for the same content.
BASE = os.environ.get('BASE', '').rstrip('/')
PREVIEW = os.environ.get('PREVIEW') == '1'

def rebase(doc):
    """Prefix every root-absolute asset/link path with BASE.

    Applied once to the finished document rather than at every call site, so
    there is no way to forget it on a new template."""
    if not BASE:
        return doc
    doc = re.sub(r'(\b(?:href|src)=")(/(?!/))', r'\1' + BASE + r'\2', doc)
    doc = re.sub(r'(srcset=")([^"]+)(")',
                 lambda m: m.group(1) + re.sub(r'(^|,\s*)/', r'\1' + BASE + '/', m.group(2)) + m.group(3),
                 doc)
    return doc
FONTS = ("https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;"
         "0,9..144,400;0,9..144,500;1,9..144,300&family=Inter:wght@400;500;600&display=swap")

def e(s): return html.escape(str(s), quote=True)
def addr(): return f"{S['street']}, {S['city']}, {S['region']} {S['zip']}"
def img(name, alt, cls="", sizes="(max-width:980px) 100vw, 50vw", loading="lazy"):
    return (f'<img src="/assets/img/{name}.jpg" srcset="/assets/img/{name}@700.jpg 700w, '
            f'/assets/img/{name}.jpg 1400w" sizes="{sizes}" alt="{e(alt)}" '
            f'loading="{loading}" decoding="async"{f" class={cls}" if cls else ""}>')
ARROW = ('<svg width="15" height="11" viewBox="0 0 15 11" fill="none" aria-hidden="true">'
         '<path d="M9.2 1l4.3 4.5L9.2 10M13 5.5H1" stroke="currentColor" stroke-width="1.3" '
         'stroke-linecap="round" stroke-linejoin="round"/></svg>')

def local_business_schema():
    return {
        "@context": "https://schema.org", "@type": "HealthAndBeautyBusiness",
        "@id": S['url'] + "/#studio",
        "name": S['name'], "description": S['tagline'], "url": S['url'] + "/",
        "telephone": S['phoneRaw'], "email": S['email'], "priceRange": S['priceRange'],
        "image": S['url'] + "/assets/img/hands-on-springs.jpg",
        "logo": S['url'] + "/assets/img/logo.png",
        "address": {"@type": "PostalAddress", "streetAddress": S['street'],
                    "addressLocality": S['city'], "addressRegion": S['region'],
                    "postalCode": S['zip'], "addressCountry": "US"},
        "geo": {"@type": "GeoCoordinates", "latitude": S['lat'], "longitude": S['lon']},
        "openingHoursSpecification": [
            {"@type": "OpeningHoursSpecification",
             "dayOfWeek": [f"https://schema.org/{d}" for d in
                           ["Monday","Tuesday","Wednesday","Thursday","Friday"]],
             "opens": o, "closes": c} for (_a, _b, o, c) in S['hoursSpec']],
        "sameAs": S['social'],
        "founder": {"@type": "Person", "name": S['instructor']},
        "employee": {"@type": "Person", "name": S['instructor'],
                     "jobTitle": "Certified Pilates Instructor"},
        "areaServed": [{"@type": "City", "name": n} for n in
                       ["Portsmouth","Rye","New Castle","Greenland","Newington","Kittery","York"]],
        "hasOfferCatalog": {
            "@type": "OfferCatalog", "name": "Pilates and movement services",
            "itemListElement": [
                {"@type": "Offer",
                 "itemOffered": {"@type": "Service", "name": s['name'], "description": s['desc'],
                                 "provider": {"@id": S['url'] + "/#studio"}},
                 **({"price": str(s['price']), "priceCurrency": "USD"} if s['price'] else {})}
                for s in S['services']]},
    }

def faq_schema():
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": a}}
                           for q, a in S['faqs']]}

def nav_html(group, cls, path):
    out = []
    for href, label in S[group]:
        cur = ' aria-current="page"' if href == path else ''
        out.append(f'<a href="{href}"{cur}>{e(label)}</a>')
    return f'<nav class="{cls}">' + ''.join(out) + '</nav>'

def header(path):
    links = ''.join(f'<a href="{h}">{e(l)}</a>' for h, l in S['navLeft'] + S['navRight'])
    return f'''<header class="hdr" id="hdr">
  <div class="wrap hdr-in">
    {nav_html('navLeft','nav-l',path)}
    <a class="brand" href="/" aria-label="{e(S['name'])} — home">
      <img src="/assets/img/logo.png" width="188" height="99" alt="{e(S['name'])}">
    </a>
    {nav_html('navRight','nav-r',path)}
    <button class="burger" id="burger" aria-label="Menu" aria-expanded="false"><span></span></button>
  </div>
  <div class="mnav" id="mnav"><div class="wrap">{links}
    <a href="tel:{S['phoneRaw']}">{e(S['phone'])}</a></div></div>
</header>'''

def footer():
    socials = ''.join(f'<a href="{u}" rel="noopener">{"Facebook" if "facebook" in u else "YouTube"}</a>'
                      for u in S['social'])
    links = ''.join(f'<a href="{h}">{e(l)}</a>'
                    for h, l in S['navLeft'] + [['/what-is-pilates/', 'What is Pilates']] + S['navRight'])
    return f'''<footer class="ftr"><div class="wrap">
  <div class="ftr-top">
    <div>
      <p class="ftr-mark">{e(S['name'])}</p>
      <p class="ftr-sub">{e(S['city'])}, New Hampshire</p>
      <p>{e(addr())}</p>
      <p><a href="tel:{S['phoneRaw']}">{e(S['phone'])}</a> · <a href="mailto:{S['email']}">{e(S['email'])}</a></p>
      <p>{e(S['hours'])}</p>
      <p class="socials">{socials}</p>
    </div>
    <nav>{links}</nav>
  </div>
  <div class="ftr-btm"><span>&copy; 2026 {e(S['name'])}</span>
    <span>Site by <a href="https://theswitchboardcompany.com">The Switchboard Company</a></span></div>
</div></footer>'''

def shell(path, title, desc, body, schema=None, hero_preload=None):
    blocks = ''.join(
        f'\n<script type="application/ld+json">{json.dumps(s, separators=(",",":"))}</script>'
        for s in (schema or []))
    canon = S['url'] + path
    noindex = '\n<meta name="robots" content="noindex,nofollow">' if PREVIEW else ''
    pre = (f'\n<link rel="preload" as="image" href="/assets/img/{hero_preload}.jpg" '
           f'imagesrcset="/assets/img/{hero_preload}@700.jpg 700w, /assets/img/{hero_preload}.jpg 1400w">'
           if hero_preload else '')
    return f'''<!DOCTYPE html>
<html lang="en" class="no-js">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canon}">{noindex}
<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{S['url']}/assets/img/hands-on-springs.jpg">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/img/logo.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="/assets/site.css">{pre}
<script>document.documentElement.className=document.documentElement.className.replace('no-js','js')</script>{blocks}
</head>
<body>
{header(path)}
<main>
{body}
</main>
{footer()}
<script src="/assets/site.js" defer></script>
</body>
</html>
'''

def write(path, text):
    text = rebase(text)
    out = os.path.join(ROOT, path.strip('/'), 'index.html') if path != '/' else os.path.join(ROOT, 'index.html')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8').write(text)
    return out

# ─────────────────────────────────────────────────────────── sections
def hero():
    slides = ''.join(
        '<figure%s><img src="/assets/img/%s.jpg" srcset="/assets/img/%s@700.jpg 700w, '
        '/assets/img/%s.jpg 1400w" sizes="100vw" alt="%s" %s decoding="async"></figure>'
        % (' class="on"' if i == 0 else '', n, n, n, e(alt),
           'fetchpriority="high"' if i == 0 else 'loading="lazy"')
        for i, (n, alt) in enumerate(S['hero']))
    dots = ''.join('<button type="button" aria-label="Show image %d" aria-current="%s"></button>'
                   % (i + 1, 'true' if i == 0 else 'false') for i in range(len(S['hero'])))
    return '''<section class="hero">
  <div class="hero-slides" id="heroSlides">%s</div>
  <div class="wrap hero-in">
    <img class="hero-logo" src="/assets/img/logo.png" width="597" height="316"
         alt="%s" fetchpriority="high">
    <p class="eyebrow eyebrow-light">%s</p>
    <h1 class="h1">One room, one teacher, and your full hour.</h1>
    <p class="lead">Private and semi-private Reformer Pilates with %s &mdash; built around your body, your injuries, and what you want to get back to doing.</p>
    <div class="hero-cta">
      <a class="btn btn-light" href="tel:%s">Call %s%s</a>
      <a class="btn btn-outline-light" href="/book-an-appointment/">How to book</a>
    </div>
    <div class="hero-dots" id="heroDots" role="group" aria-label="Choose hero image">%s</div>
  </div>
</section>''' % (slides, e(S['name']), e(S['tagline']), e(S['instructor']),
                 S['phoneRaw'], e(S['phone']), ARROW, dots)

def strip():
    items = [("Private &amp; semi-private only", "No class floor. One person, or two."),
             ("Mat, reformer, chair &amp; barrel", "Fully certified on the full apparatus."),
             (e(S['street']), f"Downtown {e(S['city'])}. {e(S['parking'])}.")]
    cells = ''.join(f'<div class="strip-item"><p class="k">{k}</p><p class="v">{v}</p></div>' for k, v in items)
    return f'<section class="strip"><div class="wrap"><div class="strip-in">{cells}</div></div></section>'

def faq_section():
    rows = ''.join(f'<details><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in S['faqs'])
    return f'''<section class="section" id="faq">
  <div class="wrap">
    <div class="head" data-reveal><p class="eyebrow">Questions</p>
      <h2 class="h2">Before you call.</h2></div>
    <div class="faq" data-reveal>{rows}</div>
  </div>
</section>'''

def cta_band():
    return f'''<section class="section band cta-band">
  <div class="wrap">
    <p class="eyebrow eyebrow-light">Begin</p>
    <h2 class="h2">Start with a free consultation.</h2>
    <p class="lead">Thirty minutes, no charge, nothing to buy at the end of it. Call the studio and talk to Michele directly.</p>
    <div class="hero-cta">
      <a class="btn btn-light" href="tel:{S['phoneRaw']}">Call {e(S['phone'])}{ARROW}</a>
      <a class="btn btn-outline-light" href="/book-an-appointment/">See how booking works</a>
    </div>
  </div>
</section>'''

def contact_section():
    return f'''<section class="section" id="visit">
  <div class="wrap contact">
    <div data-reveal>
      <p class="eyebrow">Visit</p>
      <h2 class="h2" style="margin-top:18px">{e(S['name'])}</h2>
      <div class="cinfo">
        <div><span class="lbl">Address</span><span class="val">{e(S['street'])}<br>{e(S['city'])}, {e(S['region'])} {e(S['zip'])}</span></div>
        <div><span class="lbl">Parking</span><span class="val">{e(S['parking'])}</span></div>
        <div><span class="lbl">Phone</span><a class="val" href="tel:{S['phoneRaw']}">{e(S['phone'])}</a></div>
        <div><span class="lbl">Email</span><a class="val" href="mailto:{S['email']}">{e(S['email'])}</a></div>
        <div><span class="lbl">Hours</span><span class="val">{e(S['hours'])}</span></div>
      </div>
    </div>
    <div class="map" data-reveal>
      <iframe src="https://www.google.com/maps?q={S['street'].replace(' ','+')}+{S['city']}+{S['region']}+{S['zip']}&output=embed"
        loading="lazy" title="Map to {e(addr())}"></iframe>
    </div>
  </div>
</section>'''

# ─────────────────────────────────────────────────────────── pages
def page_home():
    cards = ''.join(f'''<article class="card">
      <div class="card-img">{img(n, alt, sizes="(max-width:980px) 100vw, 33vw")}</div>
      <div class="card-body"><h3 class="h3">{e(s['name'])}</h3><p>{e(s['desc'])}</p>
        <p class="price">{"$"+str(s['price']) if s['price'] else "Ask"} <span>{"/ "+s['unit'] if s['unit'] else "/ about availability"}</span></p>
      </div></article>'''
      for s, n, alt in zip(S['services'][:3],
                           ["studio-3","semi-private","mat-class-1"],
                           ["A private reformer session","A semi-private session on the reformers","Mat work in the studio"]))
    conds = ''.join(f'<div><span class="dot"></span><p>{e(t)}<small>{e(d)}</small></p></div>'
                    for t, d in S['conditions'])
    return shell('/', f"{S['name']} | {S['tagline']}",
        f"Private and semi-private Reformer Pilates with {S['instructor']} at {addr()}. Back pain, rehabilitation, pre and postnatal, active aging. Free 30-minute consultation — call {S['phone']}.",
        hero() + strip() + f'''
<section class="section"><div class="wrap split">
  <div data-reveal>
    <p class="eyebrow">The studio</p>
    <h2 class="h2">Pilates that starts with <span class="ital">your</span> body, not a routine.</h2>
    <p class="lead" style="margin-top:22px">Most people arrive because something hurts, something changed, or something they love doing has started to cost them. A back that complains after a round of golf. A shoulder that never quite came back. A body six weeks after a C-section.</p>
    <p class="lead" style="margin-top:16px">Because every session is private, nothing is generic. Michele watches how you actually move, builds the work around it, and adjusts the moment it needs adjusting.</p>
    <p class="quote">&ldquo;10 times to feel, 20 times to notice, 30 times to change your body.&rdquo;</p>
    <p class="quote-by">&mdash; Joseph Pilates</p>
  </div>
  <div class="fig" data-reveal>{img('hands-on-springs','Michele working hands-on with a client on the reformer')}</div>
</div></section>

<section class="section" style="background:var(--paper);border-top:1px solid var(--line);border-bottom:1px solid var(--line)">
  <div class="wrap">
    <div class="head" data-reveal><p class="eyebrow">Sessions</p>
      <h2 class="h2">Ways to work together.</h2>
      <p class="lead">Everything is by appointment, Monday to Friday. Reformer work is the core of the studio; mat, yoga and nutrition round it out.</p></div>
    <div class="cards" data-reveal>{cards}</div>
    <p style="margin-top:30px" data-reveal><a class="btn btn-ghost" href="/rates-and-services/">See all rates and services{ARROW}</a></p>
  </div>
</section>

<section class="section"><div class="wrap">
  <div class="head" data-reveal><p class="eyebrow">Who it is for</p>
    <h2 class="h2">Most people here are working around something.</h2>
    <p class="lead">Pilates builds strength without pounding your joints, which is exactly why it suits bodies that cannot simply go and lift heavier.</p></div>
  <div class="fory" data-reveal>{conds}</div>
  <p style="margin-top:32px" data-reveal><a class="btn btn-ghost" href="/what-is-pilates/">What is Pilates, and what is it good for?{ARROW}</a></p>
</div></section>

<section class="section" style="background:var(--paper);border-top:1px solid var(--line)">
  <div class="wrap split">
    <div class="fig" data-reveal>{img('michele-portrait','Michele McCauley at The Pilates Room')}</div>
    <div data-reveal>
      <p class="eyebrow">Your instructor</p>
      <h2 class="h2" style="margin-top:18px">{e(S['instructor'])}</h2>
      <p class="lead" style="margin-top:22px">Michele studied under Kathy Van Patten at the Movement Center of Boston and trained for her 200-hour yoga certification at the Nosara Yoga Institute in Costa Rica. She is a triathlete, a surfer, a dancer and a culinary school graduate &mdash; which is how nutrition ended up part of the studio too.</p>
      <p style="margin-top:26px"><a class="btn btn-ghost" href="/about-the-pilates-room/">More about Michele{ARROW}</a></p>
    </div>
  </div>
</section>
''' + faq_section() + cta_band() + contact_section(),
        schema=[local_business_schema(), faq_schema()], hero_preload=S['hero'][0][0])

def page_rates():
    tables = ''
    for name, rows in S['rates'].items():
        best = max(range(len(rows)), key=lambda i: rows[i][1])
        body = ''.join(f'<div class="rate-row{" best" if i==2 else ""}"><span class="q">{e(q)}</span>'
                       f'<span class="p">${v}</span></div>' for i, (q, v) in enumerate(rows))
        per = round(rows[-1][1] / 10, 2)
        tables += (f'<div class="rate-card"><h3 class="h3">{e(name)}</h3>'
                   f'<p style="font-size:.88rem;color:var(--ink-soft);margin-top:7px">'
                   f'{"One-on-one, by appointment" if "Private Reformer"==name else "Two people, priced per person"}</p>'
                   f'<div style="margin-top:22px">{body}</div>'
                   f'<p style="margin-top:20px;font-size:.84rem;color:var(--ink-soft)">Works out to ${per:g} a session at ten.</p></div>')
    others = ''.join(f'<div><span class="dot"></span><p>{e(s["name"])}<small>{e(s["desc"])}</small></p></div>'
                     for s in S['services'][2:])
    return shell('/rates-and-services/', f"Rates & Services | {S['name']}",
        f"Private Reformer Pilates from $85 and semi-private from $45 per person at {S['name']}, {addr()}. Mat Pilates, yoga and fitness nutrition. Free 30-minute consultation.",
        f'''<section class="section"><div class="wrap">
  <div class="head" data-reveal><p class="eyebrow">Rates &amp; Services</p>
    <h2 class="h2">Straightforward pricing.</h2>
    <p class="lead">Every new client starts with a free thirty-minute consultation. Most people begin with a package of five.</p></div>
  <div class="rates" data-reveal>{tables}</div>
  <div style="margin-top:clamp(3rem,6vw,5rem)" data-reveal>
    <h3 class="h3" style="margin-bottom:8px">Also offered</h3>
    <div class="fory" style="margin-top:18px">{others}</div>
  </div>
  <p style="margin-top:34px;font-size:.92rem;color:var(--ink-soft)" data-reveal>
    Sessions are by appointment, Monday to Friday. A 24-hour cancellation policy applies.</p>
</div></section>''' + cta_band() + contact_section(),
        schema=[local_business_schema()])

def page_book():
    steps = ''.join(f'<li><span class="n">{i+1}</span><div><b>{e(t)}</b><p>{e(d)}</p></div></li>'
                    for i, (t, d) in enumerate(S['bookSteps']))
    return shell('/book-an-appointment/', f"Book an Appointment | {S['name']}",
        f"Booking at {S['name']} is by phone. Call {S['phone']} to arrange a free 30-minute consultation with {S['instructor']} in {S['city']}, {S['region']}.",
        f'''<section class="section"><div class="wrap">
  <div class="head center" data-reveal><p class="eyebrow">Book an Appointment</p>
    <h2 class="h2">Booking is a phone call.</h2>
    <p class="lead center">There is no online calendar, and that is deliberate. Michele wants to hear what is going on with your body before she puts you on a reformer.</p></div>
  <div style="max-width:760px;margin:0 auto" data-reveal>
    <p style="text-align:center;margin-bottom:34px">
      <a class="btn btn-primary" href="tel:{S['phoneRaw']}" style="font-size:1.05rem;padding:1.15em 2.4em">Call {e(S['phone'])}{ARROW}</a>
    </p>
    <ol class="steps">{steps}</ol>
    <p style="margin-top:30px;font-size:.93rem;color:var(--ink-soft)">
      Prefer to write? Email <a href="mailto:{S['email']}" style="color:var(--deep);border-bottom:1px solid currentColor">{e(S['email'])}</a>
      and include a phone number — Michele will call you back.</p>
  </div>
</div></section>''' + contact_section(),
        schema=[local_business_schema()])

def page_about():
    creds = ''.join(f'<li>{e(a)} <span>{e(b)}</span></li>' for a, b in S['credentials'])
    return shell('/about-the-pilates-room/', f"About {S['instructor']} | {S['name']}",
        f"{S['instructor']} is a certified Pilates instructor (mat, reformer, chair and barrel), ISSA personal trainer and fitness nutrition specialist, with a 200-hour yoga certification from the Nosara Yoga Institute.",
        f'''<section class="section"><div class="wrap split">
  <div data-reveal>
    <p class="eyebrow">About</p>
    <h2 class="h2" style="margin-top:18px">{e(S['instructor'])}</h2>
    <p class="lead" style="margin-top:22px">Michele has built {e(S['name'])} around one idea: that a room with one teacher and one client in it can do things a class floor never can. She studied under Kathy Van Patten at the Movement Center of Boston, who she still calls her mentor, and trained for her 200-hour yoga certification at the Nosara Yoga Institute in Costa Rica.</p>
    <p class="lead" style="margin-top:16px">Her background runs through muscle anatomy, movement and the body&ndash;mind connection, and through triathlon training, running, cycling, swimming, dancing and surfing. She is also a Johnson &amp; Wales culinary graduate, which is how nutrition and the recipe blog ended up part of the studio.</p>
    <p class="lead" style="margin-top:16px">In practice that adds up to someone who can watch how you move, understand why it hurts, and know which piece of apparatus will help.</p>
  </div>
  <div class="fig" data-reveal>{img('michele-portrait','Michele McCauley at The Pilates Room')}</div>
</div></section>

<section class="section" style="background:var(--paper);border-top:1px solid var(--line);border-bottom:1px solid var(--line)">
  <div class="wrap">
    <div class="head" data-reveal><p class="eyebrow">Training</p><h2 class="h2">Certifications.</h2></div>
    <ul class="creds" data-reveal style="max-width:760px">{creds}</ul>
    <p style="margin-top:26px;font-size:.92rem;color:var(--ink-soft)" data-reveal>
      Johnson &amp; Wales University, culinary graduate (A.A.S.) &nbsp;·&nbsp; Southern New Hampshire University, B.S. Accounting &amp; Finance</p>
  </div>
</section>

<section class="section"><div class="wrap split">
  <div class="fig" data-reveal>{img('michele-plank','Michele McCauley demonstrating a side plank')}</div>
  <div class="fig" data-reveal>{img('equipment-detail','Reformer springs in the studio')}</div>
</div></section>''' + cta_band() + contact_section(),
        schema=[local_business_schema(),
                {"@context":"https://schema.org","@type":"Person","name":S['instructor'],
                 "jobTitle":"Certified Pilates Instructor",
                 "worksFor":{"@id":S['url']+"/#studio"},
                 "alumniOf":["Nosara Yoga Institute","Johnson & Wales University",
                             "Southern New Hampshire University"],
                 "knowsAbout":["Pilates","Reformer Pilates","Yoga","Fitness nutrition",
                               "Prenatal and postnatal exercise","Active aging"]}])

RECIPES = json.load(open(os.path.join(ROOT, 'content', 'recipes-raw.json')))
RECIPES.sort(key=lambda r: r.get('date') or '', reverse=True)

def rimg(slug, alt, sizes, prio=False):
    return ('<img src="/assets/img/recipes/%s.jpg" srcset="/assets/img/recipes/%s@560.jpg 560w, '
            '/assets/img/recipes/%s.jpg 1000w" sizes="%s" alt="%s" %s decoding="async">'
            % (slug, slug, slug, sizes, e(alt),
               'fetchpriority="high"' if prio else 'loading="lazy"'))

def recipe_times(rec):
    out = []
    for label, field in (("Prep", "prep_time"), ("Cook", "cook_time")):
        v = R.mins(rec.get(field))
        if v: out.append((label, v))
    cl, cv = rec.get('custom_time_label') or '', R.mins(rec.get('custom_time'))
    if cv and cl: out.append((cl, cv))
    tv = R.mins(rec.get('total_time'))
    if tv: out.append(("Total", tv))
    return out

def page_recipe(r):
    rec, slug = r['recipe'], r['slug']
    title = R.strip_tags(r['title']['rendered'])
    summary = R.strip_tags(rec.get('summary'))

    times = ''.join('<div><span class="rl">%s</span><span class="rv">%s</span></div>' % (e(l), e(v))
                    for l, v in recipe_times(rec))
    chips = []
    if rec.get('servings'):
        chips.append(("Servings", ("%s %s" % (rec['servings'], rec.get('servings_unit') or '')).strip()))
    for c in R.taxa(rec, 'course'):  chips.append(("Course", c))
    for c in R.taxa(rec, 'cuisine'): chips.append(("Cuisine", c))
    chip_html = ''.join('<span class="chip"><i>%s</i> %s</span>' % (e(k), e(v)) for k, v in chips)

    ing_html = ''
    for kind, amt, name, note in R.parse_ingredients(rec):
        if kind == 'heading':
            ing_html += '<li class="ing-h">%s</li>' % e(amt or name)
        else:
            ing_html += ('<li>%s<span>%s</span>%s</li>'
                         % ('<b>%s</b> ' % e(amt) if amt else '', e(name),
                            ' <i>%s</i>' % e(note) if note else ''))

    step_html, n = '', 0
    for kind, text in R.parse_steps(rec):
        if kind == 'heading':
            step_html += '<li class="step-h">%s</li>' % e(text)
        else:
            n += 1
            step_html += '<li><span class="sn">%d</span><p>%s</p></li>' % (n, e(text))

    notes = R.strip_tags(rec.get('notes'))
    notes_html = ('<section class="rsec"><h2 class="h3">Notes</h2><p class="rnote">%s</p></section>'
                  % e(notes)) if notes else ''
    equip = [q.get('name') for q in (rec.get('equipment') or []) if q.get('name')]
    equip_html = ('<section class="rsec"><h2 class="h3">Equipment</h2><ul class="plain">%s</ul></section>'
                  % ''.join('<li>%s</li>' % e(q) for q in equip)) if equip else ''

    body = ('<article class="recipe"><div class="wrap">'
            '<p class="crumb"><a href="/the-culinary-greenhouse/">&larr; The Culinary Greenhouse</a></p>'
            '<div class="rhead"><div class="rhead-img">%s</div><div><h1 class="h2">%s</h1>%s'
            '<div class="chips">%s</div></div></div>%s'
            '<div class="rbody">'
            '<section class="rsec"><h2 class="h3">Ingredients</h2><ul class="ings">%s</ul></section>'
            '<div><section class="rsec"><h2 class="h3">Method</h2><ol class="steps-r">%s</ol></section>%s%s</div>'
            '</div></div></article>'
            % (rimg(slug, title, "(max-width:860px) 100vw, 400px", prio=True),
               e(title),
               '<p class="lead" style="margin-top:16px">%s</p>' % e(summary) if summary else '',
               chip_html,
               '<div class="rtimes">%s</div>' % times if times else '',
               ing_html, step_html, equip_html, notes_html))

    desc = summary or ("%s — a recipe from The Culinary Greenhouse at %s." % (title, S['name']))
    return shell('/the-culinary-greenhouse/%s/' % slug,
                 "%s | The Culinary Greenhouse" % title, desc[:300],
                 body + cta_band(),
                 schema=[R.recipe_schema(r, S, "%s/assets/img/recipes/%s.jpg" % (S['url'], slug)),
                         local_business_schema()])

def page_recipe_index():
    cards = ''
    for r in RECIPES:
        rec, slug = r['recipe'], r['slug']
        title = R.strip_tags(r['title']['rendered'])
        summary = R.strip_tags(rec.get('summary'))
        t = R.mins(rec.get('total_time'))
        cards += ('<a class="card" href="/the-culinary-greenhouse/%s/">'
                  '<div class="card-img">%s</div><div class="card-body">'
                  '<h3 class="h3">%s</h3><p>%s</p>%s</div></a>'
                  % (slug, rimg(slug, title, "(max-width:980px) 100vw, 33vw"), e(title), e(summary),
                     '<p class="rmeta">%s total</p>' % e(t) if t else ''))
    body = ('<section class="section"><div class="wrap">'
            '<div class="head center" data-reveal><p class="eyebrow">The Culinary Greenhouse</p>'
            '<h2 class="h2">Recipes from the studio.</h2>'
            '<p class="lead center">Michele is a Johnson &amp; Wales culinary graduate and an ISSA '
            'fitness nutrition specialist. These are the recipes she actually cooks.</p></div>'
            '<div class="cards" data-reveal>%s</div></div></section>' % cards)
    return shell('/the-culinary-greenhouse/', "The Culinary Greenhouse | %s" % S['name'],
        "Recipes from %s, a Johnson & Wales culinary graduate and ISSA fitness nutrition specialist at %s in %s, %s."
        % (S['instructor'], S['name'], S['city'], S['region']),
        body + cta_band(),
        schema=[local_business_schema(),
                {"@context": "https://schema.org", "@type": "CollectionPage",
                 "name": "The Culinary Greenhouse", "isPartOf": {"@id": S['url'] + "/#studio"},
                 "hasPart": [{"@type": "Recipe", "name": R.strip_tags(r['title']['rendered']),
                              "url": "%s/the-culinary-greenhouse/%s/" % (S['url'], r['slug'])}
                             for r in RECIPES]}])

def build_redirects():
    """Point every retired WordPress URL at whatever now covers it."""
    src = os.path.join(ROOT, 'content', 'posts-raw.json')
    if not os.path.exists(src):
        return []
    posts = json.load(open(src))
    live = {r['slug'] for r in RECIPES}

    # explicit wins first — these do not classify cleanly by keyword
    EXPLICIT = {
        'rates-services': '/rates-and-services/',
        'beach-yoga-booking-groups-now': '/rates-and-services/',
        'beach-yoga-is-simply-blissful': '/rates-and-services/',
        'sound-healing-workshop': '/',
        '832-2': '/',
    }
    FOOD = ('recipe','vegan','vegetarian','salad','soup','smoothie','cookie','brownie','tofu',
            'chicken','sprout','squash','beet','taco','donut','stew','tempeh','kale','pizza',
            'detox','hummus','sushi','curry','pasta','spring-roll','ice-cream','food','eat',
            'nutrition','saute','hangover','yogurt','dip','chickpea','chard','bean','quinoa',
            'salmon','shrimp','fish','cauliflower','cashew','snack','breakfast','lunch','dinner',
            'dessert','bread','sauce','drink','juice','tea','coffee','wedding')
    PILATES = ('pilates','reformer','scoliosis','core','posture','joint','back','stretch',
               'yoga','natal','aging','age-50','athlete','golf','injur','strength')

    out = []
    for post in posts:
        slug = post['slug']
        if slug in live:
            continue
        title = R.strip_tags(post['title']['rendered'])
        hay = (slug + ' ' + title).lower()
        if slug in EXPLICIT:
            target = EXPLICIT[slug]
        elif any(k in hay for k in FOOD):
            target = '/the-culinary-greenhouse/'
        elif any(k in hay for k in PILATES):
            target = '/what-is-pilates/'
        else:
            target = '/'          # never guess — send it to the homepage
        out.append((slug, target))
        write('/%s/' % slug, redirect_stub(target, title))
    return out

def page_pilates():
    P = S['pilates']
    secs = ''
    for i, (h, body) in enumerate(P['sections']):
        secs += ('<section class="psec" id="s%d"><h2 class="h3">%s</h2><p>%s</p></section>'
                 % (i, e(h), e(body)))
    toc = ''.join('<a href="#s%d">%s</a>' % (i, e(h)) for i, (h, _b) in enumerate(P['sections']))
    body = ('<section class="section"><div class="wrap">'
            '<div class="head" data-reveal><p class="eyebrow">What is Pilates</p>'
            '<h1 class="h2">Strength without the pounding.</h1>'
            '<p class="lead">%s</p></div>'
            '<div class="pwrap">'
            '<nav class="ptoc" aria-label="On this page" data-reveal>%s</nav>'
            '<div data-reveal>%s</div>'
            '</div></div></section>' % (e(P['intro']), toc, secs))
    return shell('/what-is-pilates/', "What is Pilates, and what is it good for? | %s" % S['name'],
        "How Reformer Pilates builds strength without loading your joints — and what it does for back and SI joint pain, scoliosis, active aging, athletes, and pre and postnatal recovery. %s, %s."
        % (S['name'], S['city']),
        body + cta_band(),
        schema=[local_business_schema(),
                {"@context": "https://schema.org", "@type": "Article",
                 "headline": "What is Pilates, and what is it good for?",
                 "about": "Reformer Pilates",
                 "author": {"@type": "Person", "name": S['instructor']},
                 "publisher": {"@id": S['url'] + "/#studio"},
                 "articleSection": [h for h, _b in P['sections']]}])

PAGES = [page_home, page_rates, page_book, page_about, page_pilates, page_recipe_index]

# Retired WordPress posts keep their URLs and point at whatever replaced them.
# GitHub Pages cannot serve a true 301, so these are instant meta-refresh stubs
# with a canonical — which Google follows and treats as a redirect.
def redirect_stub(target, title):
    return ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            '<title>%s</title><link rel="canonical" href="%s%s">'
            '<meta name="robots" content="noindex,follow">'
            '<meta http-equiv="refresh" content="0; url=%s">'
            '<script>location.replace("%s")</script></head>'
            '<body><p>This page has moved. <a href="%s">Continue</a>.</p></body></html>'
            % (e(title), S['url'], target, target, target, target))

def sitemap(paths):
    urls = ''.join('<url><loc>%s%s</loc></url>' % (S['url'], p) for p in paths)
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>' % urls)

def main():
    written, paths = [], []
    for fn in PAGES:
        doc = fn()
        path = re.search(r'<link rel="canonical" href="%s([^"]*)"' % re.escape(S['url']), doc).group(1)
        written.append(write(path, doc)); paths.append(path)
    for r in RECIPES:
        p = '/the-culinary-greenhouse/%s/' % r['slug']
        written.append(write(p, page_recipe(r))); paths.append(p)
    stubs = build_redirects()
    open(os.path.join(ROOT, 'sitemap.xml'), 'w').write(sitemap(paths))
    open(os.path.join(ROOT, 'robots.txt'), 'w').write(
        'User-agent: *\nDisallow: /\n' if PREVIEW
        else 'User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n' % S['url'])
    for p in written:
        print("  %-52s %d KB" % (os.path.relpath(p, ROOT), os.path.getsize(p) // 1024))
    from collections import Counter
    print("%d pages, %d redirect stubs, sitemap with %d urls"
          % (len(written), len(stubs), len(paths)))
    for t, n in Counter(t for _s, t in stubs).most_common():
        print("    %-28s %d" % (t, n))

if __name__ == '__main__':
    main()
