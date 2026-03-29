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
<link href="https://fonts.googleapis.com/css2?family=Google+Sans+Flex:wght@100..900&family=Google+Sans+Code:wght@100..700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #0d1117;
    --bg-secondary: #161b22;
    --border: #30363d;
    --text: #e6edf3;
    --text-body: #c9d1d9;
    --text-muted: #8b949e;
    --link: #58a6ff;
    --code-bg: #1f2428;
    --code-color: #f0883e;
    --font-sans: 'Google Sans Flex', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-mono: 'Google Sans Code', 'SF Mono', 'Menlo', 'Monaco', 'Consolas', monospace;
  }}
  @media (prefers-color-scheme: light) {{
    :root {{
      --bg: #ffffff;
      --bg-secondary: #f6f8fa;
      --border: #d0d7de;
      --text: #1f2328;
      --text-body: #1f2328;
      --text-muted: #656d76;
      --link: #0969da;
      --code-bg: #eff1f3;
      --code-color: #cf222e;
    }}
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html {{ overflow-x: hidden; }}
  body {{
    font-family: var(--font-sans);
    font-weight: 400;
    font-synthesis: none;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    overflow-x: hidden;
  }}
  .markdown-body {{
    max-width: 860px;
    margin: 0 auto;
    padding: 40px 24px 32px;
    line-height: 1.7;
  }}
  .markdown-body h1, .markdown-body h2, .markdown-body h3,
  .markdown-body h4, .markdown-body h5, .markdown-body h6 {{
    color: var(--text);
    font-weight: 600;
    line-height: 1.25;
    margin-top: 24px;
    margin-bottom: 12px;
  }}
  .markdown-body h1 {{ font-size: 2em; border-bottom: 1px solid var(--border); padding-bottom: 8px; }}
  .markdown-body h2 {{ font-size: 1.5em; border-bottom: 1px solid var(--border); padding-bottom: 6px; }}
  .markdown-body h3 {{ font-size: 1.25em; }}
  .markdown-body p {{ margin-bottom: 16px; color: var(--text-body); }}
  .markdown-body a {{ color: var(--link); text-decoration: none; }}
  .markdown-body a:hover {{ text-decoration: underline; }}
  .markdown-body strong {{ color: var(--text); font-weight: 600; }}
  .markdown-body em {{ color: var(--text-body); }}
  .markdown-body ul, .markdown-body ol {{
    padding-left: 2em;
    margin-bottom: 16px;
    color: var(--text-body);
  }}
  .markdown-body li {{ margin-bottom: 4px; }}
  .markdown-body li input[type="checkbox"] {{ margin-right: 6px; }}
  .markdown-body blockquote {{
    border-left: 4px solid var(--border);
    padding: 4px 16px;
    color: var(--text-muted);
    margin-bottom: 16px;
  }}
  .markdown-body hr {{
    border: none;
    border-top: 1px solid var(--border);
    margin: 24px 0;
  }}
  .table-wrapper {{
    width: 100%;
    overflow-x: auto;
    margin-bottom: 16px;
  }}
  .markdown-body table {{
    border-collapse: collapse;
    min-width: 100%;
    font-size: 14px;
    margin-bottom: 0;
  }}
  .markdown-body th {{
    background: var(--bg-secondary);
    color: var(--text);
    padding: 8px 16px;
    border: 1px solid var(--border);
    text-align: left;
    font-weight: 600;
    white-space: nowrap;
  }}
  .markdown-body td {{
    padding: 8px 16px;
    border: 1px solid var(--border);
    color: var(--text-body);
  }}
  .markdown-body tr:nth-child(even) td {{ background: var(--bg-secondary); }}
  .markdown-body code {{
    font-family: var(--font-mono);
    font-size: 85%;
    background: var(--code-bg);
    color: var(--code-color);
    padding: 2px 6px;
    border-radius: 4px;
  }}
  .markdown-body pre {{
    margin-bottom: 16px;
    border-radius: 6px;
    overflow: hidden;
  }}
  .markdown-body pre code {{
    background: none;
    color: inherit;
    padding: 0;
    font-size: 14px;
  }}
  {pygments_css}
  .highlight {{
    background: var(--bg-secondary) !important;
    margin: 0;
    border-radius: 0;
  }}
  .highlight pre {{
    padding: 16px;
    margin: 0;
    font-family: var(--font-mono);
    font-size: 14px;
    line-height: 1.6;
    white-space: pre;
    overflow-x: auto;
    color: var(--text);
  }}
  .file-footer {{
    max-width: 860px;
    margin: 0 auto;
    padding: 16px 24px 32px;
    border-top: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 12px;
  }}
  .file-footer-path {{
    font-size: 12px;
    font-family: var(--font-mono);
    color: var(--text-muted);
  }}
  .file-footer-meta {{
    font-size: 12px;
    color: var(--text-muted);
    opacity: 0.6;
  }}
  @media (max-width: 768px) {{
    .markdown-body {{ padding: 24px 16px 24px; }}
    .markdown-body h1 {{ font-size: 1.6em; }}
    .markdown-body h2 {{ font-size: 1.3em; }}
    .file-footer {{ padding: 12px 16px 24px; }}
  }}
</style>
</head>
<body>
  <div class="markdown-body">
    {body_html}
  </div>
  <footer class="file-footer">
    <span class="file-footer-path">{display_path}</span>
    <span class="file-footer-meta">{file_meta}</span>
  </footer>
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


DIR_BROWSER_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow, noarchive, nosnippet">
<title>{dirname} — vibefs</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Google+Sans+Flex:wght@100..900&family=Google+Sans+Code:wght@100..700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #1e1e1e;
    --bg-sidebar: #252526;
    --bg-header: #2d2d2d;
    --bg-hover: #2a2d2e;
    --bg-active: #37373d;
    --border: #404040;
    --text: #d4d4d4;
    --text-header: #e0e0e0;
    --text-muted: #888888;
    --text-dim: #6a6a6a;
    --link: #6ab0f3;
    --accent: #4a9eff;
    --font-sans: 'Google Sans Flex', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-mono: 'Google Sans Code', 'SF Mono', 'Menlo', 'Monaco', 'Consolas', monospace;
  }}
  @media (prefers-color-scheme: light) {{
    :root {{
      --bg: #ffffff;
      --bg-sidebar: #f3f3f3;
      --bg-header: #f6f8fa;
      --bg-hover: #e8e8e8;
      --bg-active: #d6d6d6;
      --border: #d0d7de;
      --text: #1f2328;
      --text-header: #1f2328;
      --text-muted: #656d76;
      --text-dim: #999;
      --link: #0969da;
      --accent: #0969da;
    }}
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ height: 100%; overflow: hidden; }}
  body {{
    font-family: var(--font-sans);
    background: var(--bg);
    color: var(--text);
    display: flex;
    flex-direction: column;
  }}

  /* Header */
  .header {{
    background: var(--bg-header);
    border-bottom: 1px solid var(--border);
    padding: 10px 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    flex-shrink: 0;
    min-height: 44px;
  }}
  .header-title {{
    font-size: 14px;
    font-weight: 600;
    color: var(--text-header);
    font-family: var(--font-mono);
  }}
  .header-meta {{
    font-size: 12px;
    color: var(--text-muted);
    margin-left: auto;
  }}
  .header-meta .countdown {{
    font-family: var(--font-mono);
  }}

  /* Layout */
  .layout {{
    display: flex;
    flex: 1;
    overflow: hidden;
  }}

  /* Sidebar */
  .sidebar {{
    width: 260px;
    min-width: 260px;
    background: var(--bg-sidebar);
    border-right: 1px solid var(--border);
    overflow-y: auto;
    overflow-x: hidden;
    flex-shrink: 0;
  }}
  .sidebar::-webkit-scrollbar {{ width: 6px; }}
  .sidebar::-webkit-scrollbar-track {{ background: transparent; }}
  .sidebar::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
  .search-box {{
    padding: 8px 8px 4px;
    position: sticky;
    top: 0;
    background: var(--bg-sidebar);
    z-index: 1;
  }}
  .search-box input {{
    width: 100%;
    padding: 5px 8px;
    font-size: 12px;
    font-family: var(--font-sans);
    background: var(--bg);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 4px;
    outline: none;
  }}
  .search-box input:focus {{ border-color: var(--accent); }}
  .search-box input::placeholder {{ color: var(--text-dim); }}
  .tree-item.search-hidden {{ display: none; }}
  .tree-group.search-force-open {{ display: block; }}

  .tree-item {{
    display: flex;
    align-items: center;
    padding: 3px 8px;
    cursor: pointer;
    font-size: 13px;
    color: var(--text);
    white-space: nowrap;
    user-select: none;
    border-radius: 0;
    text-decoration: none;
  }}
  .tree-item:hover {{ background: var(--bg-hover); }}
  .tree-item.active {{ background: var(--bg-active); }}
  .tree-item .icon {{
    width: 16px;
    flex-shrink: 0;
    text-align: center;
    font-size: 11px;
    color: var(--text-muted);
    margin-right: 4px;
  }}
  .tree-item .name {{
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .tree-item .size {{
    margin-left: auto;
    padding-left: 8px;
    font-size: 11px;
    color: var(--text-dim);
    font-family: var(--font-mono);
    flex-shrink: 0;
  }}
  .tree-group {{ display: none; }}
  .tree-group.open {{ display: block; }}

  /* Preview */
  .preview {{
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }}
  .preview-empty {{
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-muted);
    font-size: 14px;
  }}
  .preview-loading {{
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-muted);
    font-size: 13px;
  }}
  .preview-frame {{
    flex: 1;
    border: none;
    width: 100%;
    height: 100%;
    background: var(--bg);
  }}
  .preview-image {{
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
    overflow: auto;
    background: var(--bg);
  }}
  .preview-image img {{
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    border-radius: 4px;
  }}
  .preview-binary {{
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    color: var(--text-muted);
  }}
  .preview-binary .filename {{
    font-family: var(--font-mono);
    font-size: 14px;
    color: var(--text);
  }}
  .preview-binary .dl-btn {{
    display: inline-block;
    background: var(--accent);
    color: #fff;
    text-decoration: none;
    padding: 8px 20px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
  }}
  .preview-binary .dl-btn:hover {{ opacity: 0.9; }}

  /* Mobile */
  .sidebar-toggle {{
    display: none;
    background: none;
    border: none;
    color: var(--text-header);
    font-size: 18px;
    cursor: pointer;
    padding: 4px;
  }}
  @media (max-width: 768px) {{
    .sidebar-toggle {{ display: block; }}
    .sidebar {{
      position: fixed;
      left: 0;
      top: 44px;
      bottom: 0;
      z-index: 100;
      transform: translateX(-100%);
      transition: transform 0.2s ease;
      box-shadow: 2px 0 8px rgba(0,0,0,0.3);
    }}
    .sidebar.mobile-open {{
      transform: translateX(0);
    }}
  }}

  /* Breadcrumb */
  .breadcrumb {{
    padding: 6px 16px;
    font-size: 12px;
    font-family: var(--font-mono);
    color: var(--text-muted);
    background: var(--bg-header);
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
</style>
</head>
<body>
  <div class="header">
    <button class="sidebar-toggle" onclick="toggleSidebar()" aria-label="Toggle sidebar">&#9776;</button>
    <span class="header-title">{dirname}</span>
    <span class="header-meta">expires in <span class="countdown" id="countdown"></span></span>
  </div>
  <div class="layout">
    <nav class="sidebar" id="sidebar">
      <div class="search-box"><input type="text" id="search" placeholder="Filter files\u2026" autocomplete="off" spellcheck="false"></div>
      <div id="tree-container"></div>
    </nav>
    <main class="preview" id="preview">
      <div class="preview-empty">Select a file to preview</div>
    </main>
  </div>

<script>
(function() {{
  var TREE = {tree_json};
  var TOKEN = '{token}';
  var EXPIRES = {expires_at};
  var INITIAL_FILE = '{initial_file}';
  var BASE = '{base_path}';

  var activeEl = null;
  var currentFile = null;

  function updateCountdown() {{
    var now = Date.now() / 1000;
    var remaining = Math.max(0, EXPIRES - now);
    if (remaining <= 0) {{
      document.getElementById('countdown').textContent = 'expired';
      return;
    }}
    var h = Math.floor(remaining / 3600);
    var m = Math.floor((remaining % 3600) / 60);
    var s = Math.floor(remaining % 60);
    var parts = [];
    if (h > 0) parts.push(h + 'h');
    if (m > 0 || h > 0) parts.push(m + 'm');
    parts.push(s + 's');
    document.getElementById('countdown').textContent = parts.join(' ');
  }}
  updateCountdown();
  setInterval(updateCountdown, 1000);

  function fmtSize(n) {{
    if (n < 1024) return n + ' B';
    if (n < 1048576) return (n / 1024).toFixed(1) + ' KB';
    if (n < 1073741824) return (n / 1048576).toFixed(1) + ' MB';
    return (n / 1073741824).toFixed(1) + ' GB';
  }}

  function fileIcon(name) {{
    var ext = name.includes('.') ? name.split('.').pop().toLowerCase() : '';
    var m = {{md:'\\ud83d\\udcdd',txt:'\\ud83d\\udcc4',json:'\\ud83d\\udccb',yaml:'\\ud83d\\udccb',yml:'\\ud83d\\udccb',toml:'\\ud83d\\udccb',py:'\\ud83d\\udc0d',js:'\\ud83d\\udcdc',ts:'\\ud83d\\udcdc',go:'\\ud83d\\udd35',rs:'\\ud83e\\udd80',rb:'\\ud83d\\udc8e',html:'\\ud83c\\udf10',css:'\\ud83c\\udfa8',svg:'\\ud83c\\udfa8',png:'\\ud83d\\uddbc',jpg:'\\ud83d\\uddbc',jpeg:'\\ud83d\\uddbc',gif:'\\ud83d\\uddbc',webp:'\\ud83d\\uddbc',avif:'\\ud83d\\uddbc',sh:'\\u26a1',bash:'\\u26a1',zsh:'\\u26a1'}};
    return m[ext] || '\\ud83d\\udcc4';
  }}

  function escHtml(s) {{
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }}

  var sidebar = document.getElementById('sidebar');
  var treeContainer = document.getElementById('tree-container');
  function renderTree(node, container, depth) {{
    if (!node.children) return;
    node.children.forEach(function(child) {{
      var item = document.createElement('div');
      item.className = 'tree-item';
      item.style.paddingLeft = (8 + depth * 16) + 'px';

      if (child.is_dir) {{
        var group = document.createElement('div');
        group.className = 'tree-group';
        item.innerHTML = '<span class="icon">\\u25b6</span><span class="name">' + escHtml(child.name) + '</span>';
        item.onclick = function(e) {{
          e.stopPropagation();
          var open = group.classList.toggle('open');
          item.querySelector('.icon').textContent = open ? '\\u25bc' : '\\u25b6';
        }};
        container.appendChild(item);
        container.appendChild(group);
        renderTree(child, group, depth + 1);
      }} else {{
        item.innerHTML = '<span class="icon">' + fileIcon(child.name) + '</span>'
          + '<span class="name">' + escHtml(child.name) + '</span>'
          + '<span class="size">' + fmtSize(child.size) + '</span>';
        item.dataset.path = child.rel_path;
        item.onclick = function(e) {{
          e.stopPropagation();
          selectFile(child.rel_path, item);
        }};
        container.appendChild(item);
      }}
    }});
  }}

  renderTree(TREE, treeContainer, 0);

  // File search/filter
  var searchInput = document.getElementById('search');
  searchInput.addEventListener('input', function() {{
    var q = searchInput.value.toLowerCase().trim();
    var items = treeContainer.querySelectorAll('.tree-item');
    var groups = treeContainer.querySelectorAll('.tree-group');

    if (!q) {{
      // Reset: show all, collapse groups back
      for (var i = 0; i < items.length; i++) items[i].classList.remove('search-hidden');
      for (var i = 0; i < groups.length; i++) groups[i].classList.remove('search-force-open');
      return;
    }}

    // First pass: hide all items, find matching files
    var matchedGroups = new Set();
    for (var i = 0; i < items.length; i++) {{
      var item = items[i];
      var nameEl = item.querySelector('.name');
      if (!nameEl) continue;
      var isFile = !!item.dataset.path;
      if (isFile && nameEl.textContent.toLowerCase().indexOf(q) !== -1) {{
        item.classList.remove('search-hidden');
        // Reveal all parent groups
        var parent = item.parentElement;
        while (parent && parent !== treeContainer) {{
          if (parent.classList.contains('tree-group')) matchedGroups.add(parent);
          parent = parent.parentElement;
        }}
      }} else if (isFile) {{
        item.classList.add('search-hidden');
      }} else {{
        // Directory items: will be shown/hidden based on children
        item.classList.add('search-hidden');
      }}
    }}

    // Second pass: show/open groups that contain matches
    for (var i = 0; i < groups.length; i++) {{
      if (matchedGroups.has(groups[i])) {{
        groups[i].classList.add('search-force-open');
        // Show the directory item before this group
        var prev = groups[i].previousElementSibling;
        if (prev && prev.classList.contains('tree-item')) prev.classList.remove('search-hidden');
      }} else {{
        groups[i].classList.remove('search-force-open');
      }}
    }}
  }});

  function selectFile(relPath, el) {{
    if (currentFile === relPath) return;
    currentFile = relPath;

    if (activeEl) activeEl.classList.remove('active');
    if (el) {{ el.classList.add('active'); activeEl = el; }}

    document.getElementById('sidebar').classList.remove('mobile-open');

    var preview = document.getElementById('preview');
    preview.innerHTML = '<div class="preview-loading">Loading\\u2026</div>';

    var newUrl = BASE + '/d/' + TOKEN + '/' + relPath;
    history.replaceState(null, '', newUrl);

    fetch(BASE + '/d/' + TOKEN + '/api/file?path=' + encodeURIComponent(relPath))
      .then(function(r) {{ if (!r.ok) throw new Error(r.status); return r.json(); }})
      .then(function(data) {{
        var bc = '<div class="breadcrumb">' + breadcrumb(relPath) + '</div>';
        if (data.type === 'html') {{
          preview.innerHTML = bc + '<iframe class="preview-frame" sandbox="allow-same-origin"></iframe>';
          var iframe = preview.querySelector('iframe');
          iframe.srcdoc = data.content;
        }} else if (data.type === 'image') {{
          preview.innerHTML = bc + '<div class="preview-image"><img src="' + escHtml(data.url) + '" alt="' + escHtml(relPath) + '"></div>';
        }} else {{
          preview.innerHTML = bc + '<div class="preview-binary">'
            + '<div class="filename">' + escHtml(data.filename) + '</div>'
            + '<div>' + fmtSize(data.size) + '</div>'
            + '<a class="dl-btn" href="' + escHtml(data.url) + '" download>Download</a></div>';
        }}
      }})
      .catch(function(err) {{
        preview.innerHTML = '<div class="preview-empty">Failed to load: ' + escHtml(relPath) + '</div>';
      }});
  }}

  function breadcrumb(relPath) {{
    var parts = relPath.split('/');
    var html = escHtml(TREE.name);
    for (var i = 0; i < parts.length - 1; i++) {{
      html += ' / ' + escHtml(parts[i]);
    }}
    html += ' / ' + escHtml(parts[parts.length - 1]);
    return html;
  }}

  window.toggleSidebar = function() {{
    document.getElementById('sidebar').classList.toggle('mobile-open');
  }};

  if (INITIAL_FILE) {{
    var parts = INITIAL_FILE.split('/');
    var current = treeContainer;
    for (var i = 0; i < parts.length - 1; i++) {{
      var items = current.querySelectorAll(':scope > .tree-item');
      for (var j = 0; j < items.length; j++) {{
        var nameEl = items[j].querySelector('.name');
        if (nameEl && nameEl.textContent === parts[i]) {{
          var group = items[j].nextElementSibling;
          if (group && group.classList.contains('tree-group')) {{
            group.classList.add('open');
            items[j].querySelector('.icon').textContent = '\\u25bc';
            current = group;
          }}
          break;
        }}
      }}
    }}
    var fileItems = treeContainer.querySelectorAll('.tree-item[data-path]');
    for (var k = 0; k < fileItems.length; k++) {{
      if (fileItems[k].dataset.path === INITIAL_FILE) {{
        selectFile(INITIAL_FILE, fileItems[k]);
        fileItems[k].scrollIntoView({{ block: 'center' }});
        break;
      }}
    }}
  }}
}})();
</script>
</body>
</html>"""


OWNER_LOGIN_TEMPLATE = (
    '<!DOCTYPE html><html><head>'
    + BASE_HEAD
    + '<meta name="robots" content="noindex, nofollow">'
    '<title>Owner Login — vibefs</title><style>'
    + VERIFY_PAGE_CSS
    + '</style></head><body><div class="container">'
    '<h1>Owner Login</h1>'
    '<p class="hint">Enter password for full access</p>'
    '<form method="POST" action="/owner/login">'
    '<input type="hidden" name="next" value="{{next}}">'
    '<input type="password" name="password" placeholder="Password" autofocus>'
    '<button type="submit">Login</button>\n'
    '% if error:\n'
    '<p class="error">{{error}}</p>\n'
    '% end\n'
    '</form></div></body></html>'
)


DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Dashboard — vibefs</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Google+Sans+Flex:wght@100..900&family=Google+Sans+Code:wght@100..700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #1e1e1e;
    --bg-header: #2d2d2d;
    --bg-row: #252526;
    --bg-row-hover: #2a2d2e;
    --border: #404040;
    --text: #d4d4d4;
    --text-header: #e0e0e0;
    --text-muted: #888888;
    --link: #6ab0f3;
    --green: #4ec994;
    --red: #f4796b;
    --font-sans: 'Google Sans Flex', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-mono: 'Google Sans Code', 'SF Mono', 'Menlo', 'Monaco', 'Consolas', monospace;
  }}
  @media (prefers-color-scheme: light) {{
    :root {{
      --bg: #ffffff;
      --bg-header: #f6f8fa;
      --bg-row: #ffffff;
      --bg-row-hover: #f6f8fa;
      --border: #d0d7de;
      --text: #1f2328;
      --text-header: #1f2328;
      --text-muted: #656d76;
      --link: #0969da;
      --green: #1a7f37;
      --red: #cf222e;
    }}
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: var(--font-sans);
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }}
  .page-header {{
    background: var(--bg-header);
    border-bottom: 1px solid var(--border);
    padding: 16px 24px;
  }}
  .page-header h1 {{
    font-size: 18px;
    font-weight: 600;
    color: var(--text-header);
  }}
  .page-header .subtitle {{
    font-size: 13px;
    color: var(--text-muted);
    margin-top: 4px;
  }}
  .shares-table {{
    width: 100%;
    border-collapse: collapse;
  }}
  .shares-table th {{
    background: var(--bg-header);
    text-align: left;
    padding: 8px 16px;
    font-size: 12px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid var(--border);
  }}
  .shares-table td {{
    padding: 10px 16px;
    font-size: 13px;
    border-bottom: 1px solid var(--border);
    background: var(--bg-row);
  }}
  .shares-table tr:hover td {{ background: var(--bg-row-hover); }}
  .shares-table .type-badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
  }}
  .type-file {{ background: #2d4a7a; color: #8bb9fe; }}
  .type-dir {{ background: #2d5a3a; color: #7cda9c; }}
  .type-git {{ background: #5a3a2d; color: #daa07c; }}
  @media (prefers-color-scheme: light) {{
    .type-file {{ background: #dbeafe; color: #1e40af; }}
    .type-dir {{ background: #dcfce7; color: #166534; }}
    .type-git {{ background: #fef3c7; color: #92400e; }}
  }}
  .shares-table .path {{
    font-family: var(--font-mono);
    font-size: 12px;
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }}
  .shares-table .token-link {{
    font-family: var(--font-mono);
    color: var(--link);
    text-decoration: none;
  }}
  .shares-table .token-link:hover {{ text-decoration: underline; }}
  .status-active {{ color: var(--green); }}
  .status-expired {{ color: var(--red); opacity: 0.7; }}
  .expired-row td {{ opacity: 0.5; }}
  .empty-state {{
    text-align: center;
    padding: 60px 24px;
    color: var(--text-muted);
  }}
  @media (max-width: 768px) {{
    .shares-table {{ font-size: 12px; }}
    .shares-table th, .shares-table td {{ padding: 8px 10px; }}
  }}
</style>
</head>
<body>
  <div class="page-header">
    <h1>vibefs dashboard</h1>
    <div class="subtitle">{share_count} shares ({active_count} active)</div>
  </div>
  % if not shares:
  <div class="empty-state">No shares yet</div>
  % else:
  <table class="shares-table">
    <thead>
      <tr><th>Type</th><th>Path</th><th>Token</th><th>Created</th><th>Expires</th><th>Status</th></tr>
    </thead>
    <tbody>
      % for s in shares:
      <tr class="{{'expired-row' if s['status'] == 'expired' else ''}}">
        <td><span class="type-badge type-{{s['type']}}">{{s['type']}}</span></td>
        <td class="path" title="{{s['path']}}">{{s['display_path']}}</td>
        <td><a class="token-link" href="{{s['url']}}">{{s['token'][:8]}}…</a></td>
        <td>{{s['created_str']}}</td>
        <td>{{s['expires_str']}}</td>
        <td class="status-{{s['status']}}">{{s['status']}}</td>
      </tr>
      % end
    </tbody>
  </table>
  % end
</body>
</html>"""
