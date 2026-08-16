from pathlib import Path
import re
import hashlib
import html

ROOT = Path(".")
HTML_FILES = sorted(ROOT.glob("*.html"))
CSS_FILES = [p for p in (ROOT / "styles.css", ROOT / "styles.min.css") if p.exists()]
GENERATED_CSS = ROOT / "diagnostic-fixes.css"

if not (ROOT / "index.html").exists():
    raise SystemExit("Run this script from the root of the simba-cement2 repository.")

style_map = {}

def style_class(style_text):
    normalized = re.sub(r"\s+", " ", style_text.strip())
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:10]
    cls = f"u-{digest}"
    style_map[cls] = normalized
    return cls

def merge_class(tag, new_class):
    class_match = re.search(r'\bclass\s*=\s*(["\'])(.*?)\1', tag, flags=re.I | re.S)
    if class_match:
        old = class_match.group(2).strip()
        classes = old.split()
        if new_class not in classes:
            classes.append(new_class)
        replacement = f'class="{" ".join(classes)}"'
        return tag[:class_match.start()] + replacement + tag[class_match.end():]
    return tag[:-1] + f' class="{new_class}">'

def move_inline_styles(text):
    def repl(m):
        tag = m.group(0)
        sm = re.search(r'\sstyle\s*=\s*(["\'])(.*?)\1', tag, flags=re.I | re.S)
        if not sm:
            return tag
        style = html.unescape(sm.group(2)).strip()
        if not style:
            return tag[:sm.start()] + tag[sm.end():]
        cls = style_class(style)
        tag = tag[:sm.start()] + tag[sm.end():]
        return merge_class(tag, cls)

    return re.sub(r'<[a-zA-Z][^<>]*\sstyle\s*=\s*(?:"[^"]*"|\'[^\']*\')[^<>]*>', repl, text, flags=re.S)

def add_noopener(text):
    def repl(m):
        tag = m.group(0)
        if not re.search(r'\btarget\s*=\s*(["\'])_blank\1', tag, flags=re.I):
            return tag

        rel = re.search(r'\brel\s*=\s*(["\'])(.*?)\1', tag, flags=re.I | re.S)
        if rel:
            tokens = rel.group(2).split()
            lowered = {x.lower() for x in tokens}
            if "noopener" not in lowered:
                tokens.append("noopener")
            if "noreferrer" not in lowered:
                tokens.append("noreferrer")
            replacement = f'rel="{" ".join(tokens)}"'
            return tag[:rel.start()] + replacement + tag[rel.end():]

        return tag[:-1] + ' rel="noopener noreferrer">'

    return re.sub(r'<a\b[^>]*>', repl, text, flags=re.I | re.S)

def remove_compat_attributes(text):
    # fetchpriority triggers Edge compatibility diagnostics on older browsers.
    text = re.sub(r'\sfetchpriority\s*=\s*(["\']).*?\1', '', text, flags=re.I | re.S)

    # theme-color is optional. Remove it to eliminate the compatibility diagnostic.
    text = re.sub(
        r'\s*<meta\b(?=[^>]*\bname\s*=\s*(["\'])theme-color\1)[^>]*>\s*',
        '\n',
        text,
        flags=re.I | re.S,
    )

    # These iframe attributes are optional enhancements and were flagged by the supplied diagnostics.
    text = re.sub(r'\sloading\s*=\s*(["\'])lazy\1', '', text, flags=re.I)
    text = re.sub(
        r'\sreferrerpolicy\s*=\s*(["\'])no-referrer-when-downgrade\1',
        '',
        text,
        flags=re.I,
    )
    return text

def accessible_iframes(text):
    def repl(m):
        tag = m.group(0)
        if re.search(r'\btitle\s*=', tag, flags=re.I):
            return tag
        srcm = re.search(r'\bsrc\s*=\s*(["\'])(.*?)\1', tag, flags=re.I | re.S)
        src = srcm.group(2).lower() if srcm else ""
        title = "Simba Cement location map" if "google" in src or "maps" in src else "Embedded content"
        return tag[:-1] + f' title="{title}">'

    return re.sub(r'<iframe\b[^>]*>', repl, text, flags=re.I | re.S)

def accessible_selects(text):
    # Add aria-label only to selects without an associated explicit label, title or aria-label.
    ids_with_labels = set()
    for lm in re.finditer(r'<label\b[^>]*\bfor\s*=\s*(["\'])(.*?)\1', text, flags=re.I | re.S):
        ids_with_labels.add(lm.group(2))

    def repl(m):
        tag = m.group(0)
        if re.search(r'\b(?:aria-label|aria-labelledby|title)\s*=', tag, flags=re.I):
            return tag

        idm = re.search(r'\bid\s*=\s*(["\'])(.*?)\1', tag, flags=re.I | re.S)
        if idm and idm.group(2) in ids_with_labels:
            return tag

        namem = re.search(r'\bname\s*=\s*(["\'])(.*?)\1', tag, flags=re.I | re.S)
        raw = idm.group(2) if idm else (namem.group(2) if namem else "selection")
        label = re.sub(r'[-_]+', ' ', raw).strip().title()
        if not label:
            label = "Selection"
        return tag[:-1] + f' aria-label="{html.escape(label, quote=True)}">'

    return re.sub(r'<select\b[^>]*>', repl, text, flags=re.I | re.S)

def ensure_generated_css_link(text):
    if "diagnostic-fixes.css" in text:
        return text
    link = '<link rel="stylesheet" href="diagnostic-fixes.css">'
    if "</head>" in text:
        return text.replace("</head>", link + "\n</head>", 1)
    return text

changed = []

for p in HTML_FILES:
    text = p.read_text(encoding="utf-8")
    original = text

    text = add_noopener(text)
    text = accessible_iframes(text)
    text = accessible_selects(text)
    text = remove_compat_attributes(text)
    text = move_inline_styles(text)
    text = ensure_generated_css_link(text)

    # Remove accidental trailing spaces, while preserving line structure.
    text = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"

    if text != original:
        p.write_text(text, encoding="utf-8")
        changed.append(p.name)

# Build external CSS for every formerly inline style.
css_lines = [
    "/* Auto-generated from former inline style attributes.",
    "   Do not edit manually. Re-run fix_edge_tool_problems.py instead. */",
]

for cls, rules in sorted(style_map.items()):
    # Add Safari prefix where backdrop-filter appears.
    if "backdrop-filter" in rules and "-webkit-backdrop-filter" not in rules:
        m = re.search(r'(?<!-)\bbackdrop-filter\s*:\s*([^;]+)', rules, flags=re.I)
        if m:
            rules = f"-webkit-backdrop-filter:{m.group(1).strip()};" + rules
    css_lines.append(f".{cls}{{{rules}}}")

GENERATED_CSS.write_text("\n".join(css_lines) + "\n", encoding="utf-8")

# Also prefix backdrop-filter in existing CSS.
for p in CSS_FILES:
    text = p.read_text(encoding="utf-8")
    original = text

    # Add -webkit-backdrop-filter only where it is not already immediately provided.
    pattern = re.compile(r'(?<!-)(backdrop-filter\s*:\s*([^;}{]+);)', flags=re.I)
    def prefix_repl(m):
        start = m.start()
        preceding = text[max(0, start - 120):start]
        if re.search(r'-webkit-backdrop-filter\s*:\s*[^;}{]+;\s*$', preceding, flags=re.I):
            return m.group(1)
        value = m.group(2).strip()
        return f'-webkit-backdrop-filter:{value};{m.group(1)}'

    text = pattern.sub(prefix_repl, text)

    if text != original:
        p.write_text(text, encoding="utf-8")
        if p.name not in changed:
            changed.append(p.name)

# Verification based on the supplied diagnostic categories.
issues = []

for p in HTML_FILES:
    text = p.read_text(encoding="utf-8")

    if re.search(r'<[a-zA-Z][^<>]*\sstyle\s*=', text, flags=re.I | re.S):
        issues.append(f"{p.name}: inline style remains")

    for m in re.finditer(r'<a\b[^>]*target\s*=\s*(["\'])_blank\1[^>]*>', text, flags=re.I | re.S):
        tag = m.group(0)
        rel = re.search(r'\brel\s*=\s*(["\'])(.*?)\1', tag, flags=re.I | re.S)
        if not rel or "noopener" not in rel.group(2).lower().split():
            issues.append(f"{p.name}: target=_blank link without noopener")
            break

    if re.search(r'\sfetchpriority\s*=', text, flags=re.I):
        issues.append(f"{p.name}: fetchpriority remains")

    if re.search(r'<meta\b(?=[^>]*name\s*=\s*(["\'])theme-color\1)', text, flags=re.I):
        issues.append(f"{p.name}: theme-color remains")

    for m in re.finditer(r'<iframe\b[^>]*>', text, flags=re.I | re.S):
        if not re.search(r'\btitle\s*=', m.group(0), flags=re.I):
            issues.append(f"{p.name}: iframe without title")
            break

for p in CSS_FILES + ([GENERATED_CSS] if GENERATED_CSS.exists() else []):
    text = p.read_text(encoding="utf-8")
    # Every non-prefixed backdrop-filter should have a webkit version in the same rule.
    for rule in re.findall(r'[^{}]+\{([^{}]*)\}', text, flags=re.S):
        if re.search(r'(?<!-)\bbackdrop-filter\s*:', rule, flags=re.I):
            if not re.search(r'-webkit-backdrop-filter\s*:', rule, flags=re.I):
                issues.append(f"{p.name}: backdrop-filter without Safari prefix")
                break

print(f"Updated {len(changed)} existing files.")
print(f"Generated {GENERATED_CSS.name} with {len(style_map)} reusable CSS classes.")

if issues:
    print("\nRemaining source checks:")
    for issue in issues:
        print(" -", issue)
    raise SystemExit(1)

print("\nEdge Tools source-pattern fixes completed successfully.")
print("Now reload VS Code or reopen the folder so Microsoft Edge Tools re-scans the files.")
print("Then run: git diff --check")
