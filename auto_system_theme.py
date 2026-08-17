
from pathlib import Path
import re

ROOT = Path(".")

if not (ROOT / "index.html").exists():
    raise SystemExit("Run this from the root of the simba-cement2 project.")

html_files = list(ROOT.glob("*.html"))
changed = []

toggle_pattern = re.compile(
    r'\s*<button\b[^>]*\bid=["\']theme-toggle["\'][^>]*>.*?</button>\s*',
    flags=re.I | re.S
)

for p in html_files:
    text = p.read_text(encoding="utf-8-sig")
    original = text
    text = toggle_pattern.sub("\n", text)
    if text != original:
        p.write_text(text, encoding="utf-8")
        changed.append(p.name)

auto_theme_js = '''// Automatic system theme sync
(function initSystemTheme() {
  const media = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;

  const applySystemTheme = () => {
    const dark = media && media.matches;
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
    document.documentElement.style.colorScheme = dark ? 'dark' : 'light';
    try { localStorage.removeItem('simba_theme'); } catch (e) {}
  };

  applySystemTheme();

  if (media) {
    if (typeof media.addEventListener === 'function') {
      media.addEventListener('change', applySystemTheme);
    } else if (typeof media.addListener === 'function') {
      media.addListener(applySystemTheme);
    }
  }
})();'''

for jsname in ("app.js", "app.min.js"):
    p = ROOT / jsname
    if not p.exists():
        continue
    text = p.read_text(encoding="utf-8-sig")
    original = text

    text = re.sub(
        r'// Immediate Theme Initialization.*?\}\)\(\);\s*',
        auto_theme_js + "\n\n",
        text,
        count=1,
        flags=re.I | re.S,
    )

    text = re.sub(
        r'\s*// Theme Toggle Button Logic\s*const themeToggle = document\.getElementById\([\'"]theme-toggle[\'"]\);.*?\n\s*}\s*\n\s*(?=// Mobile Navigation Burger Menu Toggle)',
        "\n\n  ",
        text,
        count=1,
        flags=re.I | re.S,
    )

    if text != original:
        p.write_text(text, encoding="utf-8")
        changed.append(jsname)

css_patch = '''
/* Automatic device color adaptation */
:root {
  color-scheme: light dark;
}

@media (prefers-color-scheme: light) {
  :root {
    color-scheme: light;
  }
}

@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
  }
}

.theme-toggle {
  display: none !important;
}
'''

for cssname in ("styles.css", "styles.min.css"):
    p = ROOT / cssname
    if not p.exists():
        continue
    text = p.read_text(encoding="utf-8-sig")
    if "/* Automatic device color adaptation */" not in text:
        p.write_text(text.rstrip() + "\n" + css_patch + "\n", encoding="utf-8")
        changed.append(cssname)

remaining_toggle = []
for p in html_files:
    text = p.read_text(encoding="utf-8")
    if 'id="theme-toggle"' in text or "id='theme-toggle'" in text:
        remaining_toggle.append(p.name)

if remaining_toggle:
    raise SystemExit("Theme toggle remains in: " + ", ".join(remaining_toggle))

print(f"Updated {len(set(changed))} files.")
print("Manual light/dark selector removed.")
print("Site now follows each device's system light/dark setting automatically.")
print("Now run: git diff --check")
