import mimetypes
import os
import time

import bottle

from .config import load_config
from .utils import _display_path, _format_size
from .templates import MARKDOWN_HTML_TEMPLATE, CODE_HTML_TEMPLATE, _dual_pygments_css


class BaseRenderer:
    """Default renderer: returns raw file content with guessed content-type."""

    def render(self, filepath, head=None, tail=None):
        content_type, _ = mimetypes.guess_type(filepath)
        if content_type is None:
            content_type = 'application/octet-stream'
        bottle.response.content_type = content_type
        if head is not None or tail is not None:
            with open(filepath) as f:
                lines = f.readlines()
            if head is not None:
                lines = lines[:head]
            elif tail is not None:
                lines = lines[-tail:]
            return ''.join(lines)
        with open(filepath, 'rb') as f:
            return f.read()


class MarkdownRenderer:
    """Renders Markdown files as styled HTML using markdown-it-py."""

    def render(self, filepath, head=None, tail=None):
        from markdown_it import MarkdownIt
        from mdit_py_plugins.tasklists import tasklists_plugin
        from pygments import highlight
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import get_lexer_by_name, TextLexer

        with open(filepath) as f:
            lines = f.readlines()

        if head is not None:
            lines = lines[:head]
        elif tail is not None:
            lines = lines[-tail:]
        source = ''.join(lines)

        pygments_css = _dual_pygments_css(nowrap=False)
        formatter = HtmlFormatter(style='github-dark', cssclass='highlight', nowrap=False)

        def highlight_code(code, lang, attrs):
            try:
                lexer = get_lexer_by_name(lang) if lang else TextLexer()
            except Exception:
                lexer = TextLexer()
            return highlight(code, lexer, formatter)

        md = (
            MarkdownIt('gfm-like', {'highlight': highlight_code})
            .use(tasklists_plugin)
        )
        body_html = md.render(source)
        body_html = body_html.replace('<table>', '<div class="table-wrapper"><table>').replace('</table>', '</table></div>')

        display_path = _display_path(filepath)
        stat = os.stat(filepath)
        file_size = _format_size(stat.st_size)
        file_mtime = time.strftime('%Y-%m-%d %H:%M', time.localtime(stat.st_mtime))

        bottle.response.content_type = 'text/html; charset=utf-8'
        return MARKDOWN_HTML_TEMPLATE.format(
            display_path=display_path,
            file_meta=f'{file_size} · {file_mtime}',
            pygments_css=pygments_css,
            body_html=body_html,
        )


class CodeRenderer:
    """Renders code files with syntax highlighting via Pygments."""

    def render(self, filepath, head=None, tail=None):
        from pygments import highlight
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import get_lexer_for_filename, TextLexer

        with open(filepath) as f:
            lines = f.readlines()

        if head is not None:
            lines = lines[:head]
        elif tail is not None:
            lines = lines[-tail:]
        code = ''.join(lines)

        try:
            lexer = get_lexer_for_filename(filepath)
        except Exception:
            lexer = TextLexer()

        cfg = load_config()
        pygments_cfg = cfg.get('pygments', {})
        linenos = 'inline' if pygments_cfg.get('linenos', False) else False

        formatter = HtmlFormatter(
            style='github-dark',
            linenos=linenos,
            cssclass='highlight',
        )
        highlighted = highlight(code, lexer, formatter)
        css = _dual_pygments_css(linenos=linenos)
        display_path = _display_path(filepath)
        stat = os.stat(filepath)
        file_size = _format_size(stat.st_size)
        file_mtime = time.strftime('%Y-%m-%d %H:%M', time.localtime(stat.st_mtime))
        file_ctime = time.strftime(
            '%Y-%m-%d %H:%M', time.localtime(stat.st_birthtime if hasattr(stat, 'st_birthtime') else stat.st_ctime)
        )

        bottle.response.content_type = 'text/html; charset=utf-8'
        return CODE_HTML_TEMPLATE.format(
            display_path=display_path,
            file_meta=f'{file_size} · {file_mtime} (mtime) · {file_ctime} (ctime)',
            pygments_css=css,
            highlighted=highlighted,
        )


CODE_EXTENSIONS = [
    '.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.rb', '.java',
    '.c', '.cpp', '.h', '.hpp', '.cs', '.swift', '.kt', '.scala',
    '.sh', '.bash', '.zsh', '.fish',
    '.html', '.css', '.scss', '.less',
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.xml',
    '.sql', '.graphql', '.md', '.rst', '.txt',
    '.lua', '.vim', '.el', '.clj', '.hs', '.ml', '.ex', '.exs',
    '.r', '.R', '.jl', '.pl', '.pm', '.php',
    '.dockerfile', '.makefile', '.cmake', '.conf', '.env',
    '.gitignore', '.diff', '.patch',
]

_renderers = {}
_fallback_renderer = BaseRenderer()


def init_renderers():
    """Register renderers for known extensions."""
    code_renderer = CodeRenderer()
    markdown_renderer = MarkdownRenderer()
    for ext in CODE_EXTENSIONS:
        _renderers[ext] = code_renderer
    _renderers['.md'] = markdown_renderer
    _renderers['.markdown'] = markdown_renderer


def get_renderer(filepath):
    """Get the appropriate renderer for a file, falling back to BaseRenderer."""
    _, ext = os.path.splitext(filepath)
    return _renderers.get(ext.lower(), _fallback_renderer)


init_renderers()
