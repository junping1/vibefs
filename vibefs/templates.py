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
