from pathlib import Path
import re
import json
import html as htmlmod
from collections import Counter

SITE = "https://simbacement.co.ke"
OG_IMAGE = f"{SITE}/images/simba-cement-og.jpg"
ROOT = Path(".")

def strip_tags(value):
    value = re.sub(r"<script\b.*?</script>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<style\b.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", htmlmod.unescape(value)).strip()

def attr(tag, name):
    m = re.search(rf"\b{name}\s*=\s*([\"'])(.*?)\1", tag, flags=re.I | re.S)
    return m.group(2) if m else ""

def replace_unsplash_images(text, filename):
    def img_repl(m):
        tag = m.group(0)
        src = attr(tag, "src")
        if "images.unsplash.com" not in src:
            return tag
        alt = attr(tag, "alt").lower()
        if "42.5" in alt or "42 5" in alt:
            local = "images/simba cement 42.5.jpeg"
        elif "32.5" in alt or "32 5" in alt:
            local = "images/simba cement 32.5.jpeg"
        elif filename == "products.html":
            local = "images/bag.jpg"
        else:
            local = "images/hero.jpeg"
        return re.sub(
            r"\bsrc\s*=\s*([\"']).*?\1",
            f'src="{local}"',
            tag,
            count=1,
            flags=re.I | re.S,
        )

    text = re.sub(r"<img\b[^>]*>", img_repl, text, flags=re.I | re.S)

    text = re.sub(
        r'(<meta\b[^>]*(?:property|name)\s*=\s*["\'](?:og:image(?::secure_url)?|twitter:image)["\'][^>]*content\s*=\s*["\'])https://images\.unsplash\.com/[^"\']+(["\'])',
        rf"\1{OG_IMAGE}\2",
        text,
        flags=re.I,
    )

    text = re.sub(
        r'(<link\b[^>]*rel\s*=\s*["\']preload["\'][^>]*href\s*=\s*["\'])https://images\.unsplash\.com/[^"\']+(["\'])',
        r"\1images/hero.jpeg\2",
        text,
        flags=re.I,
    )

    text = re.sub(
        r"url\(([\"']?)https://images\.unsplash\.com/[^)\"']+\1\)",
        "url('images/hero.jpeg')",
        text,
        flags=re.I,
    )

    text = re.sub(
        r"https://images\.unsplash\.com/[^\"'\s)>]+",
        "images/hero.jpeg",
        text,
        flags=re.I,
    )
    return text

def remove_sales_email(text):
    text = re.sub(
        r'<a\b[^>]*href\s*=\s*["\']mailto:sales@simbacement\.co\.ke["\'][^>]*>.*?</a>',
        "",
        text,
        flags=re.I | re.S,
    )
    text = re.sub(
        r"<strong>\s*Email\s*:\s*</strong>\s*(?:<br\s*/?>)?",
        "",
        text,
        flags=re.I,
    )
    text = re.sub(
        r'"email"\s*:\s*"sales@simbacement\.co\.ke"\s*,?',
        "",
        text,
        flags=re.I,
    )
    text = re.sub(r"\bsales@simbacement\.co\.ke\b", "", text, flags=re.I)
    return text

def ensure_basic_meta(text, filename):
    title_m = re.search(r"<title>(.*?)</title>", text, flags=re.I | re.S)
    h1_m = re.search(r"<h1\b[^>]*>(.*?)</h1>", text, flags=re.I | re.S)
    title = (
        strip_tags(title_m.group(1))
        if title_m
        else strip_tags(h1_m.group(1))
        if h1_m
        else "Simba Cement Kenya"
    )

    desc_m = re.search(
        r'<meta\b[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\'][^>]*>',
        text,
        flags=re.I | re.S,
    )
    desc = (
        strip_tags(desc_m.group(1))
        if desc_m
        else f"{title}. Simba Cement supply, product information, quotations and delivery support in Kenya."
    )

    url = SITE + ("/" if filename == "index.html" else "/" + filename)
    additions = []

    if not re.search(r'<link\b[^>]*rel=["\']canonical["\']', text, flags=re.I):
        additions.append(f'<link rel="canonical" href="{url}">')

    if not desc_m:
        additions.append(
            f'<meta name="description" content="{htmlmod.escape(desc, quote=True)}">'
        )

    if not re.search(r'<meta\b[^>]*property=["\']og:title["\']', text, flags=re.I):
        additions.append(
            f'<meta property="og:title" content="{htmlmod.escape(title, quote=True)}">'
        )

    if not re.search(
        r'<meta\b[^>]*property=["\']og:description["\']', text, flags=re.I
    ):
        additions.append(
            f'<meta property="og:description" content="{htmlmod.escape(desc, quote=True)}">'
        )

    if not re.search(r'<meta\b[^>]*property=["\']og:url["\']', text, flags=re.I):
        additions.append(f'<meta property="og:url" content="{url}">')

    if not re.search(r'<meta\b[^>]*property=["\']og:image["\']', text, flags=re.I):
        additions.extend(
            [
                f'<meta property="og:image" content="{OG_IMAGE}">',
                '<meta property="og:image:width" content="1200">',
                '<meta property="og:image:height" content="675">',
                '<meta property="og:image:alt" content="Simba Cement products and construction supply in Kenya">',
            ]
        )

    if additions:
        text = text.replace("</head>", "\n" + "\n".join(additions) + "\n</head>", 1)

    return text, title, desc, url

def ensure_schema(text, filename, title, desc, url):
    # Remove AggregateRating blocks instead of fabricating review/rating data.
    text = re.sub(
        r',?\s*"aggregateRating"\s*:\s*\{.*?\}(?=\s*[,}])',
        "",
        text,
        flags=re.I | re.S,
    )

    graph = [
        {
            "@type": "Organization",
            "@id": f"{SITE}/#organization",
            "name": "Simba Cement Kenya",
            "url": f"{SITE}/",
            "logo": {"@type": "ImageObject", "url": f"{SITE}/images/logo.jpeg"},
        },
        {
            "@type": "WebSite",
            "@id": f"{SITE}/#website",
            "url": f"{SITE}/",
            "name": "Simba Cement Kenya",
            "publisher": {"@id": f"{SITE}/#organization"},
            "inLanguage": "en-KE",
        },
    ]

    crumb_name = "Home" if filename == "index.html" else title.split("|")[0].strip()
    items = [
        {
            "@type": "ListItem",
            "position": 1,
            "name": "Home",
            "item": f"{SITE}/",
        }
    ]
    if filename != "index.html":
        items.append(
            {
                "@type": "ListItem",
                "position": 2,
                "name": crumb_name,
                "item": url,
            }
        )

    graph.append(
        {
            "@type": "BreadcrumbList",
            "@id": f"{url}#breadcrumb",
            "itemListElement": items,
        }
    )

    if filename == "products.html":
        graph.extend(
            [
                {
                    "@type": "Product",
                    "@id": f"{url}#simba-32-5r",
                    "name": "Simba Cement 32.5R PPC",
                    "description": "50kg Portland Pozzolana Cement for masonry, plastering, screeding and general construction.",
                    "image": f"{SITE}/images/simba%20cement%2032.5.jpeg",
                    "brand": {"@type": "Brand", "name": "Simba Cement"},
                    "category": "Portland Pozzolana Cement",
                    "sku": "SIMBA-32.5R-50KG",
                },
                {
                    "@type": "Product",
                    "@id": f"{url}#simba-42-5n",
                    "name": "Simba Cement 42.5N OPC",
                    "description": "50kg Ordinary Portland Cement for structural concrete, slabs, columns, beams and foundations.",
                    "image": f"{SITE}/images/simba%20cement%2042.5.jpeg",
                    "brand": {"@type": "Brand", "name": "Simba Cement"},
                    "category": "Ordinary Portland Cement",
                    "sku": "SIMBA-42.5N-50KG",
                },
            ]
        )

    if filename == "blog.html":
        graph.append(
            {
                "@type": "Blog",
                "@id": f"{url}#blog",
                "url": url,
                "name": title,
                "description": desc,
                "publisher": {"@id": f"{SITE}/#organization"},
                "inLanguage": "en-KE",
            }
        )
    elif re.search(r"<article\b", text, flags=re.I):
        graph.append(
            {
                "@type": "BlogPosting",
                "@id": f"{url}#article",
                "headline": title,
                "description": desc,
                "url": url,
                "mainEntityOfPage": url,
                "publisher": {"@id": f"{SITE}/#organization"},
                "image": OG_IMAGE,
                "inLanguage": "en-KE",
            }
        )

    if filename == "faq.html" and '"@type":"FAQPage"' not in text.replace(" ", ""):
        entities = []
        for m in re.finditer(
            r"<details\b[^>]*>\s*<summary\b[^>]*>(.*?)</summary>(.*?)</details>",
            text,
            flags=re.I | re.S,
        ):
            question = strip_tags(m.group(1))
            answer = strip_tags(m.group(2))
            if question and answer:
                entities.append(
                    {
                        "@type": "Question",
                        "name": question,
                        "acceptedAnswer": {"@type": "Answer", "text": answer},
                    }
                )
        if entities:
            graph.append(
                {
                    "@type": "FAQPage",
                    "@id": f"{url}#faq",
                    "mainEntity": entities[:20],
                }
            )

    marker = "production-schema-v1"
    if marker not in text:
        payload = {"@context": "https://schema.org", "@graph": graph}
        schema = (
            '\n<script type="application/ld+json" data-schema-source="production-schema-v1">\n'
            + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
            + "\n</script>\n"
        )
        text = text.replace("</head>", schema + "</head>", 1)

    return text

def harden_images_and_links(text, filename):
    image_index = 0

    def img_attrs(m):
        nonlocal image_index
        tag = m.group(0)
        image_index += 1

        if not re.search(r"\bdecoding=", tag, flags=re.I):
            tag = tag[:-1] + ' decoding="async">'

        if image_index == 1 and filename == "index.html":
            tag = re.sub(r'\sloading=["\']lazy["\']', "", tag, flags=re.I)
            if not re.search(r"\bfetchpriority=", tag, flags=re.I):
                tag = tag[:-1] + ' fetchpriority="high">'
        elif not re.search(r"\bloading=", tag, flags=re.I):
            tag = tag[:-1] + ' loading="lazy">'

        return tag

    text = re.sub(r"<img\b[^>]*>", img_attrs, text, flags=re.I | re.S)

    def ext_link(m):
        tag = m.group(0)
        href = attr(tag, "href")
        if (
            href.startswith("http")
            and re.search(r'target=["\']_blank["\']', tag, flags=re.I)
            and not re.search(r"\brel=", tag, flags=re.I)
        ):
            tag = tag[:-1] + ' rel="noopener noreferrer">'
        return tag

    return re.sub(r"<a\b[^>]*>", ext_link, text, flags=re.I | re.S)

def main():
    if not (ROOT / "index.html").exists():
        raise SystemExit("Run this script from the root of the simba-cement2 repository.")

    html_files = [p for p in ROOT.glob("*.html") if p.name != "404.html"]
    results = {}

    for p in html_files:
        text = p.read_text(encoding="utf-8")
        original = text

        # 1. Repair malformed meta tags that render a stray > at the top of pages.
        text = re.sub(r"(<meta\b[^>]*>)>", r"\1", text, flags=re.I | re.S)

        # 2. Remove the requested sales email from Contact.
        if p.name == "contact.html":
            text = remove_sales_email(text)

        # 3. Replace Unsplash stock imagery with repository assets.
        text = replace_unsplash_images(text, p.name)

        # 4. Ensure canonical/meta/Open Graph coverage.
        text, title, desc, url = ensure_basic_meta(text, p.name)

        # 5. Add structured data without fake AggregateRating.
        text = ensure_schema(text, p.name, title, desc, url)

        # 6. Add image/link performance and security attributes.
        text = harden_images_and_links(text, p.name)

        if text != original:
            p.write_text(text, encoding="utf-8")

        results[p.name] = (title, desc)

    # 7. Fix GitHub Pages PWA scope in both source and deployed JS.
    for jsname in ("app.js", "app.min.js"):
        p = ROOT / jsname
        if p.exists():
            text = p.read_text(encoding="utf-8")
            text = text.replace(
                "navigator.serviceWorker.register('/sw.js')",
                "navigator.serviceWorker.register('./sw.js')",
            )
            text = text.replace(
                'navigator.serviceWorker.register("/sw.js")',
                'navigator.serviceWorker.register("./sw.js")',
            )
            p.write_text(text, encoding="utf-8")

    # 8. Shared mobile/Core Web Vitals safeguards.
    css_addition = """
/* production-mobile-performance-v1 */
img{max-width:100%;height:auto}
a,button,.btn{touch-action:manipulation}
@media(max-width:768px){
  button,.btn,.menu a,input,select,textarea{min-height:44px}
  input,select,textarea{font-size:16px}
  body{overflow-x:hidden}
}
@media(prefers-reduced-motion:reduce){
  *,*::before,*::after{
    scroll-behavior:auto!important;
    animation-duration:.01ms!important;
    animation-iteration-count:1!important;
    transition-duration:.01ms!important
  }
}
"""
    for cssname in ("styles.css", "styles.min.css"):
        p = ROOT / cssname
        if p.exists():
            text = p.read_text(encoding="utf-8")
            if "production-mobile-performance-v1" not in text:
                p.write_text(text.rstrip() + "\n" + css_addition, encoding="utf-8")

    # 9. Audit internal .html links.
    existing = {p.name for p in ROOT.glob("*.html")}
    broken = []

    for p in ROOT.glob("*.html"):
        text = p.read_text(encoding="utf-8")
        for href in re.findall(r'href\s*=\s*["\']([^"\']+)["\']', text, flags=re.I):
            clean = href.split("#", 1)[0].split("?", 1)[0]
            if not clean or clean.startswith(
                ("http://", "https://", "mailto:", "tel:", "javascript:", "#", "/")
            ):
                continue
            if clean.endswith(".html") and Path(clean).name not in existing:
                broken.append((p.name, href))

    if broken:
        print("\nBroken internal HTML links found:")
        for src, href in broken:
            print(f"  {src} -> {href}")
        print("\nFix the links above before publishing.")
    else:
        print("\nInternal HTML link audit passed.")

    # 10. SEO duplicate audit.
    title_counts = Counter(v[0] for v in results.values() if v[0])
    desc_counts = Counter(v[1] for v in results.values() if v[1])

    duplicate_titles = [t for t, count in title_counts.items() if count > 1]
    duplicate_descs = [d for d, count in desc_counts.items() if count > 1]

    if duplicate_titles:
        print("\nDuplicate page titles still needing manual refinement:")
        for title in duplicate_titles:
            print(f"  {title}")
    else:
        print("Unique-title audit passed.")

    if duplicate_descs:
        print(f"\nDuplicate meta descriptions found: {len(duplicate_descs)}")
    else:
        print("Unique-description audit passed.")

    # 11. Final checks.
    checks = {
        "stray_meta_gt": False,
        "sales_email": False,
        "unsplash": False,
        "bad_sw_path": False,
    }

    for p in ROOT.glob("*.html"):
        text = p.read_text(encoding="utf-8")
        checks["stray_meta_gt"] |= bool(re.search(r"<meta[^>]*>>", text, flags=re.I))
        checks["sales_email"] |= "sales@simbacement.co.ke" in text.lower()
        checks["unsplash"] |= "images.unsplash.com" in text.lower()

    for jsname in ("app.js", "app.min.js"):
        p = ROOT / jsname
        if p.exists():
            checks["bad_sw_path"] |= "register('/sw.js')" in p.read_text(encoding="utf-8")

    failed = [name for name, value in checks.items() if value]
    if failed:
        raise SystemExit("Validation failed: " + ", ".join(failed))

    print("\nProduction fixes applied successfully.")
    print("Review git diff, test locally, then commit and push.")

if __name__ == "__main__":
    main()
