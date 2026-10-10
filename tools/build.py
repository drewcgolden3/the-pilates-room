#!/usr/bin/env python3
"""Build The Pilates Room.

    python3 tools/build.py                                   # production
    BASE=/the-pilates-room PREVIEW=1 python3 tools/build.py  # staging

Every fact on the site — address, hours, rates, credentials, FAQs — comes
from content/site.json and is rendered into BOTH the visible page and the
schema.org markup. They cannot drift apart, which is the thing local search
and the AI assistants actually reward.
"""
import html, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recipes as R

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(ROOT, 'content', 'site.json')))
RECIPES = json.load(open(os.path.join(ROOT, 'content', 'recipes-raw.json')))
RECIPES.sort(key=lambda r: r.get('date') or '', reverse=True)

BASE = os.environ.get('BASE', '').rstrip('/')
PREVIEW = os.environ.get('PREVIEW') == '1'

# Display face taken from her logo: the wordmark is geometric, Josefin Sans
# is its closest widely available match. Literata keeps body copy readable —
# Josefin has a very small x-height and is a display face, not a text face.
FONTS = ("https://fonts.googleapis.com/css2"
         "?family=Josefin+Sans:wght@400;500;600;700"
         "&family=Literata:opsz,wght@7..72,400;7..72,500&display=swap")

def e(s): return html.escape(str(s or ''), quote=True)
def addr(): return "%s, %s, %s %s" % (S['street'], S['city'], S['region'], S['zip'])

ARR = ('<svg width="14" height="10" viewBox="0 0 14 10" fill="none" aria-hidden="true">'
       '<path d="M8.6 1l4 4-4 4M12 5H1" stroke="currentColor" stroke-width="1.4" '
       'stroke-linecap="round" stroke-linejoin="round"/></svg>')

def rebase(doc):
    """Prefix root-absolute paths with BASE, once, over the finished document."""
    if not BASE:
        return doc
    doc = re.sub(r'(\b(?:href|src)=")(/(?!/))', r'\1' + BASE + r'\2', doc)
    doc = re.sub(r'(srcset=")([^"]+)(")',
                 lambda m: m.group(1) + re.sub(r'(^|,\s*)/', r'\1' + BASE + '/', m.group(2)) + m.group(3),
                 doc)
    return doc

def pic(name, alt, sizes, ratio='', prio=False, cls=''):
    return ('<img src="/assets/img/%s.jpg" srcset="/assets/img/%s@700.jpg 700w, /assets/img/%s.jpg 1400w" '
            'sizes="%s" alt="%s" width="1400" height="%s" %s decoding="async"%s>'
            % (name, name, name, sizes, e(alt), ratio or '1050',
               'fetchpriority="high"' if prio else 'loading="lazy"',
               ' class="%s"' % cls if cls else ''))

def rpic(slug, alt, sizes, prio=False):
    return ('<img src="/assets/img/recipes/%s.jpg" srcset="/assets/img/recipes/%s@560.jpg 560w, '
            '/assets/img/recipes/%s.jpg 1000w" sizes="%s" alt="%s" width="1000" height="750" '
            '%s decoding="async">'
            % (slug, slug, slug, sizes, e(alt), 'fetchpriority="high"' if prio else 'loading="lazy"'))

# ───────────────────────────────────────────────────────── schema
def biz():
    return {
        "@context": "https://schema.org", "@type": "HealthAndBeautyBusiness",
        "@id": S['url'] + "/#studio", "name": S['name'], "description": S['tagline'],
        "url": S['url'] + "/", "telephone": S['phoneRaw'], "email": S['email'],
        "priceRange": S['priceRange'],
        "image": S['url'] + "/assets/img/hands-on-springs.jpg",
        "logo": S['url'] + "/assets/img/logo.png",
        "foundingDate": str(S.get('studioSince', '')),
        "address": {"@type": "PostalAddress", "streetAddress": S['street'],
                    "addressLocality": S['city'], "addressRegion": S['region'],
                    "postalCode": S['zip'], "addressCountry": "US"},
        "geo": {"@type": "GeoCoordinates", "latitude": S['lat'], "longitude": S['lon']},
        "openingHoursSpecification": [{
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": ["https://schema.org/%s" % d for d in
                          ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]],
            "opens": o, "closes": c} for (_a, _b, o, c) in S['hoursSpec']],
        "sameAs": S['social'],
        "founder": {"@type": "Person", "name": S['instructor']},
        "employee": {"@type": "Person", "name": S['instructor'],
                     "jobTitle": "Certified Pilates Instructor"},
        "areaServed": [{"@type": "City", "name": n} for n in
                       ["Portsmouth", "Rye", "New Castle", "Greenland", "Newington", "Kittery", "York"]],
        "hasOfferCatalog": {"@type": "OfferCatalog", "name": "Pilates and movement services",
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

# ───────────────────────────────────────────────────────── chrome
def header(path):
    links = S['navLeft'] + [['/what-is-pilates/', 'What is Pilates']] + S['navRight']
    nav = ''.join('<a href="%s"%s>%s</a>' % (h, ' aria-current="page"' if h == path else '', e(l))
                  for h, l in links)
    mob = ''.join('<a href="%s">%s</a>' % (h, e(l)) for h, l in links)
    return ('<header class="hdr"><div class="shell hdr-in">'
            '<a class="hdr-logo" id="navLogoTarget" href="/" aria-label="%s — home">'
            '<img src="/assets/img/logo.png" width="158" height="84" alt="%s"></a>'
            '<nav aria-label="Primary">%s</nav>'
            '<div class="hdr-call"><a class="hdr-tel" href="tel:%s">%s</a>'
            '<a class="btn btn-pri" href="/book-an-appointment/">Book</a></div>'
            '<button class="burger" id="burger" aria-label="Menu" aria-expanded="false" '
            'aria-controls="mnav"><span></span></button>'
            '</div><div class="mnav" id="mnav"><div class="shell">%s'
            '<a href="tel:%s">Call %s</a></div></div></header>'
            % (e(S['name']), e(S['name']), nav, S['phoneRaw'], e(S['phone']),
               mob, S['phoneRaw'], e(S['phone'])))

def footer():
    links = S['navLeft'] + [['/what-is-pilates/', 'What is Pilates']] + S['navRight']
    nav = ''.join('<li><a href="%s">%s</a></li>' % (h, e(l)) for h, l in links)
    socials = ''.join('<li><a href="%s" rel="noopener">%s</a></li>'
                      % (u, 'Facebook' if 'facebook' in u else 'YouTube') for u in S['social'])
    return ('<footer class="ftr"><div class="shell">'
            '<div class="ftr-grid">'
            '<div><p class="ftr-name">%s</p>'
            '<p>%s<br>%s, %s %s</p>'
            '<p style="margin-top:10px">%s</p>'
            '<p style="margin-top:10px"><a href="tel:%s">%s</a><br><a href="mailto:%s">%s</a></p></div>'
            '<div><h4>Pages</h4><ul>%s</ul></div>'
            '<div><h4>Hours</h4><ul><li>%s</li><li>%s</li></ul>'
            '<h4 style="margin-top:22px">Follow</h4><ul>%s</ul></div>'
            '</div>'
            '<div class="ftr-btm"><span>&copy; 2026 %s. Teaching on the Seacoast since %s.</span>'
            '<span>Site by <a href="https://theswitchboardcompany.com">The Switchboard Company</a></span>'
            '</div></div></footer>'
            % (e(S['name']), e(S['street']), e(S['city']), e(S['region']), e(S['zip']),
               e(S['parking']), S['phoneRaw'], e(S['phone']), S['email'], e(S['email']),
               nav, e(S['hours']), 'Appointment only', socials,
               e(S['name']), S.get('teachingSince', 2008)))

def shell(path, title, desc, body, schema=None, preload=None, body_class=''):
    blocks = ''.join('\n<script type="application/ld+json">%s</script>'
                     % json.dumps(s, separators=(',', ':')) for s in (schema or []))
    canon = S['url'] + path
    noindex = '\n<meta name="robots" content="noindex,nofollow">' if PREVIEW else ''
    pre = ('\n<link rel="preload" as="image" href="/assets/img/%s.jpg" '
           'imagesrcset="/assets/img/%s@700.jpg 700w, /assets/img/%s.jpg 1400w">'
           % (preload, preload, preload)) if preload else ''
    return ('<!DOCTYPE html>\n<html lang="en">\n<head>\n'
            '<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>%s</title>\n<meta name="description" content="%s">\n'
            '<link rel="canonical" href="%s">%s\n'
            '<meta property="og:type" content="website">\n'
            '<meta property="og:title" content="%s">\n'
            '<meta property="og:description" content="%s">\n'
            '<meta property="og:url" content="%s">\n'
            '<meta property="og:image" content="%s/assets/img/hands-on-springs.jpg">\n'
            '<meta property="og:locale" content="en_US">\n'
            '<meta name="twitter:card" content="summary_large_image">\n'
            '<meta name="theme-color" content="#FBF8F4">\n'
            '<link rel="icon" href="/assets/img/logo.png">\n'
            '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            '<link rel="stylesheet" href="%s">\n'
            '<link rel="stylesheet" href="/assets/site.css">%s%s\n'
            '</head>\n<body%s>\n%s\n<main id="main">\n%s\n</main>\n%s\n'
            '<script src="/assets/site.js" defer></script>\n</body>\n</html>\n'
            % (e(title), e(desc), canon, noindex, e(title), e(desc), canon, S['url'],
               FONTS, pre, blocks,
               ' class="%s"' % body_class if body_class else '',
               header(path), body, footer()))

def write(path, text):
    text = rebase(text)
    out = (os.path.join(ROOT, 'index.html') if path == '/'
           else os.path.join(ROOT, path.strip('/'), 'index.html'))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8').write(text)
    return out

# ───────────────────────────────────────────────────────── blocks
def cta(title, lede, pale=True):
    return ('<section class="band on-blue"><div class="shell cta-in">'
            '<div><span class="label">Get started</span>'
            '<h2 class="d2" style="margin-top:12px">%s</h2>'
            '<p class="lede" style="margin-top:16px">%s</p></div>'
            '<div class="cta-acts"><a class="btn %s" href="tel:%s">Call %s%s</a>'
            '<a class="btn btn-ghost-l" href="/book-an-appointment/">How booking works</a></div>'
            '</div></section>'
            % (e(title), e(lede), 'btn-pale' if pale else 'btn-pri',
               S['phoneRaw'], e(S['phone']), ARR))

def visit():
    rows = [("Address", "%s<br>%s, %s %s" % (e(S['street']), e(S['city']), e(S['region']), e(S['zip']))),
            ("Parking", e(S['parking'])),
            ("Phone", '<a href="tel:%s">%s</a>' % (S['phoneRaw'], e(S['phone']))),
            ("Email", '<a href="mailto:%s">%s</a>' % (S['email'], e(S['email']))),
            ("Hours", e(S['hours']))]
    dl = ''.join('<div class="vr"><dt>%s</dt><dd>%s</dd></div>' % (k, v) for k, v in rows)
    return ('<section class="band" id="visit"><div class="shell visit">'
            '<div><span class="label">Visit</span>'
            '<h2 class="d2" style="margin:12px 0 22px">Downtown Portsmouth.</h2>'
            '<dl class="vlist">%s</dl></div>'
            '<div class="map"><iframe src="https://www.google.com/maps?q=%s+%s+%s+%s&output=embed" '
            'loading="lazy" title="Map to %s"></iframe></div>'
            '</div></section>'
            % (dl, S['street'].replace(' ', '+'), S['city'], S['region'], S['zip'], e(addr())))

# ───────────────────────────────────────────────────────── pages
def page_home():
    slides = ''.join(
        '<figure%s><img src="/assets/img/%s.jpg" srcset="/assets/img/%s@700.jpg 700w, '
        '/assets/img/%s.jpg 1400w" sizes="(max-width:1040px) 100vw, 50vw" alt="%s" %s decoding="async">'
        '</figure>' % (' class="on"' if i == 0 else '', n, n, n, e(alt),
                       'fetchpriority="high"' if i == 0 else 'loading="lazy"')
        for i, (n, alt) in enumerate(S['hero']))
    dots = ('' if len(S['hero']) < 2 else
            '<div class="hero-dots" id="heroDots" role="group" aria-label="Choose photograph">'
            + ''.join('<button type="button" aria-label="Show photograph %d" aria-current="%s"></button>'
                      % (i + 1, 'true' if i == 0 else 'false') for i in range(len(S['hero'])))
            + '</div>')

    rail = ''.join('<div><p class="k">%s</p><p class="v">%s</p></div>' % (k, v) for k, v in [
        ("One to one, or two", "No class floor and no crowded schedule."),
        ("Reformer, Cadillac, chair, barrel", "A fully equipped studio, not a mat in a corner."),
        ("Teaching since %s" % S.get('teachingSince', 2008),
         "In the Seacoast studio since %s." % S.get('studioSince', 2013))])

    rows = ''
    for s in S['services'][:3]:
        fig = ('<span class="fig">$%s<small>per %s</small></span>' % (s['price'], s['unit'])
               if s['price'] else '<span class="fig" style="font-size:.95rem">Ask</span>')
        rows += ('<div class="row"><h3 class="d3">%s</h3><p>%s</p>%s</div>'
                 % (e(s['name']), e(s['desc']), fig))

    conds = ''.join('<div><dt>%s</dt><dd>%s</dd></div>' % (e(t), e(d)) for t, d in S['conditions'])
    faqs = ''.join('<details><summary>%s</summary><p>%s</p></details>' % (e(q), e(a))
                   for q, a in S['faqs'][:5])

    body = (
    # Full-bleed hero, Bayshore-style: photography behind, her logo over it.
    # The logo stays in full colour — a white knockout collapses the lotus
    # into a solid blob, because its petals are separated by colour, not alpha.
    '<section class="hero" id="heroSlides">'
    '<div class="hero-bg">%s</div>'
    '<div class="shell hero-inner">'
    '<p class="hero-eyebrow">Portsmouth, New Hampshire &nbsp;·&nbsp; Since %s</p>'
    '<h1 class="hero-mark"><span class="hero-logo-slot">'
    '<span class="hero-logo" id="heroLogo">'
    '<img src="/assets/img/logo.png" width="597" height="316" alt="%s" fetchpriority="high">'
    '</span></span></h1>'
    '<p class="hero-tag">Feel the difference in one session.</p>'
    '<p class="hero-sub">A private studio on High Street, and an hour that is entirely yours. '
    'Book a class with instructor %s one-on-one, or with a partner.</p>'
    '<div class="hero-acts"><a class="btn btn-sky" href="/book-an-appointment/">Book now</a>'
    '<a class="btn btn-ghost-l" href="/rates-and-services/">Rates &amp; services</a></div>'
    '<p class="hero-foot">%s &nbsp;·&nbsp; Free parking behind the building &nbsp;·&nbsp; '
    'Monday to Friday, by appointment</p>'
    '%s'
    '</div></section>'

    '<section class="rail"><div class="shell rail-in">%s</div></section>'

    # the approach
    '<section class="band"><div class="shell duo duo-wide">'
    '<div><span class="label">The studio</span>'
    '<h2 class="d2" style="margin:14px 0 20px">Nothing here is a routine you follow.</h2>'
    '<p class="lede">Because every session is private, Michele can watch how you actually move, '
    'build the work around it, and change it the moment it needs changing. A back that complains '
    'after a round of golf and a body six weeks after a C-section do not need the same hour.</p>'
    '<p class="lede" style="margin-top:16px">On the reformer, spring tension does the work that '
    'weights normally would. You can load a muscle hard without loading a knee, a hip or a spine '
    'the same way — which is why it suits bodies that cannot simply go and lift heavier.</p>'
    '<p style="margin-top:26px"><a class="ln-b" href="/what-is-pilates/">What Pilates actually does%s</a></p>'
    '</div>'
    '<figure class="ratio-45">%s</figure></div></section>'

    # services as an editorial list
    '<section class="band on-sand"><div class="shell">'
    '<div class="sec-head"><span class="label">Sessions</span>'
    '<h2 class="d2">Three ways to work together.</h2>'
    '<p class="lede">Everything is by appointment, Monday to Friday. Reformer work is the core of '
    'the studio; mat, yoga and nutrition round it out.</p></div>'
    '<div class="list">%s</div>'
    '<p style="margin-top:30px"><a class="ln-b" href="/rates-and-services/">All rates and services%s</a></p>'
    '</div></section>'

    # who it is for
    '<section class="band"><div class="shell">'
    '<div class="sec-head"><span class="label">Who it is for</span>'
    '<h2 class="d2">Most people here are working around something.</h2></div>'
    '<dl class="cond">%s</dl></div></section>'

    # a wide banner frame of Michele teaching — her best photograph, and only
    # 1733x684, so it is given the full width its crop was made for
    '<figure class="bleed"><img src="/assets/img/michele-barre.jpg" '
    'srcset="/assets/img/michele-barre@700.jpg 850w, /assets/img/michele-barre.jpg 1700w" '
    'sizes="100vw" alt="Michele McCauley teaching at the barre in the studio" '
    'width="1700" height="671" loading="lazy" decoding="async">'
    '<figcaption>In the studio on High Street.</figcaption></figure>'

    # michele
    '<section class="band on-sand"><div class="shell duo duo-flip">'
    '<figure class="ratio-45">%s</figure>'
    '<div><span class="label">Your instructor</span>'
    '<h2 class="d2" style="margin:14px 0 20px">%s</h2>'
    '<p class="lede">Michele studied under Kathy Van Patten at the Movement Center of Boston, and '
    'trained for her 200-hour yoga certification at the Nosara Yoga Institute in Costa Rica. She is '
    'a triathlete, a surfer, a dancer and a culinary school graduate — which is how nutrition, and '
    'eventually a recipe blog, ended up part of the studio.</p>'
    '<p style="margin-top:26px"><a class="ln-b" href="/about-the-pilates-room/">More about Michele%s</a></p>'
    '</div></div></section>'

    # faq
    '<section class="band"><div class="shell">'
    '<div class="sec-head"><h2 class="d2">Before you call.</h2></div>'
    '<div class="faq">%s</div>'
    '<p style="margin-top:28px" class="body-sm">More questions are answered on '
    '<a class="ln" href="/book-an-appointment/" style="color:var(--blue)">the booking page</a>.</p>'
    '</div></section>'

    % (slides, S.get('studioSince', 2013), e(S['name']), e(S['instructor']),
       e(addr()), dots, rail, ARR,
       pic('hands-on-springs', 'Michele guiding a client through springwork on the reformer',
           '(max-width:1040px) 100vw, 42vw'),
       rows, ARR, conds,
       pic('michele-portrait', '%s at The Pilates Room' % S['instructor'],
           '(max-width:1040px) 100vw, 46vw'),
       e(S['instructor']), ARR, faqs)
    ) + cta("Start with a free consultation.",
            "Thirty minutes, no charge, and nothing to buy at the end of it.") + visit()

    return shell('/', "%s | %s" % (S['name'], S['tagline']),
        "Private and semi-private Reformer Pilates with %s at %s. Back pain, rehabilitation, "
        "pre and postnatal, active aging. Free 30-minute consultation — call %s."
        % (S['instructor'], addr(), S['phone']),
        body, schema=[biz(), faq_schema()], preload=S['hero'][0][0], body_class='home')


def page_rates():
    ladders = ''
    for name, rows in S['rates'].items():
        items = ''.join('<div class="lr%s"><dt>%s</dt><dd>$%s</dd></div>'
                        % (' lr-key' if i == 2 else '', e(q), v) for i, (q, v) in enumerate(rows))
        per = rows[-1][1] / 10
        sub = ("One to one, by appointment" if name.startswith("Private")
               else "Two people, priced per person")
        ladders += ('<div class="ladder"><h3 class="d3">%s</h3><p class="sub">%s</p>'
                    '<dl>%s</dl><p class="note">Works out to $%g a session at ten.</p></div>'
                    % (e(name), sub, items, per))

    others = ''.join('<div class="row"><h3 class="d3">%s</h3><p>%s</p>'
                     '<span class="fig" style="font-size:.95rem">Ask</span></div>'
                     % (e(s['name']), e(s['desc'])) for s in S['services'][2:])

    body = ('<section class="band-tight"><div class="shell">'
            '<div class="sec-head"><span class="label">Rates &amp; services</span>'
            '<h1 class="d1">What a session costs.</h1>'
            '<p class="lede">Every new client starts with a free thirty-minute consultation, so you '
            'can decide whether it is right for you before you buy anything. Most people then begin '
            'with a package of five.</p></div>'
            '<div class="ladders">%s</div>'
            '<p class="body-sm" style="margin-top:28px;max-width:60ch">Sessions run Monday to Friday '
            'by appointment. A 24-hour cancellation policy applies.</p>'
            '</div></section>'
            '<section class="band on-sand"><div class="shell">'
            '<div class="sec-head"><h2 class="d2">Also offered.</h2>'
            '<p class="lede">Alongside reformer work, and usually built into the same programme '
            'rather than booked separately.</p></div>'
            '<div class="list">%s</div></div></section>' % (ladders, others))

    return shell('/rates-and-services/', "Rates &amp; Services | %s" % S['name'],
        "Private Reformer Pilates from $85 and semi-private from $45 per person at %s, %s. "
        "Mat Pilates, yoga and fitness nutrition. Free 30-minute consultation."
        % (S['name'], addr()),
        body + cta("Not sure which to book?",
                   "Call and talk it through. The consultation is free and there is no obligation.")
        + visit(), schema=[biz()])


def page_book():
    steps = ''.join('<li><span class="n">%02d</span><div><h3 class="d3">%s</h3><p>%s</p></div></li>'
                    % (i + 1, e(t), e(d)) for i, (t, d) in enumerate(S['bookSteps']))
    faqs = ''.join('<details><summary>%s</summary><p>%s</p></details>' % (e(q), e(a))
                   for q, a in S['faqs'])
    body = ('<section class="band-tight"><div class="shell duo duo-wide">'
            '<div><span class="label">Book an appointment</span>'
            '<h1 class="d1" style="margin:14px 0 20px">Booking is a phone call.</h1>'
            '<p class="lede">There is no online calendar, and that is deliberate. Michele would '
            'rather hear what is going on with your body before she puts you on a reformer.</p>'
            '<div class="acts"><a class="btn btn-pri" href="tel:%s">Call %s%s</a>'
            '<a class="ln-b" href="mailto:%s">Or email the studio%s</a></div>'
            '<p class="fine">If she is teaching, leave a message with a number and she will '
            'call you back.</p></div>'
            '<figure class="ratio-32">%s</figure></div></section>'
            '<section class="band on-sand"><div class="shell">'
            '<div class="sec-head"><h2 class="d2">What happens next.</h2></div>'
            '<ol class="steps">%s</ol></div></section>'
            '<section class="band"><div class="shell">'
            '<div class="sec-head"><h2 class="d2">Questions people ask first.</h2></div>'
            '<div class="faq">%s</div></div></section>'
            % (S['phoneRaw'], e(S['phone']), ARR, S['email'], ARR,
               pic('semi-private', 'A semi-private session on the reformers',
                   '(max-width:1040px) 100vw, 42vw'),
               steps, faqs))
    return shell('/book-an-appointment/', "Book an Appointment | %s" % S['name'],
        "Booking at %s is by phone. Call %s to arrange a free 30-minute consultation with %s in %s, %s."
        % (S['name'], S['phone'], S['instructor'], S['city'], S['region']),
        body + visit(), schema=[biz(), faq_schema()])


def page_about():
    creds = ''.join('<div class="cr"><dt>%s</dt><dd>%s</dd></div>' % (e(a), e(b))
                    for a, b in S['credentials'])
    body = ('<section class="band-tight"><div class="shell duo">'
            '<div><span class="label">About</span>'
            '<h1 class="d1" style="margin:14px 0 20px">%s</h1>'
            '<p class="lede">Michele has taught Pilates since %s, and has run The Pilates Room in '
            'downtown Portsmouth since %s. She studied under Kathy Van Patten at the Movement Center '
            'of Boston, who she still calls her mentor, and trained for her 200-hour yoga '
            'certification at the Nosara Yoga Institute in Costa Rica.</p>'
            '<p class="lede" style="margin-top:16px">Her background runs through muscle anatomy, '
            'movement and the body&ndash;mind connection, and through triathlon training, running, '
            'cycling, swimming, dancing and surfing. She is also a Johnson &amp; Wales culinary '
            'graduate, which is how nutrition — and eventually the recipe blog — became part of the '
            'studio.</p>'
            '<p class="lede" style="margin-top:16px">What that adds up to in a session is someone who '
            'can watch how you move, work out why it hurts, and know which piece of apparatus will '
            'help.</p></div>'
            '<figure class="ratio-45">%s</figure></div></section>'
            '<section class="band on-sand"><div class="shell duo duo-wide">'
            '<div><span class="label">Training</span>'
            '<h2 class="d2" style="margin:14px 0 22px">Certifications.</h2>'
            '<dl class="creds">%s</dl>'
            '<p class="body-sm" style="margin-top:20px">Johnson &amp; Wales University, culinary '
            'graduate (A.A.S.) &nbsp;·&nbsp; Southern New Hampshire University, B.S. Accounting '
            '&amp; Finance</p></div>'
            '<figure class="ratio-45">%s</figure></div></section>'
            % (e(S['instructor']), S.get('teachingSince', 2008), S.get('studioSince', 2013),
               pic('michele-portrait', '%s at The Pilates Room' % S['instructor'],
                   '(max-width:1040px) 100vw, 46vw', prio=True),
               creds,
               pic('michele-plank', '%s demonstrating a side plank' % S['instructor'],
                   '(max-width:1040px) 100vw, 38vw')))
    return shell('/about-the-pilates-room/', "About %s | %s" % (S['instructor'], S['name']),
        "%s is a certified Pilates instructor (mat, reformer, chair and barrel), ISSA personal "
        "trainer and fitness nutrition specialist, teaching in Portsmouth NH since %s."
        % (S['instructor'], S.get('studioSince', 2013)),
        body + cta("Come and meet her first.",
                   "The consultation is free and there is nothing to buy at the end of it.") + visit(),
        schema=[biz(), {"@context": "https://schema.org", "@type": "Person",
                        "name": S['instructor'], "jobTitle": "Certified Pilates Instructor",
                        "worksFor": {"@id": S['url'] + "/#studio"},
                        "alumniOf": ["Nosara Yoga Institute", "Johnson & Wales University",
                                     "Southern New Hampshire University"],
                        "knowsAbout": ["Pilates", "Reformer Pilates", "Yoga", "Fitness nutrition",
                                       "Prenatal and postnatal exercise", "Active aging"]}],
        preload='michele-portrait')


def page_pilates():
    P = S['pilates']
    secs = ''.join('<section class="gsec" id="s%d"><h2 class="d3">%s</h2><p>%s</p></section>'
                   % (i, e(h), e(b)) for i, (h, b) in enumerate(P['sections']))
    toc = ''.join('<a href="#s%d">%s</a>' % (i, e(h)) for i, (h, _b) in enumerate(P['sections']))
    body = ('<section class="band-tight"><div class="shell">'
            '<div class="sec-head"><span class="label">What is Pilates</span>'
            '<h1 class="d1">Strength without the pounding.</h1>'
            '<p class="lede">%s</p></div>'
            '<div class="guide"><nav class="gtoc" aria-label="On this page">%s</nav>'
            '<div>%s</div></div></div></section>' % (e(P['intro']), toc, secs))
    return shell('/what-is-pilates/', "What is Pilates, and what is it good for? | %s" % S['name'],
        "How Reformer Pilates builds strength without loading your joints — and what it does for "
        "back and SI joint pain, scoliosis, active aging, athletes, and pre and postnatal recovery.",
        body + cta("Still not sure it is for you?",
                   "That is exactly what the free consultation is for."),
        schema=[biz(), {"@context": "https://schema.org", "@type": "Article",
                        "headline": "What is Pilates, and what is it good for?",
                        "about": "Reformer Pilates",
                        "author": {"@type": "Person", "name": S['instructor']},
                        "publisher": {"@id": S['url'] + "/#studio"},
                        "articleSection": [h for h, _b in P['sections']]}])

# ───────────────────────────────────────────────────────── recipes
def recipe_times(rec):
    out = []
    for label, field in (("Prep", "prep_time"), ("Cook", "cook_time")):
        v = R.mins(rec.get(field))
        if v: out.append((label, v))
    cl, cv = rec.get('custom_time_label') or '', R.mins(rec.get('custom_time'))
    if cv and cl: out.append((cl, cv))
    tv = R.mins(rec.get('total_time'))
    if tv: out.append(("Total", tv))
    if rec.get('servings'):
        out.append(("Serves", ("%s %s" % (rec['servings'], rec.get('servings_unit') or '')).strip()))
    return out

def page_recipe(r):
    rec, slug = r['recipe'], r['slug']
    title = R.strip_tags(r['title']['rendered'])
    summary = R.strip_tags(rec.get('summary'))
    facts = ''.join('<div><dt>%s</dt><dd>%s</dd></div>' % (e(l), e(v)) for l, v in recipe_times(rec))
    tags = R.taxa(rec, 'course') + R.taxa(rec, 'cuisine')

    ings = ''
    for kind, amt, name, note in R.parse_ingredients(rec):
        if kind == 'heading':
            ings += '<li class="gh">%s</li>' % e(amt or name)
        else:
            ings += ('<li>%s%s%s</li>' % ('<b>%s</b> ' % e(amt) if amt else '', e(name),
                                          ' <i>%s</i>' % e(note) if note else ''))
    steps, n = '', 0
    for kind, text in R.parse_steps(rec):
        if kind == 'heading':
            steps += '<li class="gh">%s</li>' % e(text)
        else:
            n += 1
            steps += '<li><span class="sn">%02d</span><p>%s</p></li>' % (n, e(text))

    notes = R.strip_tags(rec.get('notes'))
    body = ('<article class="shell article">'
            '<a class="crumb" href="/the-culinary-greenhouse/">&larr;&nbsp; The Culinary Greenhouse</a>'
            '<div class="r-head"><div><h1 class="d2">%s</h1>%s%s</div>'
            '<figure>%s</figure></div>'
            '%s'
            '<div class="r-body">'
            '<div class="r-ings"><h2 class="d3">Ingredients</h2><ul>%s</ul></div>'
            '<div class="r-steps"><h2 class="d3">Method</h2><ol>%s</ol>%s</div>'
            '</div></article>'
            % (e(title),
               ('<p class="lede" style="margin-top:14px">%s</p>' % e(summary)
                if summary and summary.strip().lower() != title.strip().lower() else ''),
               '<p class="meta" style="margin-top:16px">%s</p>' % e(' · '.join(tags)) if tags else '',
               rpic(slug, title, '(max-width:1040px) 100vw, 50vw', prio=True),
               '<dl class="r-facts">%s</dl>' % facts if facts else '',
               ings, steps,
               '<div class="r-note">%s</div>' % e(notes) if notes else ''))
    desc = summary or ("%s — a recipe from The Culinary Greenhouse at %s." % (title, S['name']))
    return shell('/the-culinary-greenhouse/%s/' % slug,
                 "%s | The Culinary Greenhouse" % title, desc[:300],
                 body + cta("Pilates, as well as the cooking.",
                            "Private and semi-private reformer sessions in downtown Portsmouth."),
                 schema=[R.recipe_schema(r, S, "%s/assets/img/recipes/%s.jpg" % (S['url'], slug)), biz()])

def page_recipe_index():
    cards = ''
    for r in RECIPES:
        rec, slug = r['recipe'], r['slug']
        title = R.strip_tags(r['title']['rendered'])
        summary = R.strip_tags(rec.get('summary'))
        t = R.mins(rec.get('total_time'))
        cards += ('<a class="rcard" href="/the-culinary-greenhouse/%s/">'
                  '<figure>%s</figure><div><h3 class="d3">%s</h3>%s%s</div></a>'
                  % (slug, rpic(slug, title, '(max-width:760px) 100vw, (max-width:1040px) 50vw, 33vw'),
                     e(title),
                     ('<p style="margin-top:7px">%s</p>' % e(summary)
                      if summary and summary.strip().lower() != title.strip().lower() else ''),
                     '<p class="meta">%s total</p>' % e(t) if t else ''))
    body = ('<section class="band-tight"><div class="shell">'
            '<div class="sec-head" style="max-width:40rem"><span class="label">The Culinary Greenhouse</span>'
            '<h1 class="d1">What Michele cooks.</h1>'
            '<p class="lede">She is a Johnson &amp; Wales culinary graduate and an ISSA fitness '
            'nutrition specialist, so the food side of the studio is not an afterthought. These are '
            'the recipes she actually makes.</p></div>'
            '<div class="rgrid">%s</div></div></section>' % cards)
    return shell('/the-culinary-greenhouse/', "The Culinary Greenhouse | %s" % S['name'],
        "Recipes from %s, a Johnson & Wales culinary graduate and ISSA fitness nutrition "
        "specialist at %s in %s, %s." % (S['instructor'], S['name'], S['city'], S['region']),
        body + cta("The studio side of things.",
                   "Private and semi-private Reformer Pilates, by appointment."),
        schema=[biz(), {"@context": "https://schema.org", "@type": "CollectionPage",
                        "name": "The Culinary Greenhouse", "isPartOf": {"@id": S['url'] + "/#studio"},
                        "hasPart": [{"@type": "Recipe", "name": R.strip_tags(r['title']['rendered']),
                                     "url": "%s/the-culinary-greenhouse/%s/" % (S['url'], r['slug'])}
                                    for r in RECIPES]}])

PAGES = [page_home, page_rates, page_book, page_about, page_pilates, page_recipe_index]

# ───────────────────────────────────────────────────────── redirects
def redirect_stub(target, title):
    return ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            '<title>%s</title><link rel="canonical" href="%s%s">'
            '<meta name="robots" content="noindex,follow">'
            '<meta http-equiv="refresh" content="0; url=%s">'
            '<script>location.replace("%s")</script></head>'
            '<body><p>This page has moved. <a href="%s">Continue</a>.</p></body></html>'
            % (e(title), S['url'], target, target, target, target))

def build_redirects():
    src = os.path.join(ROOT, 'content', 'posts-raw.json')
    if not os.path.exists(src):
        return []
    posts = json.load(open(src))
    live = {r['slug'] for r in RECIPES}
    EXPLICIT = {'rates-services': '/rates-and-services/',
                'beach-yoga-booking-groups-now': '/rates-and-services/',
                'beach-yoga-is-simply-blissful': '/rates-and-services/',
                'sound-healing-workshop': '/', '832-2': '/'}
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
            target = '/'
        out.append((slug, target))
        write('/%s/' % slug, redirect_stub(target, title))
    return out

def sitemap(paths):
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>'
            % ''.join('<url><loc>%s%s</loc></url>' % (S['url'], p) for p in paths))

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
    print("%d pages, %d redirect stubs, sitemap with %d urls"
          % (len(written), len(stubs), len(paths)))

if __name__ == '__main__':
    main()
