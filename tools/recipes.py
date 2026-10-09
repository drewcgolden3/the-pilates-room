"""Recipe pages for The Culinary Greenhouse.

Her WP Recipe Maker data comes through in two different shapes. Most recipes
put each step in instructions[].text; a few have the whole step typed into the
GROUP heading with no steps under it. parse_steps() handles both, so nothing
has to be re-entered by hand.
"""
import html, json, os, re

def e(s): return html.escape(str(s or ''), quote=True)

def strip_tags(s):
    # unescape AFTER stripping tags: WP stores titles like "8&#215;8", and if the
    # entity survives it gets escaped again on output and shows as literal text
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s or ''))).strip()

def parse_steps(rec):
    """-> [('heading', text) | ('step', text)] covering both data shapes."""
    out = []
    for item in rec.get('instructions_flat') or []:
        if item.get('type') == 'instruction':
            t = strip_tags(item.get('text'))
            if t: out.append(('step', t))
        elif item.get('type') == 'group':
            name = strip_tags(item.get('name'))
            if not name: continue
            # a long "group name" is really a step she typed into the heading
            out.append(('step' if len(name) > 60 else 'heading', name))
    return out

def parse_ingredients(rec):
    out = []
    for item in rec.get('ingredients_flat') or []:
        if item.get('type') == 'group':
            n = strip_tags(item.get('name'))
            if n: out.append(('heading', n, '', ''))
        else:
            amount = strip_tags(item.get('amount'))
            unit = strip_tags(item.get('unit'))
            name = strip_tags(item.get('name'))
            notes = strip_tags(item.get('notes'))
            if name: out.append(('item', f"{amount} {unit}".strip(), name, notes))
    return out

def mins(v):
    try: v = int(float(v or 0))
    except (TypeError, ValueError): return None
    if not v: return None
    if v < 60: return f"{v} min"
    h, m = divmod(v, 60)
    return f"{h} hr" + (f" {m} min" if m else "")

def taxa(rec, key):
    return [t.get('name') for t in (rec.get('tags') or {}).get(key, []) if t.get('name')]

def iso_dur(v):
    try: v = int(float(v or 0))
    except (TypeError, ValueError): return None
    if not v: return None
    h, m = divmod(v, 60)
    return "PT" + (f"{h}H" if h else "") + (f"{m}M" if m else "")

def recipe_schema(r, site, img_url):
    rec = r['recipe']
    steps = [t for kind, t in parse_steps(rec) if kind == 'step']
    ings = [f"{a} {n}".strip() + (f", {o}" if o else "")
            for kind, a, n, o in parse_ingredients(rec) if kind == 'item']
    d = {"@context": "https://schema.org", "@type": "Recipe",
         "name": strip_tags(r['title']['rendered']),
         "description": strip_tags(rec.get('summary')),
         "image": img_url,
         "datePublished": (r.get('date') or '')[:10],
         "author": {"@type": "Person", "name": site['instructor']},
         "publisher": {"@id": site['url'] + "/#studio"},
         "recipeIngredient": ings,
         "recipeInstructions": [{"@type": "HowToStep", "text": s} for s in steps]}
    if rec.get('servings'): d["recipeYield"] = f"{rec['servings']} {rec.get('servings_unit') or 'servings'}".strip()
    for k, f in (("prepTime", "prep_time"), ("cookTime", "cook_time"), ("totalTime", "total_time")):
        v = iso_dur(rec.get(f))
        if v: d[k] = v
    c = taxa(rec, 'course'); u = taxa(rec, 'cuisine')
    if c: d["recipeCategory"] = c
    if u: d["recipeCuisine"] = u
    return {k: v for k, v in d.items() if v}
