import json
import os
import secrets
import sqlite3
import subprocess
import time

from .constants import DB_PATH, TOKEN_LENGTH, DIR_TOKEN_LENGTH


_db_initialized = False


def get_db_path():
    return os.environ.get('VIBEFS_DB', DB_PATH)


def _ensure_tables(db):
    global _db_initialized
    if _db_initialized:
        return
    db.execute("""
        CREATE TABLE IF NOT EXISTS authorizations (
            token TEXT PRIMARY KEY,
            filepath TEXT NOT NULL,
            filename TEXT NOT NULL,
            created_at REAL NOT NULL,
            expires_at REAL NOT NULL,
            live INTEGER NOT NULL DEFAULT 0
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS git_authorizations (
            token TEXT PRIMARY KEY,
            repo_path TEXT NOT NULL,
            commit_hash TEXT NOT NULL,
            created_at REAL NOT NULL,
            expires_at REAL NOT NULL
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS dir_authorizations (
            token TEXT PRIMARY KEY,
            dirpath TEXT NOT NULL,
            dirname TEXT NOT NULL,
            excludes TEXT NOT NULL,
            created_at REAL NOT NULL,
            expires_at REAL NOT NULL,
            live INTEGER NOT NULL DEFAULT 0
        )
    """)
    # Migrate: add live column if missing (existing databases)
    for table in ('authorizations', 'dir_authorizations'):
        try:
            db.execute(f'ALTER TABLE {table} ADD COLUMN live INTEGER NOT NULL DEFAULT 0')
        except sqlite3.OperationalError:
            pass  # column already exists
    db.commit()
    _db_initialized = True


def get_db():
    db = sqlite3.connect(get_db_path())
    db.row_factory = sqlite3.Row
    _ensure_tables(db)
    return db


def add_authorization(filepath, ttl, live=False):
    """Add an authorization record and return (token, filename, is_new)."""
    abs_path = os.path.abspath(filepath)
    if not os.path.isfile(abs_path):
        raise FileNotFoundError(f'File not found: {abs_path}')

    filename = os.path.basename(abs_path)
    now = time.time()

    db = get_db()
    row = db.execute(
        'SELECT token FROM authorizations WHERE filepath = ? AND expires_at > ?',
        (abs_path, now),
    ).fetchone()

    if row:
        token = row['token']
        db.execute(
            'UPDATE authorizations SET expires_at = ?, live = ? WHERE token = ?',
            (now + ttl, int(live), token),
        )
        db.commit()
        db.close()
        return token, filename, False
    else:
        token = secrets.token_hex(TOKEN_LENGTH)
        db.execute(
            'INSERT INTO authorizations (token, filepath, filename, created_at, expires_at, live) VALUES (?, ?, ?, ?, ?, ?)',
            (token, abs_path, filename, now, now + ttl, int(live)),
        )
        db.commit()
        db.close()
        return token, filename, True


def remove_authorization(token):
    """Remove an authorization record. Returns True if it existed."""
    db = get_db()
    cursor = db.execute('DELETE FROM authorizations WHERE token = ?', (token,))
    db.commit()
    deleted = cursor.rowcount > 0
    db.close()
    return deleted


def list_authorizations():
    """Return all authorization records."""
    db = get_db()
    rows = db.execute(
        'SELECT token, filepath, filename, created_at, expires_at FROM authorizations ORDER BY created_at DESC'
    ).fetchall()
    db.close()
    return rows


def lookup_authorization(token):
    """Look up a token. Returns (row, status) where status is 'valid', 'expired', or 'not_found'."""
    db = get_db()
    row = db.execute(
        'SELECT token, filepath, filename, created_at, expires_at, live FROM authorizations WHERE token = ?',
        (token,),
    ).fetchone()
    db.close()

    if row is None:
        return None, 'not_found'
    if time.time() > row['expires_at']:
        return row, 'expired'
    return row, 'valid'


def has_active_authorizations():
    """Check if there are any non-expired authorizations (files, git, or dirs)."""
    db = get_db()
    now = time.time()
    file_cnt = db.execute(
        'SELECT COUNT(*) as cnt FROM authorizations WHERE expires_at > ?',
        (now,),
    ).fetchone()['cnt']
    git_cnt = db.execute(
        'SELECT COUNT(*) as cnt FROM git_authorizations WHERE expires_at > ?',
        (now,),
    ).fetchone()['cnt']
    dir_cnt = db.execute(
        'SELECT COUNT(*) as cnt FROM dir_authorizations WHERE expires_at > ?',
        (now,),
    ).fetchone()['cnt']
    db.close()
    return (file_cnt + git_cnt + dir_cnt) > 0


def add_git_authorization(repo_path, commit_hash, ttl):
    """Add a git commit authorization record and return (token, is_new)."""
    abs_repo = os.path.abspath(repo_path)
    if not os.path.isdir(os.path.join(abs_repo, '.git')):
        raise ValueError(f'Not a git repository: {abs_repo}')

    now = time.time()
    db = get_db()
    row = db.execute(
        'SELECT token FROM git_authorizations WHERE repo_path = ? AND commit_hash = ? AND expires_at > ?',
        (abs_repo, commit_hash, now),
    ).fetchone()

    if row:
        token = row['token']
        db.execute(
            'UPDATE git_authorizations SET expires_at = ? WHERE token = ?',
            (now + ttl, token),
        )
        db.commit()
        db.close()
        return token, False
    else:
        token = secrets.token_hex(TOKEN_LENGTH)
        db.execute(
            'INSERT INTO git_authorizations (token, repo_path, commit_hash, created_at, expires_at) VALUES (?, ?, ?, ?, ?)',
            (token, abs_repo, commit_hash, now, now + ttl),
        )
        db.commit()
        db.close()
        return token, True


def lookup_git_authorization(token):
    """Look up a git token. Returns (row, status)."""
    db = get_db()
    row = db.execute(
        'SELECT token, repo_path, commit_hash, created_at, expires_at FROM git_authorizations WHERE token = ?',
        (token,),
    ).fetchone()
    db.close()

    if row is None:
        return None, 'not_found'
    if time.time() > row['expires_at']:
        return row, 'expired'
    return row, 'valid'


def get_git_commit_info(repo_path, commit_hash):
    """Get commit info via git commands. Returns dict with metadata and file diffs."""
    result = subprocess.run(
        ['git', 'log', '-1', '--format=%H%n%an%n%ae%n%aI%n%s%n%b', commit_hash],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    )
    lines = result.stdout.strip().split('\n', 5)
    info = {
        'hash': lines[0] if len(lines) > 0 else commit_hash,
        'author_name': lines[1] if len(lines) > 1 else '',
        'author_email': lines[2] if len(lines) > 2 else '',
        'date': lines[3] if len(lines) > 3 else '',
        'subject': lines[4] if len(lines) > 4 else '',
        'body': lines[5].strip() if len(lines) > 5 else '',
    }

    result = subprocess.run(
        ['git', 'diff-tree', '--no-commit-id', '-r', '--numstat', commit_hash],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    )
    files = []
    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        parts = line.split('\t', 2)
        if len(parts) == 3:
            added, deleted, filepath = parts
            files.append({'path': filepath, 'added': added, 'deleted': deleted})

    for f in files:
        try:
            result = subprocess.run(
                ['git', 'diff', f'{commit_hash}~1', commit_hash, '--', f['path']],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            f['diff'] = result.stdout
        except subprocess.CalledProcessError:
            try:
                result = subprocess.run(
                    ['git', 'show', f'{commit_hash}', '--', f['path']],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                f['diff'] = result.stdout
            except subprocess.CalledProcessError:
                f['diff'] = ''

    info['files'] = files
    return info


def add_dir_authorization(dirpath, ttl, excludes, live=False):
    """Add a directory authorization record and return (token, dirname, is_new)."""
    abs_path = os.path.abspath(dirpath)
    if not os.path.isdir(abs_path):
        raise FileNotFoundError(f'Directory not found: {abs_path}')

    dirname = os.path.basename(abs_path)
    now = time.time()
    excludes_json = json.dumps(excludes)

    db = get_db()
    row = db.execute(
        'SELECT token FROM dir_authorizations WHERE dirpath = ? AND expires_at > ?',
        (abs_path, now),
    ).fetchone()

    if row:
        token = row['token']
        db.execute(
            'UPDATE dir_authorizations SET expires_at = ?, excludes = ?, live = ? WHERE token = ?',
            (now + ttl, excludes_json, int(live), token),
        )
        db.commit()
        db.close()
        return token, dirname, False
    else:
        token = secrets.token_hex(DIR_TOKEN_LENGTH)
        db.execute(
            'INSERT INTO dir_authorizations (token, dirpath, dirname, excludes, created_at, expires_at, live) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (token, abs_path, dirname, excludes_json, now, now + ttl, int(live)),
        )
        db.commit()
        db.close()
        return token, dirname, True


def lookup_dir_authorization(token):
    """Look up a directory token. Returns (row, status)."""
    db = get_db()
    row = db.execute(
        'SELECT token, dirpath, dirname, excludes, created_at, expires_at, live FROM dir_authorizations WHERE token = ?',
        (token,),
    ).fetchone()
    db.close()

    if row is None:
        return None, 'not_found'
    if time.time() > row['expires_at']:
        return row, 'expired'
    return row, 'valid'


def list_dir_authorizations():
    """Return all directory authorization records."""
    db = get_db()
    rows = db.execute(
        'SELECT token, dirpath, dirname, excludes, created_at, expires_at FROM dir_authorizations ORDER BY created_at DESC'
    ).fetchall()
    db.close()
    return rows


def list_all_authorizations():
    """Return all authorizations (files, git, dirs) for the dashboard."""
    db = get_db()
    now = time.time()
    results = []

    for row in db.execute('SELECT token, filepath, filename, created_at, expires_at FROM authorizations ORDER BY created_at DESC').fetchall():
        results.append({'type': 'file', 'token': row['token'], 'path': row['filepath'], 'name': row['filename'],
                        'created_at': row['created_at'], 'expires_at': row['expires_at'], 'status': 'active' if row['expires_at'] > now else 'expired'})

    for row in db.execute('SELECT token, repo_path, commit_hash, created_at, expires_at FROM git_authorizations ORDER BY created_at DESC').fetchall():
        results.append({'type': 'git', 'token': row['token'], 'path': row['repo_path'], 'name': row['commit_hash'][:12],
                        'created_at': row['created_at'], 'expires_at': row['expires_at'], 'status': 'active' if row['expires_at'] > now else 'expired'})

    for row in db.execute('SELECT token, dirpath, dirname, created_at, expires_at FROM dir_authorizations ORDER BY created_at DESC').fetchall():
        results.append({'type': 'dir', 'token': row['token'], 'path': row['dirpath'], 'name': row['dirname'],
                        'created_at': row['created_at'], 'expires_at': row['expires_at'], 'status': 'active' if row['expires_at'] > now else 'expired'})

    results.sort(key=lambda x: x['created_at'], reverse=True)
    db.close()
    return results


def cleanup_expired_shares():
    """Delete temp share files whose authorizations have expired."""
    from .constants import SHARES_DIR
    if not os.path.isdir(SHARES_DIR):
        return
    db = get_db()
    now = time.time()
    rows = db.execute(
        'SELECT token, filepath FROM authorizations WHERE filepath LIKE ? AND expires_at < ?',
        (SHARES_DIR + '%', now),
    ).fetchall()
    for row in rows:
        filepath = row['filepath']
        if os.path.isfile(filepath):
            os.remove(filepath)
        db.execute('DELETE FROM authorizations WHERE token = ?', (row['token'],))
    db.commit()
    db.close()
