"""HTML templates and CSS for vibefs renderers."""

BASE_HEAD = '<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">'

_GOOGLE_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Google+Sans+Flex:wght@100..900&family=Google+Sans+Code:wght@100..700&display=swap" rel="stylesheet">'
)


def _dual_pygments_css(dark_style='github-dark', light_style='default', cssclass='highlight', **kwargs):
    """Return combined Pygments CSS for dark (default) and light (media query) modes."""
    from pygments.formatters import HtmlFormatter
    try:
        dark_css = HtmlFormatter(style=dark_style, cssclass=cssclass, **kwargs).get_style_defs(f'.{cssclass}')
    except Exception:
        dark_css = HtmlFormatter(style='monokai', cssclass=cssclass, **kwargs).get_style_defs(f'.{cssclass}')
    try:
        light_css = HtmlFormatter(style=light_style, cssclass=cssclass, **kwargs).get_style_defs(f'.{cssclass}')
    except Exception:
        light_css = HtmlFormatter(style='default', cssclass=cssclass, **kwargs).get_style_defs(f'.{cssclass}')
    return dark_css + '\n@media (prefers-color-scheme: light) {\n' + light_css + '\n}'


BASE_CSS = (
    '* { margin: 0; padding: 0; box-sizing: border-box; }'
    ' :root { --bg: #1e1e1e; --bg-header: #2d2d2d; --border: #404040;'
    ' --text: #d4d4d4; --text-header: #e0e0e0; --text-muted: #888888;'
    ' --link: #6ab0f3;'
    ' --font-sans: "Google Sans Flex", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;'
    ' --font-mono: "Google Sans Code", "SF Mono", "Menlo", "Monaco", "Consolas", monospace; }'
    ' @media (prefers-color-scheme: light) {'
    ' :root { --bg: #ffffff; --bg-header: #f6f8fa; --border: #d0d7de;'
    ' --text: #1f2328; --text-header: #1f2328; --text-muted: #656d76;'
    ' --link: #0969da; } }'
    ' body { font-family: var(--font-sans);'
    ' background: var(--bg); color: var(--text); min-height: 100vh; }'
)


CENTERED_PAGE_CSS = (
    BASE_CSS + ' body { display: flex; align-items: center; justify-content: center; }'
    ' .container { max-width: 400px; width: 100%; padding: 32px 16px; text-align: center; }'
    ' h1 { font-size: 1.3em; color: var(--text-header); margin-bottom: 8px; }'
    ' p { color: var(--text-muted); font-size: 14px; }'
    ' .unlock { display: inline-block; margin-top: 24px; background: #4a9eff; color: #fff;'
    ' text-decoration: none; padding: 10px 20px; border-radius: 6px; font-size: 14px; font-weight: 500; }'
    ' .unlock:hover { background: #3a8eef; }'
)


EXPIRED_TEMPLATE = (
    '<!DOCTYPE html><html><head>'
    + BASE_HEAD
    + '<title>File Expired</title><style>'
    + CENTERED_PAGE_CSS
    + '</style></head><body><div class="container">'
    '<h1>This file is no longer available</h1>'
    '<p><strong>{{filename}}</strong> has expired and can no longer be accessed.</p>\n'
    '% if verify_url:\n'
    '<a class="unlock" href="{{verify_url}}">Unlock with password</a>\n'
    '% end\n'
    '</div></body></html>'
)


VERIFY_PAGE_CSS = (
    CENTERED_PAGE_CSS + ' .hint { color: var(--text-muted); font-size: 13px; margin-bottom: 16px; }'
    ' form { display: flex; flex-direction: column; gap: 12px; }'
    ' input[type="password"] { background: var(--bg-header); border: 1px solid var(--border); color: var(--text-header);'
    ' padding: 10px 14px; border-radius: 6px; font-size: 16px; outline: none; width: 100%;'
    ' -webkit-appearance: none; }'
    ' input[type="password"]:focus { border-color: var(--link); }'
    ' button { background: #4a9eff; color: #fff; border: none; padding: 10px 14px;'
    ' border-radius: 6px; font-size: 14px; cursor: pointer; font-weight: 500; }'
    ' button:hover { background: #3a8eef; }'
    ' .error { color: #f44; font-size: 13px; }'
)


EXPIRED_VERIFY_TEMPLATE = (
    '<!DOCTYPE html><html><head>'
    + BASE_HEAD
    + '<title>Verification Required</title><style>'
    + VERIFY_PAGE_CSS
    + '</style></head><body><div class="container">'
    '<h1>This content has expired</h1>'
    '<p class="hint">Enter password to unlock access</p>'
    '<form method="POST" action="/verify">'
    '<input type="hidden" name="next" value="{{next}}">'
    '<input type="password" name="password" placeholder="Password" autofocus>'
    '<button type="submit">Unlock</button>\n'
    '% if error:\n'
    '<p class="error">{{error}}</p>\n'
    '% end\n'
    '</form></div></body></html>'
)


MARKDOWN_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{display_path}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible+Mono:ital,wght@0,200..800;1,200..800&family=Atkinson+Hyperlegible+Next:ital,wght@0,200..800;1,200..800&display=swap" rel="stylesheet">
<script>
/* Run before paint to avoid flash of wrong theme */
(function() {{
  var t = localStorage.getItem('vf-theme');
  if (!t) t = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', t);
  var fs = parseInt(localStorage.getItem('vf-fs'));
  if (fs >= 14 && fs <= 26) document.documentElement.style.setProperty('--fs', fs + 'px');
}})();
</script>
<style>
/* ── Reset ──────────────────────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ overflow-x: hidden; scroll-behavior: smooth; }}

/* ── Font stack ─────────────────────────────────────────────── */
/* Atkinson Hyperlegible Next: designed by the Braille Institute */
/* to maximise character disambiguation — every glyph is         */
/* engineered to be distinct from every other. Excellent for     */
/* mixed prose/technical content. Variable font = one HTTP req.  */
:root {{
  --font-body: 'Atkinson Hyperlegible Next', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-ui:   'Atkinson Hyperlegible Next', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'Atkinson Hyperlegible Mono', 'SF Mono', 'Menlo', 'Consolas', monospace;
  --fs: 18px;
}}

/* ── Light theme — warm off-white, like quality book paper ──── */
/* Avoids pure white (#fff) which causes eye strain and glare   */
:root, [data-theme="light"] {{
  --bg:           #F9F7F4;
  --bg-raised:    #F2EFE9;
  --bg-code:      #EDE9E2;
  --border:       #DDD9D1;
  --border-soft:  #E8E4DC;
  --text-head:    #1C1916;
  --text-body:    #36322C;
  --text-muted:   #7A746C;
  --link:         #1A5296;
  --link-hover:   #0E3870;
  --code-fg:      #7C3319;
  --quote-bg:     #F2EDE3;
  --quote-border: #C4B49A;
  --progress:     #1A5296;
  --ctrl-bg:      rgba(0,0,0,0.05);
  --ctrl-hover:   rgba(0,0,0,0.10);
  --ctrl-active:  rgba(0,0,0,0.15);
  --ctrl-shadow:  rgba(0,0,0,0.10);
}}

/* ── Dark theme — warm dark, NOT pure black ─────────────────── */
/* Pure black causes halation; ~50% with astigmatism find it    */
/* harder to read. Warm dark grey is the research-backed choice */
[data-theme="dark"] {{
  --bg:           #1C1814;
  --bg-raised:    #252018;
  --bg-code:      #201C18;
  --border:       #322C26;
  --border-soft:  #2A2520;
  --text-head:    #E0D6C8;
  --text-body:    #C4BAA8;
  --text-muted:   #78706A;
  --link:         #82B8F5;
  --link-hover:   #A8CEFF;
  --code-fg:      #F0A070;
  --quote-bg:     #231E18;
  --quote-border: #5A4C3E;
  --progress:     #82B8F5;
  --ctrl-bg:      rgba(255,255,255,0.06);
  --ctrl-hover:   rgba(255,255,255,0.12);
  --ctrl-active:  rgba(255,255,255,0.18);
  --ctrl-shadow:  rgba(0,0,0,0.40);
}}

/* ── Night theme — near-black warm amber, for lights-off ────── */
/* ~1800K colour temperature. Minimises blue light to preserve  */
/* melatonin. Warm amber text is easier than white in darkness. */
/* Also benefits ~40% of adults with astigmatism (sepia effect) */
[data-theme="night"] {{
  --bg:           #0E0B08;
  --bg-raised:    #161008;
  --bg-code:      #130E08;
  --border:       #1E1710;
  --border-soft:  #1A1410;
  --text-head:    #C8A870;
  --text-body:    #A88C60;
  --text-muted:   #5C4C38;
  --link:         #C49460;
  --link-hover:   #D8AC78;
  --code-fg:      #C49460;
  --quote-bg:     #120E08;
  --quote-border: #4A3820;
  --progress:     #C49460;
  --ctrl-bg:      rgba(200,160,100,0.08);
  --ctrl-hover:   rgba(200,160,100,0.15);
  --ctrl-active:  rgba(200,160,100,0.22);
  --ctrl-shadow:  rgba(0,0,0,0.60);
}}

/* ── Reading progress bar ───────────────────────────────────── */
#vf-progress {{
  position: fixed; top: 0; left: 0;
  height: 2px; width: 0%;
  background: var(--progress);
  z-index: 1000;
  transition: width 80ms linear;
  opacity: 0.65;
  pointer-events: none;
}}

/* ── Controls (theme + font size) ──────────────────────────── */
.vf-ctrl-group {{
  position: fixed; right: 16px;
  display: flex; align-items: center; gap: 2px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 4px 5px;
  box-shadow: 0 2px 10px var(--ctrl-shadow);
  z-index: 999;
  opacity: 0.25;
  transition: opacity 0.25s;
}}
.vf-ctrl-group:hover {{ opacity: 1; }}
#vf-themes {{ top: 14px; }}
#vf-fonts  {{ top: 54px; }}

.vf-btn {{
  border: none; background: none; cursor: pointer;
  padding: 4px 9px; border-radius: 14px;
  font-family: var(--font-ui); font-size: 12px; line-height: 1;
  color: var(--text-muted);
  transition: background 0.15s, color 0.15s;
  -webkit-user-select: none; user-select: none;
}}
.vf-btn:hover  {{ background: var(--ctrl-hover);  color: var(--text-body); }}
.vf-btn.active {{ background: var(--ctrl-active); color: var(--text-head); font-weight: 500; }}

/* ── Body ───────────────────────────────────────────────────── */
/* 18px: research shows 18-20px is optimal for extended reading */
body {{
  font-family: var(--font-body);
  font-size: var(--fs);
  /* 1.65: above research minimum (1.4) to account for          */
  /* longer document reading and serif font rhythm              */
  line-height: 1.65;
  /* 0.01em letter-spacing improves comprehension (research)    */
  letter-spacing: 0.01em;
  background: var(--bg);
  color: var(--text-body);
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}}

/* ── Content column ─────────────────────────────────────────── */
/* 65ch ≈ 65 characters — research sweet spot (55-66 chars)    */
.md {{
  max-width: 65ch;
  margin: 0 auto;
  padding: 52px 24px 80px;
}}

/* ── Headings ───────────────────────────────────────────────── */
/* Sans-serif for headings: clear contrast with serif body      */
h1, h2, h3, h4, h5, h6 {{
  font-family: var(--font-ui);
  color: var(--text-head);
  line-height: 1.22;
  font-weight: 600;
  letter-spacing: -0.02em;
}}
h1 {{ font-size: 1.75em; margin: 0 0 0.8em; padding-bottom: 0.4em; border-bottom: 1px solid var(--border-soft); }}
h2 {{ font-size: 1.30em; margin: 2.2em 0 0.6em; padding-bottom: 0.35em; border-bottom: 1px solid var(--border-soft); }}
h3 {{ font-size: 1.08em; margin: 1.8em 0 0.5em; font-weight: 600; }}
h4 {{ font-size: 1.00em; margin: 1.5em 0 0.4em; font-weight: 600; letter-spacing: 0; }}
h5, h6 {{ font-size: 0.85em; margin: 1.3em 0 0.35em; font-weight: 600;
          color: var(--text-muted); letter-spacing: 0.04em; text-transform: uppercase; }}

/* ── Prose ──────────────────────────────────────────────────── */
p {{ margin-bottom: 1.2em; }}
strong {{ color: var(--text-head); font-weight: 600; }}
em {{ font-style: italic; }}

a {{
  color: var(--link);
  text-decoration: underline;
  text-decoration-color: transparent;
  text-underline-offset: 3px;
  transition: color 0.15s, text-decoration-color 0.15s;
}}
a:hover {{ color: var(--link-hover); text-decoration-color: var(--link-hover); }}

/* ── Lists ──────────────────────────────────────────────────── */
ul, ol {{ padding-left: 1.7em; margin-bottom: 1.2em; }}
li {{ margin-bottom: 0.35em; }}
li > ul, li > ol {{ margin-top: 0.25em; margin-bottom: 0.25em; }}

/* ── Blockquote ─────────────────────────────────────────────── */
/* Tinted background + left rule — more readable than bare rule */
blockquote {{
  border-left: 3px solid var(--quote-border);
  background: var(--quote-bg);
  margin: 1.6em 0;
  padding: 0.8em 1.2em;
  border-radius: 0 5px 5px 0;
  color: var(--text-muted);
  font-style: italic;
}}
blockquote p:last-child {{ margin-bottom: 0; }}

/* ── Rule ───────────────────────────────────────────────────── */
hr {{ border: none; border-top: 1px solid var(--border); margin: 2.4em 0; }}

/* ── Inline code ────────────────────────────────────────────── */
code {{
  font-family: var(--font-mono);
  font-size: 0.80em;
  background: var(--bg-code);
  color: var(--code-fg);
  padding: 0.15em 0.42em;
  border-radius: 3px;
  font-variant-ligatures: none;
  letter-spacing: 0;
}}

/* ── Code blocks ────────────────────────────────────────────── */
pre {{
  margin: 1.6em 0;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid var(--border);
}}
pre code {{ background: none; color: inherit; padding: 0; }}

{pygments_css}

.highlight {{
  background: var(--bg-code) !important;
  margin: 0; border-radius: 0;
}}
.highlight pre {{
  padding: 1.1em 1.3em;
  margin: 0;
  font-family: var(--font-mono);
  font-size: 0.82em;
  line-height: 1.6;
  white-space: pre;
  overflow-x: auto;
  letter-spacing: 0;
  font-variant-ligatures: none;
}}

/* ── Tables ─────────────────────────────────────────────────── */
.table-wrapper {{
  width: 100%; overflow-x: auto; margin: 1.6em 0;
  border: 1px solid var(--border); border-radius: 6px;
}}
table {{ border-collapse: collapse; width: 100%; font-family: var(--font-ui); font-size: 0.875em; letter-spacing: 0; }}
th {{
  background: var(--bg-raised); color: var(--text-head);
  padding: 0.65em 1em; border-bottom: 2px solid var(--border);
  text-align: left; font-weight: 600; white-space: nowrap;
}}
td {{
  padding: 0.6em 1em; border-bottom: 1px solid var(--border-soft);
  color: var(--text-body);
}}
tr:last-child td {{ border-bottom: none; }}
tr:nth-child(even) td {{ background: var(--bg-raised); }}
tbody tr:hover td {{ background: var(--bg-code); }}

/* ── Images ─────────────────────────────────────────────────── */
img {{ max-width: 100%; height: auto; border-radius: 5px; }}

/* ── Footer ─────────────────────────────────────────────────── */
.vf-footer {{
  max-width: 65ch; margin: 0 auto;
  padding: 14px 24px 36px;
  border-top: 1px solid var(--border);
  display: flex; align-items: center; gap: 10px;
  font-family: var(--font-ui);
}}
.vf-footer-path {{ font-size: 11px; font-family: var(--font-mono); color: var(--text-muted); letter-spacing: 0; }}
.vf-footer-meta {{ font-size: 11px; color: var(--text-muted); opacity: 0.55; margin-left: auto; }}

/* ── Mobile ─────────────────────────────────────────────────── */
@media (max-width: 600px) {{
  :root {{ --fs: 17px; }}
  .md {{ padding: 36px 18px 60px; }}
  .vf-ctrl-group {{ opacity: 0.5; }}
  #vf-themes {{ top: auto; bottom: 56px; right: 12px; }}
  #vf-fonts  {{ top: auto; bottom: 14px; right: 12px; }}
}}

/* ── Print ──────────────────────────────────────────────────── */
@media print {{
  #vf-progress, .vf-ctrl-group {{ display: none !important; }}
  body {{ background: #fff; color: #111; font-size: 11pt; }}
  a {{ color: #111; text-decoration: underline; }}
  pre, code {{ background: #f4f4f4 !important; color: #333 !important; border: 1px solid #ddd; }}
  h1, h2, h3, h4, h5, h6 {{ color: #000; }}
  .md {{ max-width: 100%; padding: 0; }}
  .vf-footer {{ padding: 12pt 0 0; border-top: 1pt solid #ccc; }}
}}
</style>
</head>
<body>

<div id="vf-progress"></div>

<!-- Theme: ☀ light  ◐ dark  ☾ night (sepia/amber — warm for low-light) -->
<nav id="vf-themes" class="vf-ctrl-group" aria-label="Theme">
  <button class="vf-btn" data-t="light"  title="Light mode">☀</button>
  <button class="vf-btn" data-t="dark"   title="Dark mode">◐</button>
  <button class="vf-btn" data-t="night"  title="Night mode (warm amber)">☾</button>
</nav>

<!-- Font size: A− smaller  A+ larger -->
<div id="vf-fonts" class="vf-ctrl-group" aria-label="Font size">
  <button class="vf-btn" id="vf-fd" title="Smaller text">A−</button>
  <button class="vf-btn" id="vf-fu" title="Larger text">A+</button>
</div>

<main class="md">
  {body_html}
</main>

<footer class="vf-footer">
  <span class="vf-footer-path">{display_path}</span>
  <span class="vf-footer-meta">{file_meta}</span>
</footer>

<script>
(function() {{
  /* Reading progress bar */
  var bar = document.getElementById('vf-progress');
  function tick() {{
    var scrolled = window.scrollY || document.documentElement.scrollTop;
    var total = document.documentElement.scrollHeight - window.innerHeight;
    bar.style.width = (total > 0 ? Math.min(100, scrolled / total * 100) : 0) + '%';
  }}
  window.addEventListener('scroll', tick, {{passive: true}});
  tick();

  /* Theme switcher */
  var btns = document.querySelectorAll('[data-t]');
  function applyTheme(t) {{
    document.documentElement.setAttribute('data-theme', t);
    localStorage.setItem('vf-theme', t);
    btns.forEach(function(b) {{ b.classList.toggle('active', b.dataset.t === t); }});
  }}
  btns.forEach(function(b) {{
    b.addEventListener('click', function() {{ applyTheme(b.dataset.t); }});
  }});
  applyTheme(document.documentElement.getAttribute('data-theme') || 'light');

  /* Font size controls: 14–26px range */
  var FS_MIN = 14, FS_MAX = 26;
  var fs = parseInt(localStorage.getItem('vf-fs')) || 18;
  function applyFs(n) {{
    fs = Math.max(FS_MIN, Math.min(FS_MAX, n));
    document.documentElement.style.setProperty('--fs', fs + 'px');
    localStorage.setItem('vf-fs', fs);
  }}
  document.getElementById('vf-fu').addEventListener('click', function() {{ applyFs(fs + 1); }});
  document.getElementById('vf-fd').addEventListener('click', function() {{ applyFs(fs - 1); }});
  applyFs(fs);
}})();
</script>

</body>
</html>"""


CODE_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{display_path}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Google+Sans+Flex:wght@100..900&family=Google+Sans+Code:wght@100..700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #1e1e1e;
    --bg-header: #2d2d2d;
    --border: #404040;
    --text: #d4d4d4;
    --text-header: #e0e0e0;
    --text-muted: #888888;
    --font-sans: 'Google Sans Flex', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-mono: 'Google Sans Code', 'SF Mono', 'Menlo', 'Monaco', 'Consolas', monospace;
  }}
  @media (prefers-color-scheme: light) {{
    :root {{
      --bg: #ffffff;
      --bg-header: #f6f8fa;
      --border: #d0d7de;
      --text: #1f2328;
      --text-header: #1f2328;
      --text-muted: #656d76;
    }}
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: var(--font-sans);
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }}
  .file-header {{
    background: var(--bg-header);
    border-bottom: 1px solid var(--border);
    padding: 12px 16px;
  }}
  .file-path {{
    font-size: 14px;
    font-weight: 500;
    color: var(--text-header);
    word-break: break-all;
    font-family: var(--font-mono);
  }}
  .file-meta {{
    font-size: 12px;
    font-weight: 400;
    color: var(--text-muted);
    margin-top: 4px;
    font-family: var(--font-sans);
  }}
  .file-content {{
    overflow-x: auto;
  }}
  {pygments_css}
  .highlight {{
    background: var(--bg);
    padding: 0;
  }}
  .highlight pre {{
    padding: 12px 16px;
    margin: 0;
    font-family: var(--font-mono);
    font-size: 14px;
    line-height: 1.65;
    white-space: pre-wrap;
    word-wrap: break-word;
    overflow-wrap: break-word;
  }}
  @media (max-width: 768px) {{
    .file-header {{
      padding: 10px 12px;
    }}
    .highlight pre {{
      font-size: 13px;
      line-height: 1.5;
      padding: 8px 12px;
    }}
  }}
</style>
</head>
<body>
  <div class="file-header">
    <div class="file-path">{display_path}</div>
    <div class="file-meta">{file_meta}</div>
  </div>
  <div class="file-content">
    {highlighted}
  </div>
</body>
</html>"""


GIT_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{repo_path} · {short_hash}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Google+Sans+Flex:wght@100..900&family=Google+Sans+Code:wght@100..700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #1e1e1e;
    --bg-header: #2d2d2d;
    --bg-file: #252525;
    --bg-file-hover: #2d2d2d;
    --border: #383838;
    --text: #d4d4d4;
    --text-header: #e0e0e0;
    --text-muted: #888888;
    --text-body: #b0b0b0;
    --link: #6ab0f3;
    --font-sans: 'Google Sans Flex', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-mono: 'Google Sans Code', 'SF Mono', 'Menlo', 'Monaco', 'Consolas', monospace;
  }}
  @media (prefers-color-scheme: light) {{
    :root {{
      --bg: #ffffff;
      --bg-header: #f6f8fa;
      --bg-file: #f6f8fa;
      --bg-file-hover: #eef1f4;
      --border: #d0d7de;
      --text: #1f2328;
      --text-header: #1f2328;
      --text-muted: #656d76;
      --text-body: #57606a;
      --link: #0969da;
    }}
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: var(--font-sans);
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }}
  .commit-header {{
    background: var(--bg-header);
    border-bottom: 1px solid var(--border);
    padding: 16px 20px;
  }}
  .commit-repo {{
    font-size: 12px;
    font-family: var(--font-mono);
    color: var(--text-muted);
    margin-bottom: 10px;
  }}
  .commit-subject {{
    font-size: 17px;
    font-weight: 600;
    color: var(--text-header);
    margin-bottom: 8px;
    line-height: 1.4;
  }}
  .commit-body {{
    font-size: 14px;
    color: var(--text-body);
    white-space: pre-wrap;
    margin-bottom: 10px;
    line-height: 1.6;
  }}
  .commit-meta {{
    font-size: 13px;
    color: var(--text-muted);
  }}
  .commit-meta .hash {{
    font-family: var(--font-mono);
    color: var(--link);
  }}
  .file-summary {{
    padding: 10px 20px;
    font-size: 13px;
    color: var(--text-muted);
    background: var(--bg-header);
    border-bottom: 1px solid var(--border);
  }}
  .file-list {{
    padding: 4px 0;
  }}
  .file-list details {{
    border-bottom: 1px solid var(--border);
  }}
  .file-list summary {{
    padding: 10px 20px;
    cursor: pointer;
    font-size: 13px;
    font-family: var(--font-mono);
    background: var(--bg-file);
    display: flex;
    align-items: center;
    gap: 12px;
    list-style: none;
  }}
  .file-list summary::-webkit-details-marker {{ display: none; }}
  .file-list summary::before {{
    content: '▶';
    font-size: 10px;
    color: var(--text-muted);
    transition: transform 0.15s;
    flex-shrink: 0;
  }}
  .file-list details[open] summary::before {{ transform: rotate(90deg); }}
  .file-list summary:hover {{
    background: var(--bg-file-hover);
  }}
  .file-path {{
    color: var(--text-header);
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }}
  .file-stats {{
    color: var(--text-muted);
    font-size: 12px;
    flex-shrink: 0;
  }}
  .diff-content {{
    overflow-x: auto;
  }}
  {pygments_css}
  .highlight {{
    background: var(--bg);
    padding: 0;
  }}
  .highlight pre {{
    padding: 10px 20px;
    margin: 0;
    font-family: var(--font-mono);
    font-size: 13px;
    line-height: 1.55;
    white-space: pre-wrap;
    word-wrap: break-word;
  }}
  @media (max-width: 768px) {{
    .commit-header {{ padding: 12px 16px; }}
    .file-list summary {{ padding: 8px 12px; }}
    .highlight pre {{ font-size: 12px; padding: 8px 12px; }}
  }}
</style>
</head>
<body>
  <div class="commit-header">
    <div class="commit-repo">{repo_path}</div>
    <div class="commit-subject">{subject}</div>
    {body_html}
    <div class="commit-meta">
      <span class="hash">{short_hash}</span> · {author_name} &lt;{author_email}&gt; · {date}
    </div>
  </div>
  <div class="file-summary">{file_count} files changed</div>
  <div class="file-list">
    {files_html}
  </div>
</body>
</html>"""
