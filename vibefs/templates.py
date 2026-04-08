"""HTML templates and CSS for vibefs renderers.

Templates are loaded from vibefs/templates/ via Jinja2.
This module provides render_template() and the _dual_pygments_css() utility.
"""

import os

from jinja2 import Environment, FileSystemLoader

_template_dir = os.path.join(os.path.dirname(__file__), 'templates')
_env = Environment(loader=FileSystemLoader(_template_dir), autoescape=True)


def render_template(name, **kwargs):
    """Render a Jinja2 template by name with the given context variables."""
    return _env.get_template(name).render(**kwargs)


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
