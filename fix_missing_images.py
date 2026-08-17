from pathlib import Path
import re
import unicodedata
from difflib import SequenceMatcher

ROOT = Path(".")
IMG_DIR = ROOT / "images"

if not (ROOT / "index.html").exists():
    raise SystemExit("Run this script from the root of the simba-cement2 project.")
if not IMG_DIR.exists():
    raise SystemExit("The images folder was not found.")

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif", ".svg"}

def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = s.lower()
    s = s.replace("42.5n", "425n").replace("42.5r", "425r").replace("32.5r", "325r")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())

def tokens(s):
    stop = {
        "a","an","and","for","the","to","in","of","on","is","with","guide",
        "kenya","simba","cement","image","infographic","applications"
    }
    return {x for x in norm(s).split() if x not in stop}

images = [p for p in IMG_DIR.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
by_lower = {p.name.lower(): p for p in images}
by_stem = {}
for p in images:
    by_stem.setdefault(p.stem.lower(), []).append(p)

# Exact mappings for the new guide graphics.
BLOG_MAP = {
    "simba cement 32.5r vs 42.5n": [
        "32.5r vs 42.5n.png",
    ],
    "best cement for house construction in kenya": [
        "Best Cement for House Construction in Kenya.png",
    ],
    "best cement for foundations in kenya": [
        "Best Cement for Foundations in Kenya.png",
        "Best Cement for Foundations Kenya.png",
        "Cement Foundation Planning Guide.png",
    ],
    "which cement is best for plastering?": [
        "Which Cement Is Best for Plastering.png",
        "Best Cement for Plastering.png",
    ],
    "which cement is best for masonry?": [
        "Which Cement Is Best for Masonry.png",
        "Best Cement for Masonry.png",
    ],
    "how many cement bags do i need for a house?": [
        "How Many Cement Bags Do I Need for a House.png",
        "Cement Bag Calculation House Guide.png",
    ],
    "how many cement bags do i need for a foundation?": [
        "How Many Cement Bags Do I Need for a Foundation.png",
        "Cement Foundation Planning Guide.png",
    ],
    "how to store cement properly": [
        "How to Store Cement Properly.png",
        "Cement Storage Guide.png",
    ],
    "how long can cement be stored?": [
        "How Long Can Cement Be Stored.png",
        "Cement Storage Guide.png",
    ],
    "cement for columns and beams": [
        "Cement for Columns and Beams.png",
        "Cement Guide for Strong Structures.png",
    ],
    "cement for block making": [
        "Cement for Block Making.png",
        "Cement for Stronger Block Making.png",
    ],
    "bulk cement ordering guide kenya": [
        "Bulk Cement Ordering Guide Kenya.png",
    ],
    "how to request a simba cement quotation": [
        "How to Request a Simba Cement Quotation.png",
        "Simba Cement Quotation Guide.png",
    ],
    "where to buy simba cement in kenya": [
        "Where to Buy Simba Cement in Kenya.png",
    ],
    "simba cement delivery guide kenya": [
        "Simba Cement Delivery Guide Kenya.png",
    ],
    "simba cement prices in kenya": [
        "Simba Cement Prices in Kenya.png",
    ],
    "simba cement 32.5r applications": [
        "Simba Cement 32.5R Applications.png",
    ],
    "simba cement 42.5n applications": [
        "Simba Cement 42.5N Applications.png",
    ],
    "how to reduce cement waste on site": [
        "How to Reduce Cement Waste on Site.png",
    ],
    "cement guide for first-time home builders": [
        "Cement Guide for First-Time Home Builders.png",
    ],
    "how to calculate concrete volume": [
        "How to Calculate Concrete Volume.png",
        "Concrete Volume Calculation Guide.png",
    ],
    "cement site delivery checklist": [
        "Cement Site Delivery Checklist.png",
        "Cement Site Delivery Checklist Infographic.png",
    ],
}

def existing_candidate(names):
    for name in names:
        p = by_lower.get(name.lower())
        if p:
            return p
    return None

def fuzzy_image(label):
    label_n = norm(label)
    label_t = tokens(label)
    best = None
    best_score = 0.0

    for p in images:
        pn = norm(p.stem)
        pt = tokens(p.stem)
        seq = SequenceMatcher(None, label_n, pn).ratio()
        union = label_t | pt
        jac = len(label_t & pt) / len(union) if union else 0
        contain = 1.0 if (label_n in pn or pn in label_n) else 0.0
        score = 0.45 * seq + 0.45 * jac + 0.10 * contain
        if score > best_score:
            best_score = score
            best = p

    return best if best_score >= 0.43 else None

def choose_blog_image(alt):
    key = alt.strip().lower()
    for title, candidates in BLOG_MAP.items():
        if key == title.lower():
            p = existing_candidate(candidates)
            if p:
                return p
            break
    return fuzzy_image(alt)

def relative_image_path(p):
    return "images/" + p.name

changed = []
replacements = []
unresolved = []

# First repair blog.html with the specific guide-image mapping.
blog = ROOT / "blog.html"
if blog.exists():
    text = blog.read_text(encoding="utf-8-sig")
    original = text

    # Known hero extension mismatch.
    if (IMG_DIR / "hero.jpeg").exists():
        text = text.replace('href="images/hero.jpg"', 'href="images/hero.jpeg"')
        text = text.replace('src="images/hero.jpg"', 'src="images/hero.jpeg"')

    def blog_img_repl(m):
        tag = m.group(0)
        src_m = re.search(r'\bsrc\s*=\s*(["\'])(.*?)\1', tag, re.I | re.S)
        alt_m = re.search(r'\balt\s*=\s*(["\'])(.*?)\1', tag, re.I | re.S)
        if not src_m:
            return tag

        src = src_m.group(2)
        if not src.startswith("images/"):
            return tag

        current = ROOT / src
        broken_generic = Path(src).name.lower() in {"bag.jpg", "bag.jpeg", "bag.png"}
        if current.exists() and not broken_generic:
            return tag

        alt = alt_m.group(2) if alt_m else ""
        chosen = choose_blog_image(alt)

        if not chosen:
            unresolved.append(("blog.html", src, alt))
            return tag

        new_src = relative_image_path(chosen)
        replacements.append(("blog.html", src, new_src, alt))
        start, end = src_m.span(2)
        return tag[:start] + new_src + tag[end:]

    text = re.sub(r'<img\b[^>]*>', blog_img_repl, text, flags=re.I | re.S)

    if text != original:
        blog.write_text(text, encoding="utf-8")
        changed.append("blog.html")

# Repair broken local image references across every HTML file.
for page in sorted(ROOT.glob("*.html")):
    text = page.read_text(encoding="utf-8-sig")
    original = text

    def img_repl(m):
        tag = m.group(0)
        src_m = re.search(r'\bsrc\s*=\s*(["\'])(.*?)\1', tag, re.I | re.S)
        alt_m = re.search(r'\balt\s*=\s*(["\'])(.*?)\1', tag, re.I | re.S)
        if not src_m:
            return tag

        src = src_m.group(2)
        if not src.startswith("images/"):
            return tag

        current = ROOT / src
        if current.exists():
            return tag

        name = Path(src).name
        stem = Path(name).stem
        alt = alt_m.group(2) if alt_m else ""

        # Same filename with a different image extension.
        for ext in IMAGE_EXTS:
            p = IMG_DIR / f"{stem}{ext}"
            if p.exists():
                new_src = relative_image_path(p)
                replacements.append((page.name, src, new_src, alt))
                a, b = src_m.span(2)
                return tag[:a] + new_src + tag[b:]

        # Common site assets.
        common = {
            "hero.jpg": "hero.jpeg",
            "hero.png": "hero.jpeg",
            "logo.jpg": "logo.jpeg",
            "logo.png": "logo.jpeg",
            "favicon.jpg": "favicon.jpeg",
            "favicon.png": "favicon.jpeg",
        }
        mapped = common.get(name.lower())
        if mapped and (IMG_DIR / mapped).exists():
            new_src = "images/" + mapped
            replacements.append((page.name, src, new_src, alt))
            a, b = src_m.span(2)
            return tag[:a] + new_src + tag[b:]

        # Use alt text or filename to locate the best matching uploaded image.
        chosen = fuzzy_image(alt or stem)
        if chosen:
            new_src = relative_image_path(chosen)
            replacements.append((page.name, src, new_src, alt))
            a, b = src_m.span(2)
            return tag[:a] + new_src + tag[b:]

        unresolved.append((page.name, src, alt))
        return tag

    text = re.sub(r'<img\b[^>]*>', img_repl, text, flags=re.I | re.S)

    # Fix image preload links too.
    def preload_repl(m):
        whole = m.group(0)
        href_m = re.search(r'\bhref\s*=\s*(["\'])(.*?)\1', whole, re.I | re.S)
        if not href_m:
            return whole
        href = href_m.group(2)
        if not href.startswith("images/") or (ROOT / href).exists():
            return whole

        name = Path(href).name
        stem = Path(name).stem
        options = [
            IMG_DIR / f"{stem}.jpeg",
            IMG_DIR / f"{stem}.jpg",
            IMG_DIR / f"{stem}.png",
            IMG_DIR / "hero.jpeg",
        ]
        chosen = next((p for p in options if p.exists()), None)
        if not chosen:
            return whole

        new_href = relative_image_path(chosen)
        a, b = href_m.span(2)
        return whole[:a] + new_href + whole[b:]

    text = re.sub(
        r'<link\b(?=[^>]*\brel\s*=\s*["\']preload["\'])(?=[^>]*\bas\s*=\s*["\']image["\'])[^>]*>',
        preload_repl,
        text,
        flags=re.I | re.S,
    )

    if text != original:
        page.write_text(text, encoding="utf-8")
        if page.name not in changed:
            changed.append(page.name)

# CSS url(...) references.
for css in (ROOT / "styles.css", ROOT / "styles.min.css", ROOT / "diagnostic-fixes.css"):
    if not css.exists():
        continue
    text = css.read_text(encoding="utf-8-sig")
    original = text

    def css_url_repl(m):
        quote = m.group(1) or ""
        src = m.group(2)
        if not src.startswith("images/") or (ROOT / src).exists():
            return m.group(0)

        stem = Path(src).stem
        for ext in IMAGE_EXTS:
            p = IMG_DIR / f"{stem}{ext}"
            if p.exists():
                return f"url({quote}{relative_image_path(p)}{quote})"
        return m.group(0)

    text = re.sub(r'url\(\s*(["\']?)(images/[^)"\']+)\1\s*\)', css_url_repl, text, flags=re.I)

    if text != original:
        css.write_text(text, encoding="utf-8")
        changed.append(css.name)

# Final audit.
remaining = []
for page in sorted(ROOT.glob("*.html")):
    text = page.read_text(encoding="utf-8-sig")
    for m in re.finditer(r'\bsrc\s*=\s*(["\'])(images/.*?)\1', text, re.I | re.S):
        src = m.group(2)
        if not (ROOT / src).exists():
            remaining.append((page.name, src))

print(f"Existing image files found: {len(images)}")
print(f"Files updated: {len(set(changed))}")
print(f"Image references repaired: {len(replacements)}")

if replacements:
    print("\nExamples of repaired paths:")
    for page, old, new, alt in replacements[:25]:
        print(f"  {page}: {old} -> {new}")

if remaining:
    print("\nStill missing after repair:")
    seen = set()
    for page, src in remaining:
        if (page, src) not in seen:
            print(f"  {page}: {src}")
            seen.add((page, src))
    print("\nSome missing files need manual matching. Send this output if any remain.")
    raise SystemExit(1)

print("\nSUCCESS: no broken local <img> references remain.")
print("Now run:")
print("  git diff --check")
print("  git status")
print("Then preview the site locally before committing.")
