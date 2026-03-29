import fnmatch
import os
import threading
import time

from .constants import MAX_DIR_FILES

# Simple TTL cache for walk_directory results
_tree_cache = {}  # key: (dirpath, excludes_tuple) -> (tree, timestamp)
_tree_cache_lock = threading.Lock()
_TREE_CACHE_TTL = 30  # seconds


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


def _js_safe_json(obj):
    """Serialize to JSON and escape sequences that break <script> context.

    Prevents XSS via filenames containing </script>, <!--, etc.
    """
    import json
    s = json.dumps(obj)
    # Escape sequences that could break out of <script> tags
    s = s.replace('</', '<\\/')
    s = s.replace('<!--', '<\\!--')
    return s


def _js_string_escape(text):
    """Escape a string for safe embedding inside a JS single-quoted string literal.

    Handles: backslash, single quotes, newlines, and </script> injection.
    """
    text = text.replace('\\', '\\\\')
    text = text.replace("'", "\\'")
    text = text.replace('"', '\\"')
    text = text.replace('\n', '\\n')
    text = text.replace('\r', '\\r')
    text = text.replace('</', '<\\/')
    return text


def is_safe_subpath(base, target):
    """Check that target is strictly inside base. Prevents path traversal."""
    base_real = os.path.realpath(base)
    target_real = os.path.realpath(target)
    return target_real == base_real or target_real.startswith(base_real + os.sep)


def _is_excluded(name, is_dir, excludes):
    """Check if a file/directory name matches any exclude pattern."""
    for pattern in excludes:
        if pattern.endswith('/'):
            if is_dir and fnmatch.fnmatch(name, pattern.rstrip('/')):
                return True
        else:
            if fnmatch.fnmatch(name, pattern):
                return True
    return False


def walk_directory(dirpath, excludes):
    """Walk directory recursively, returning a nested tree structure.

    Returns dict: {name, rel_path, is_dir, size, children}
    Refuses to follow symlinks that escape the base directory.
    Raises ValueError if file count exceeds MAX_DIR_FILES.
    Results are cached for _TREE_CACHE_TTL seconds to avoid redundant scans.
    """
    cache_key = (os.path.realpath(dirpath), tuple(excludes))
    now = time.time()
    with _tree_cache_lock:
        cached = _tree_cache.get(cache_key)
        if cached and now - cached[1] < _TREE_CACHE_TTL:
            return cached[0]

    tree = _walk_directory_uncached(dirpath, excludes)

    with _tree_cache_lock:
        # Evict stale entries while we're here
        stale = [k for k, (_, ts) in _tree_cache.items() if now - ts > _TREE_CACHE_TTL * 2]
        for k in stale:
            del _tree_cache[k]
        _tree_cache[cache_key] = (tree, now)

    return tree


def _walk_directory_uncached(dirpath, excludes):
    """Internal: walk directory without caching."""
    base_real = os.path.realpath(dirpath)
    file_count = 0

    def _walk(current_path, rel_prefix):
        nonlocal file_count
        children = []

        try:
            entries = sorted(os.scandir(current_path), key=lambda e: (not e.is_dir(follow_symlinks=False), e.name.lower()))
        except PermissionError:
            return children

        for entry in entries:
            is_dir = entry.is_dir(follow_symlinks=False)
            is_link = entry.is_symlink()

            if _is_excluded(entry.name, is_dir, excludes):
                continue

            # For symlinks, check they don't escape the base directory
            if is_link:
                real_target = os.path.realpath(entry.path)
                if not is_safe_subpath(base_real, real_target):
                    continue
                # Re-check if symlink target is actually a dir
                is_dir = os.path.isdir(real_target)

            rel_path = os.path.join(rel_prefix, entry.name) if rel_prefix else entry.name

            if is_dir:
                sub_children = _walk(entry.path, rel_path)
                children.append({
                    'name': entry.name,
                    'rel_path': rel_path,
                    'is_dir': True,
                    'size': 0,
                    'children': sub_children,
                })
            else:
                file_count += 1
                if file_count > MAX_DIR_FILES:
                    raise ValueError(f'Directory contains more than {MAX_DIR_FILES} files. Use --exclude to narrow scope.')
                try:
                    size = entry.stat(follow_symlinks=True).st_size
                except OSError:
                    size = 0
                children.append({
                    'name': entry.name,
                    'rel_path': rel_path,
                    'is_dir': False,
                    'size': size,
                    'children': [],
                })

        return children

    dirname = os.path.basename(dirpath)
    return {
        'name': dirname,
        'rel_path': '',
        'is_dir': True,
        'size': 0,
        'children': _walk(dirpath, ''),
    }


IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico', '.bmp', '.avif'}


PDF_EXTENSIONS = {'.pdf'}
MEDIA_EXTENSIONS = {
    '.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a', '.opus', '.weba',
    '.mp4', '.webm', '.ogv', '.mov', '.avi', '.mkv',
}
CSV_EXTENSIONS = {'.csv', '.tsv', '.tab'}


def get_file_type(filepath):
    """Determine the file type category for preview purposes.

    Returns: 'image', 'markdown', 'code', 'csv', 'pdf', 'media', 'svg', or 'binary'.
    """
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()
    if ext == '.svg':
        return 'svg'
    if ext in IMAGE_EXTENSIONS:
        return 'image'
    if ext in PDF_EXTENSIONS:
        return 'pdf'
    if ext in MEDIA_EXTENSIONS:
        return 'media'
    if ext in CSV_EXTENSIONS:
        return 'csv'
    from .renderers import _renderers, MarkdownRenderer
    renderer = _renderers.get(ext)
    if isinstance(renderer, MarkdownRenderer):
        return 'markdown'
    if renderer is not None:
        return 'code'
    return 'binary'
