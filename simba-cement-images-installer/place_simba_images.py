from pathlib import Path
import re
import shutil

ROOT = Path(".")
IMG = ROOT / "images"

if not (ROOT / "index.html").exists():
    raise SystemExit("Run this script from the root of the simba-cement2 project.")

IMG.mkdir(exist_ok=True)

FILES = [
    "logo.jpeg",
    "simba cement 32.5.jpeg",
    "simba cement 42.5.jpeg",
    "favicon.jpeg",
    "hero.jpeg",
]

for name in FILES:
    src = ROOT / name
    if not src.exists():
        raise SystemExit(f"Missing {name}. Keep the five supplied images beside this script.")
    shutil.copy2(src, IMG / name)

html_files = sorted(ROOT.glob("*.html"))
changed = []

def ensure_favicon(text):
    text = re.sub(
        r'\s*<link\b[^>]*\brel\s*=\s*["\'](?:shortcut icon|icon)["\'][^>]*>\s*',
        '\n',
        text,
        flags=re.I,
    )
    favicon = (
        '<link rel="icon" type="image/jpeg" href="images/favicon.jpeg">\n'
        '<link rel="shortcut icon" href="images/favicon.jpeg">'
    )
    return text.replace("</head>", favicon + "\n</head>", 1)

def replace_header_brand(text):
    text = re.sub(
        r'<div\s+class=["\']brand-mark["\']>\s*S\s*</div>',
        '<div class="brand-mark brand-mark-image"><img src="images/logo.jpeg" '
        'alt="Simba Cement logo" width="160" height="90" decoding="async"></div>',
        text,
        flags=re.I,
    )
    return text

def replace_product_images(text):
    text = text.replace(
        'src="images/bag.jpg" alt="Simba Cement 32.5R bag"',
        'src="images/simba cement 32.5.jpeg" alt="Simba Cement 32.5R PPC 50kg bag"'
    )
    text = text.replace(
        'src="images/simba cement 42.5.jpeg" alt="Simba Cement 42.5N bag"',
        'src="images/simba cement 42.5.jpeg" alt="Simba Cement 42.5N Power 50kg bag"'
    )
    return text

def replace_hero(text, filename):
    if filename != "index.html":
        return text
    text = re.sub(
        r'(<img\b[^>]*class=["\'][^"\']*\bbg\b[^"\']*["\'][^>]*\bsrc=["\'])[^"\']+(["\'])',
        r'\1images/hero.jpeg\2',
        text,
        count=1,
        flags=re.I,
    )
    return text

def update_social_image(text, filename):
    if filename == "index.html":
        social = "https://simbacement.co.ke/images/hero.jpeg"
    elif filename == "products.html":
        social = "https://simbacement.co.ke/images/simba%20cement%2032.5.jpeg"
    else:
        return text

    text = re.sub(
        r'(<meta\b[^>]*property=["\']og:image(?:\:secure_url)?["\'][^>]*content=["\'])[^"\']+(["\'])',
        rf'\1{social}\2',
        text,
        flags=re.I,
    )
    text = re.sub(
        r'(<meta\b[^>]*name=["\']twitter:image["\'][^>]*content=["\'])[^"\']+(["\'])',
        rf'\1{social}\2',
        text,
        flags=re.I,
    )
    return text

for p in html_files:
    text = p.read_text(encoding="utf-8-sig")
    original = text

    text = ensure_favicon(text)
    text = replace_header_brand(text)
    text = replace_product_images(text)
    text = replace_hero(text, p.name)
    text = update_social_image(text, p.name)

    if text != original:
        p.write_text(text, encoding="utf-8")
        changed.append(p.name)

css_patch = '''
/* Simba image placement */
.brand-mark.brand-mark-image{
  width:72px;
  height:48px;
  border-radius:8px;
  overflow:hidden;
  background:#fff;
  display:flex;
  align-items:center;
  justify-content:center;
  flex:0 0 auto;
}
.brand-mark.brand-mark-image img{
  width:100%;
  height:100%;
  object-fit:contain;
  display:block;
}
@media (max-width:768px){
  .brand-mark.brand-mark-image{
    width:58px;
    height:40px;
  }
}
'''

for css_name in ("styles.css", "styles.min.css"):
    p = ROOT / css_name
    if p.exists():
        text = p.read_text(encoding="utf-8")
        if "/* Simba image placement */" not in text:
            p.write_text(text.rstrip() + "\n" + css_patch + "\n", encoding="utf-8")

index = (ROOT / "index.html").read_text(encoding="utf-8")
products = (ROOT / "products.html").read_text(encoding="utf-8")

checks = {
    "homepage hero": 'src="images/hero.jpeg"' in index,
    "header logo": 'src="images/logo.jpeg"' in index,
    "favicon": 'href="images/favicon.jpeg"' in index,
    "32.5 product": 'src="images/simba cement 32.5.jpeg"' in products,
    "42.5 product": 'src="images/simba cement 42.5.jpeg"' in products,
}

failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("Placement verification failed: " + ", ".join(failed))

print(f"Updated {len(changed)} HTML files.")
print("Placed all five images successfully:")
print("  logo.jpeg -> website header/brand")
print("  favicon.jpeg -> browser favicon")
print("  hero.jpeg -> homepage hero")
print("  simba cement 32.5.jpeg -> 32.5R product")
print("  simba cement 42.5.jpeg -> 42.5 product")
print("")
print("Run: git diff --check")
print("Then preview index.html and products.html before committing.")
