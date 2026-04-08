# vibefs — Architecture

A file and directory preview service with time-limited URLs, designed for AI agents to share local files with users.

## Architecture

- **Package structure**: `vibefs/` with separate modules for CLI, server, DB, rendering, config, and utilities
- **CLI**: Click-based, subcommands for sharing, managing, and serving
- **Web**: Bottle + Waitress (production WSGI server)
- **Templating**: Jinja2 templates in `vibefs/templates/`
- **Storage**: SQLite via `~/.vibefs/vibefs.db`
- **Syntax highlighting**: Pygments with dual dark/light theme support

## Commands

```
vibefs allow <path> [--ttl N] [--live] [--json]       Share a file or directory
vibefs share [--type T] [--content C] [--title T]     Share content from stdin
vibefs allow-git <repo> <hash> [--ttl N] [--json]     Share a git commit
vibefs revoke <token>                                  Revoke a share
vibefs list [--json]                                   List all shares
vibefs serve [--port N] [--host H] [--tunnel]          Start server
vibefs stop                                            Stop daemon
vibefs status [--json]                                 Check daemon status
vibefs owner-url                                       Print dashboard URL
vibefs config set <key> <value>                        Set config
vibefs config get <key>                                Get config
```

## URL Format

```
http://host:port/f/{token}          # file share (8 hex char token)
http://host:port/d/{token}          # directory share (12 hex char token)
http://host:port/d/{token}/path     # deep link to file within directory
http://host:port/git/{token}        # git commit share
http://host:port/dashboard          # owner dashboard (32 hex char key)
```

## Rendering

- **Code**: Pygments syntax highlighting (50+ extensions), configurable style and line numbers
- **Markdown**: markdown-it with GFM, task lists, fenced code highlighting, table wrapping, theme/font controls
- **CSV/TSV**: Parsed and rendered as styled HTML tables
- **PDF**: Browser's native viewer
- **SVG**: Inline rendering
- **Audio/Video**: HTML5 players (base64 data URI for <50MB, raw download for larger)
- **Images**: Inline with correct MIME type
- **Git commits**: Metadata + expandable file diffs with syntax highlighting
- **Directories**: Sidebar file tree + preview pane (Jinja2 template with JS)

## Security Model

- Nothing accessible by default — explicit `allow` with TTL required
- Token entropy: 8 hex (files), 12 hex (dirs), 32 hex (owner)
- Rate limiting: 60 req/min per IP (CF-Connecting-IP aware)
- Path traversal: `realpath()` + prefix check, symlink validation
- Anti-crawler: robots.txt, X-Robots-Tag, noindex, no-referrer
- XSS: Escaped JSON/JS in templates
- Owner auth: constant-time comparison, httponly samesite=Lax cookie
- Large file DoS: >5MB served as download, max 10K files per dir share
- Directory tree cached 30s to prevent scan DoS

## Project Structure

```
vibefs/
├── cli.py            # CLI commands (click)
├── server.py         # Bottle routes, rate limiting, security headers
├── db.py             # SQLite: authorizations, git_authorizations, dir_authorizations
├── renderers.py      # Renderer classes: Code, Markdown, CSV, PDF, Media, SVG, Base
├── templates.py      # Jinja2 env setup, render_template(), dual Pygments CSS
├── templates/        # Jinja2 HTML templates
│   ├── base.html
│   ├── code.html
│   ├── csv.html
│   ├── dashboard.html
│   ├── dir_browser.html
│   ├── expired.html
│   ├── git.html
│   ├── markdown.html
│   ├── media.html
│   ├── owner_login.html
│   └── verify.html
├── config.py         # Config loading, owner key generation
├── constants.py      # Token lengths, TTLs, limits, paths
├── daemon.py         # PID management, daemon start/stop, cleanup timer
├── tunnel.py         # Cloudflare Quick Tunnel integration
├── utils.py          # walk_directory(), is_safe_subpath(), html escaping
└── __init__.py
```

## Dependencies

- `bottle` — Web framework
- `waitress` — Production WSGI server
- `click` — CLI framework
- `jinja2` — Template engine
- `pygments` — Syntax highlighting
- `markdown-it-py[linkify]` + `mdit-py-plugins` — Markdown rendering
- Python stdlib: sqlite3, os, hashlib, hmac, time, mimetypes, csv, etc.

## Design Principles

- **Secure by default**: Nothing is accessible until explicitly allowed
- **Ephemeral**: Authorizations expire automatically
- **Agent-friendly**: CLI output is clean and parseable, `--json` on all commands
- **Zero-config**: Auto-starts daemon, auto-generates owner key, sensible defaults
- **Rich rendering**: Code, markdown, CSV, PDF, media — not just raw file serving
