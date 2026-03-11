import os


def _display_path(filepath):
    home = os.path.expanduser('~')
    if filepath.startswith(home + '/'):
        return '~/' + filepath[len(home) + 1:]
    return filepath


def _format_size(nbytes):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if nbytes < 1024:
            return f'{nbytes:.0f} {unit}' if unit == 'B' else f'{nbytes:.1f} {unit}'
        nbytes /= 1024
    return f'{nbytes:.1f} TB'


def _html_escape(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
