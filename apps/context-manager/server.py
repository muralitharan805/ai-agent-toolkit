#!/usr/bin/env python3
"""Local context catalog and reviewed sync UI. Run with --help for options."""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote, urlparse

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'bin'))
from toolkit_manifest import validated_rule_path

STATIC = Path(__file__).parent / 'static'
CONSUMER = ('frameworks', 'infra', 'shared', 'domains')
AGENTS = ('codex', 'antigravity', 'claude')
DEV_PAIR_ORIGINS = ('http://127.0.0.1:4200', 'http://localhost:4200')
PAIR_ORIGINS = ('https://seyalicraft.com', *DEV_PAIR_ORIGINS)


def context_command(args, env=None):
    proc = subprocess.run(['bash', str(ROOT / 'bin/context.sh'), *args],
                          capture_output=True, text=True, timeout=120, cwd=ROOT, env=env)
    output = proc.stdout + proc.stderr
    if proc.returncode:
        raise ValueError(output[-12000:])
    return output


def global_layout(tool, env=None):
    if tool not in AGENTS:
        raise ValueError('Unsupported global agent')
    return json.loads(context_command(['--describe-global', '--tool', tool], env))


def global_snapshot(layout):
    files = {}
    for name in layout['trees'] + layout['files']:
        path = Path(os.path.abspath(os.path.join(ROOT, name)))
        if path.resolve() != path or path.is_symlink():
            raise ValueError(f'Symlink destination is not supported: {path}')
        if not path.exists():
            continue
        is_tree = name in layout['trees']
        if (is_tree and not path.is_dir()) or (not is_tree and not path.is_file()):
            raise ValueError(f'Unexpected global destination type: {path}')
        for item in path.rglob('*') if is_tree else (path,):
            if item.is_symlink():
                raise ValueError(f'Symlink destination is not supported: {item}')
            if item.is_file():
                files[str(item)] = item.read_bytes()
            elif not item.is_dir():
                raise ValueError(f'Unsupported file type: {item}')
    return files


def sync_source_digest(selectors, files):
    sources = {selector: source_digest(selector).encode() for selector in selectors}
    for path, contents in files.items():
        if Path(path).name != '.toolkit-manifest.json':
            continue
        manifest = json.loads(contents)
        for entries in manifest.get('aggregates', {}).values():
            if not isinstance(entries, list):
                raise ValueError('Invalid registered rule source list')
            for entry in entries:
                rule = validated_rule_path(ROOT, entry)
                sources[str(rule)] = rule.read_bytes() if rule.is_file() else b''
    return digest(sources)


def global_paths(layout, staged):
    pairs = []
    for key in ('trees', 'files'):
        pairs.extend(zip(staged[key], layout[key], strict=True))
    return [(Path(local), Path(os.path.abspath(os.path.join(ROOT, real)))) for local, real in pairs]


def translate_path(path, pairs):
    for source, target in pairs:
        if path.is_relative_to(source):
            return target / path.relative_to(source)
    raise ValueError(f'Unexpected path in global preview: {path}')


def catalog():
    result = []
    for category in CONSUMER:
        for file in sorted((ROOT / category).rglob('skills/SKILL.md')):
            if any(part in ('examples', 'node_modules', '.git') for part in file.relative_to(ROOT).parts):
                continue
            text = file.read_text()
            meta = yaml.safe_load(text.split('---', 2)[1]) if text.startswith('---') else {}
            bundle = file.parent.parent
            result.append(dict(id=str(bundle.relative_to(ROOT)), name=meta.get('name', bundle.name),
                               description=meta.get('description', ''), category=category,
                               rules=len(list((bundle / 'rules').glob('*.md'))), content=text))
    return result


def snapshot(project, tool):
    """Read only destinations owned by the workspace CLI; reject symlink traversal."""
    if not project.is_dir() or project.resolve() != project:
        raise ValueError('Project moved or became a symlink. Register its current location.')
    if tool == 'claude':
        root = project / '.claude'
        files = global_snapshot(dict(trees=[str(root / 'skills')],
                                     files=[str(root / '.toolkit-manifest.json')]))
        return {str(Path(path).relative_to(project)): contents for path, contents in files.items()}
    files = {}
    for name in ('.agents', 'AGENTS.md', 'AGENTS.md.bak', 'AGENTS.override.md'):
        base = project / name
        if base.is_symlink():
            raise ValueError(f'Symlink destination is not supported: {name}')
        paths = sorted(base.rglob('*')) if base.is_dir() else [base]
        for path in paths:
            if path.is_symlink():
                raise ValueError(f'Symlink destination is not supported: {path}')
            if path.is_file():
                files[str(path.relative_to(project))] = path.read_bytes()
    return files


def validate_cleanup_targets(files, trees, manifests, selectors):
    """Ensure reviewed cleanup can only touch destinations included in its snapshot."""
    for path, contents in files.items():
        manifest = Path(path)
        if manifest not in manifests:
            continue
        for key, entry in json.loads(contents).get('managed', {}).items():
            source = entry.get('source') or ''
            if selectors and not any(source == selector or source.startswith(selector + '/')
                                     for selector in selectors):
                continue
            relative = Path(entry.get('target') or key)
            target = manifest.parent / relative
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError(f'Unexpected managed cleanup path: {target}')
            if not any(target != tree and target.is_relative_to(tree) for tree in trees):
                raise ValueError(f'Unexpected managed cleanup path: {target}')


def digest(files):
    h = hashlib.sha256()
    for name, value in sorted(files.items()):
        h.update(name.encode() + b'\0' + value + b'\0')
    return h.hexdigest()


def source_digest(selector):
    base = ROOT / selector
    files = {}
    for path in sorted(base.rglob('*')):
        if path.is_symlink():
            raise ValueError('Source symlinks are not supported')
        if path.is_file():
            files[str(path.relative_to(base))] = path.read_bytes()
    return digest(files)


class Manager:
    def __init__(self, state):
        self.state = state
        saved = json.loads(state.read_text()) if state.exists() else []
        directories = {}
        for project in saved:
            directories.setdefault(project['path'], project)
        self.projects = list(directories.values())
        self.previews = {}
        self.lock = threading.Lock()

    def directories(self, data):
        path = Path(data.get('path') or Path.home()).expanduser()
        if not path.is_absolute():
            raise ValueError('Enter an absolute folder path')
        path = path.resolve(strict=True)
        if not path.is_dir():
            raise ValueError('Choose a directory')
        children = [
            {'name': child.name, 'path': str(child)}
            for child in path.iterdir()
            if not child.name.startswith('.') and not child.is_symlink() and child.is_dir()
        ]
        return {
            'path': str(path),
            'parent': str(path.parent) if path.parent != path else None,
            'children': sorted(children, key=lambda child: child['name'].casefold()),
        }

    def register(self, data):
        requested = Path(data['path']).expanduser()
        if not requested.is_absolute():
            raise ValueError('Enter an absolute project path')
        path = requested.resolve(strict=True)
        if not path.is_dir() or path == Path.home() or path == Path('/') or path == ROOT:
            raise ValueError('Choose a project directory, not the toolkit, home, or filesystem root')
        for item in self.projects:
            if item['path'] == str(path):
                return item
        item = dict(id=secrets.token_hex(8), name=data.get('name', '').strip() or path.name,
                    path=str(path))
        self.projects.append(item)
        self.state.parent.mkdir(parents=True, exist_ok=True)
        temp = self.state.with_suffix('.tmp')
        temp.write_text(json.dumps(self.projects, indent=2))
        temp.replace(self.state)
        return item

    def project(self, project_id):
        return next(p for p in self.projects if p['id'] == project_id)

    def installed(self, data):
        tool = data['tool']
        if tool not in AGENTS:
            raise ValueError('Unsupported agent')
        if data.get('scope') == 'global':
            layout = global_layout(tool)
            roots = [Path(os.path.abspath(os.path.join(ROOT, name))).parent
                     for name in layout['files'] if Path(name).name == '.toolkit-manifest.json']
            path = layout['instructions']
            instructions = Path(os.path.abspath(os.path.join(ROOT, path))) if path else None
            aggregate_root = instructions.parent if instructions else None
        else:
            project = Path(self.project(data['project'])['path'])
            if not project.is_dir() or project.resolve() != project:
                raise ValueError('Target directory is unavailable')
            roots = [project / ('.claude' if tool == 'claude' else '.agents')]
            instructions = project / 'AGENTS.md' if tool == 'codex' else None
            aggregate_root = roots[0]

        items = []
        for root in dict.fromkeys(roots):
            manifest = root / '.toolkit-manifest.json'
            if manifest.resolve() != manifest or manifest.is_symlink():
                raise ValueError('Symlink manifest is not supported')
            proc = subprocess.run(
                ['python3', str(ROOT / 'bin/toolkit_manifest.py'), 'inventory',
                 '--root', str(root), '--toolkit-root', str(ROOT), '--tool', tool],
                capture_output=True, text=True, timeout=30, cwd=ROOT,
            )
            if proc.returncode:
                reason = proc.stderr.strip().splitlines()[-1:] or ['Inventory command failed']
                raise ValueError(f'Could not read {manifest}: {reason[0]}')
            inventory = json.loads(proc.stdout)
            items.extend(inventory['items'])
            if instructions and root == aggregate_root:
                aggregate = 'agents_rules' if tool == 'codex' else 'gemini_rules'
                for source in inventory['aggregates'].get(aggregate, []):
                    items.append(dict(source=source, target=str(instructions), kind='instructions',
                                      status='instructions-registered' if instructions.is_file()
                                      else 'missing'))
        return dict(items=items)

    def export_zip(self, data):
        platform = data.get('platform')
        if platform not in ('chatgpt', 'gemini'):
            raise ValueError('Choose ChatGPT or Gemini')
        selector = data.get('selector')
        bundle = next((item for item in catalog() if item['id'] == selector), None)
        if bundle is None:
            raise ValueError('Select a catalog bundle')
        if not isinstance(bundle['name'], str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', bundle['name']):
            raise ValueError('This bundle needs a valid skill name before it can be exported')
        source_digest(selector)
        with tempfile.TemporaryDirectory(prefix='context-export-') as work:
            context_command(['-e', selector, '--tool', platform, '--mode', 'zip', '--out', work])
            archives = list(Path(work).glob('*.zip'))
            if len(archives) != 1:
                raise ValueError('Expected one ZIP archive for the selected bundle')
            archive = archives[0]
            return archive.name, archive.read_bytes()

    def run(self, tool, selector, target, remove=False):
        command = ['-w', selector, '--tool', tool, '--target', str(target)]
        if remove:
            command.append('--clean')
        return context_command(command)

    def preview(self, data):
        operation = data.get('operation', 'sync')
        if operation not in ('sync', 'remove'):
            raise ValueError('Choose sync or remove')
        remove = operation == 'remove'
        if data.get('scope') == 'global':
            return self.preview_global(data, remove)
        if data.get('allInstalled'):
            raise ValueError('All installed context is available only for global removal')
        project = self.project(data['project'])
        tool = data.get('tool', project.get('tool', 'codex'))
        if tool not in AGENTS:
            raise ValueError('Unsupported agent')
        selector = data['selector']
        if selector not in {c['id'] for c in catalog()}:
            raise ValueError('Select a catalog bundle')
        target = Path(project['path'])
        before = snapshot(target, tool)
        if remove:
            root = Path('.claude' if tool == 'claude' else '.agents')
            names = ('skills',) if tool == 'claude' else ('skills', 'rules', 'workflows', 'plugins')
            validate_cleanup_targets(before, [root / name for name in names],
                                     {root / '.toolkit-manifest.json'}, [selector])
        source = sync_source_digest([selector], before)
        with tempfile.TemporaryDirectory(prefix='context-preview-') as work:
            dest = Path(work)
            for name, content in before.items():
                file = dest / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(content)
            output = self.run(tool, selector, dest, remove)
            after = snapshot(dest, tool)
        return self.review(before, after, output.replace(work, str(target)),
                           dict(project=project['id'], tool=tool, selector=selector,
                                source=source, remove=remove))

    def preview_global(self, data, remove):
        tool = data['tool']
        layout = global_layout(tool)
        selector = data.get('selector')
        all_installed = data.get('allInstalled', False)
        if not isinstance(all_installed, bool) or (all_installed and (not remove or selector is not None)):
            raise ValueError('Choose either all installed global context or one bundle to remove')
        if selector is not None and selector not in {c['id'] for c in catalog()}:
            raise ValueError('Select a catalog bundle')
        selectors = [] if all_installed else layout['defaults'] if selector is None else [selector]
        command = ['-g', '--tool', tool]
        if remove:
            if not (selectors or all_installed):
                raise ValueError('No global bundles selected for removal')
            command.extend(['--clean', *selectors])
        elif selector is not None:
            command.append(selector)
        before = global_snapshot(layout)
        if remove:
            trees = [Path(os.path.abspath(os.path.join(ROOT, path))) for path in layout['trees']]
            manifests = {Path(os.path.abspath(os.path.join(ROOT, path))) for path in layout['files']
                         if Path(path).name == '.toolkit-manifest.json'}
            validate_cleanup_targets(before, trees, manifests, selectors)
        source = sync_source_digest(selectors, before)
        with tempfile.TemporaryDirectory(prefix='context-global-preview-') as work:
            env = {**os.environ, 'HOME': work, 'CODEX_HOME': str(Path(work) / 'codex-config'),
                   'CLAUDE_CONFIG_DIR': str(Path(work) / 'claude-config')}
            staged = global_layout(tool, env)
            pairs = global_paths(layout, staged)
            reverse = [(real, local) for local, real in pairs]
            for name, content in before.items():
                file = translate_path(Path(name), reverse)
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(content)
            output = context_command(command, env)
            after = {str(translate_path(Path(name), pairs)): content
                     for name, content in global_snapshot(staged).items()}
            for local, real in pairs:
                output = output.replace(str(local), str(real))
            scope_line = f"Scope : global:{layout['scopeRoot']} ({tool})"
            output = '\n'.join(scope_line if line.startswith('Scope : ') else line
                               for line in output.splitlines())
        return self.review(before, after, output, dict(
            tool=tool, layout=layout, selectors=selectors, command=command, source=source))

    def review(self, before, after, output, plan):
        changes = []
        for name in sorted(before.keys() | after.keys()):
            if name.endswith('.toolkit-manifest.json') or before.get(name) == after.get(name):
                continue
            left = before.get(name, b'').decode('utf-8', errors='replace').splitlines(True)
            right = after.get(name, b'').decode('utf-8', errors='replace').splitlines(True)
            change = 'remove' if name not in after else 'add' if name not in before else 'update'
            changes.append(dict(path=name, change=change, diff=''.join(difflib.unified_diff(
                left, right, fromfile='before/' + name, tofile='after/' + name))))
        token = secrets.token_hex(24)
        self.previews = {token: {**plan, 'target': digest(before)}}
        return dict(token=token, changes=changes, output=output)

    def sync(self, data):
        preview = self.previews.pop(data['token'], None)
        if preview is None:
            raise ValueError('Preview expired. Review a fresh preview before syncing.')
        if 'layout' in preview:
            layout = global_layout(preview['tool'])
            if layout != preview['layout']:
                raise ValueError('Global configuration changed. Refresh the preview.')
            current = global_snapshot(layout)
            if (digest(current) != preview['target']
                    or sync_source_digest(preview['selectors'], current) != preview['source']):
                raise ValueError('Source or destination changed. Refresh the preview.')
            return dict(output=context_command(preview['command']))
        project = self.project(preview['project'])
        target = Path(project['path'])
        current = snapshot(target, preview['tool'])
        if (digest(current) != preview['target']
                or sync_source_digest([preview['selector']], current) != preview['source']):
            raise ValueError('Source or destination changed. Refresh the preview.')
        return dict(output=self.run(preview['tool'], preview['selector'], target, preview['remove']))


class Handler(BaseHTTPRequestHandler):
    def send(self, code, data, content_type='application/json', filename=None):
        payload = json.dumps(data).encode() if content_type == 'application/json' else data
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(payload)))
        if filename is not None:
            self.send_header('Content-Disposition', f"attachment; filename*=UTF-8''{quote(filename, safe='')}")
        origin = self.hosted_origin()
        if origin:
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Access-Control-Expose-Headers', 'Content-Disposition')
            self.send_header('Vary', 'Origin')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(payload)

    def trusted(self):
        host = self.headers.get('Host', '')
        return host in (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}')

    def hosted_origin(self):
        origin = self.headers.get('Origin')
        configured = getattr(self.server, 'pair_origin', None)
        allowed = DEV_PAIR_ORIGINS if configured in DEV_PAIR_ORIGINS else (configured,)
        return origin if origin in allowed else None

    def bootstrap(self, token):
        with self.server.manager.lock:
            data = dict(token=token, projects=list(self.server.manager.projects),
                        catalog=catalog(), globalSync={tool: global_layout(tool) for tool in AGENTS})
        return self.send(200, data)

    def do_OPTIONS(self):
        paths = ('/api/bootstrap', '/api/directories', '/api/projects', '/api/installed',
                 '/api/preview', '/api/sync', '/api/export-zip')
        origin = self.hosted_origin()
        if (not self.trusted() or not origin or self.path not in paths
                or self.headers.get('Access-Control-Request-Method') != 'POST'):
            return self.send(403, dict(error='Untrusted request'))
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', origin)
        self.send_header('Access-Control-Allow-Methods', 'POST')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Context-Token')
        self.send_header('Vary', 'Origin')
        self.end_headers()

    def do_GET(self):
        origin = self.headers.get('Origin')
        if not self.trusted() or (origin and origin not in self.local_origins()):
            return self.send(403, dict(error='Invalid host'))
        path = urlparse(self.path).path
        if path == '/api/bootstrap':
            return self.send(403, dict(error='An access code is required'))
        files = {'/': ('index.html', 'text/html; charset=utf-8'), '/app.js': ('app.js', 'text/javascript'), '/style.css': ('style.css', 'text/css')}
        if path not in files:
            return self.send(404, dict(error='Not found'))
        file, mime = files[path]
        self.send(200, (STATIC / file).read_bytes(), mime)

    def local_origins(self):
        return (f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}')

    def do_POST(self):
        origin = self.headers.get('Origin')
        hosted = bool(self.hosted_origin())
        expected = self.server.pair_token if hosted else self.server.token
        token = self.headers.get('X-Context-Token', '').encode('utf-8')
        if (not self.trusted() or (origin and not hosted and origin not in self.local_origins())
                or not secrets.compare_digest(token, expected.encode('utf-8'))):
            return self.send(403, dict(error='Untrusted request'))
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if size < 1 or size > 65536:
                raise ValueError('Invalid request size')
            data = json.loads(self.rfile.read(size))
            if self.path == '/api/bootstrap':
                return self.bootstrap(expected)
            if self.path == '/api/export-zip':
                filename, archive = self.server.manager.export_zip(data)
                return self.send(200, archive, 'application/zip', filename)
            action = {
                '/api/directories': 'directories',
                '/api/projects': 'register',
                '/api/installed': 'installed',
                '/api/preview': 'preview',
                '/api/sync': 'sync',
            }.get(self.path)
            if not action:
                return self.send(404, dict(error='Not found'))
            with self.server.manager.lock:
                result = getattr(self.server.manager, action)(data)
            self.send(200, result)
        except (ValueError, KeyError, StopIteration, OSError, subprocess.TimeoutExpired) as error:
            self.send(400, dict(error=str(error) or 'Invalid selection'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--state', type=Path, default=Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))) / 'ai-agent-toolkit/projects.json')
    parser.add_argument('--pair-with', choices=PAIR_ORIGINS,
                        help='Allow the selected SeyaliCraft origin to pair with this local companion')
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.token = secrets.token_urlsafe(32)
    server.pair_origin = args.pair_with
    server.pair_token = secrets.token_urlsafe(32) if args.pair_with else None
    server.manager = Manager(args.state)
    print(f'Context Manager: http://127.0.0.1:{server.server_port}', flush=True)
    print(f'Local access code: {server.token}', flush=True)
    if args.pair_with:
        print(f'Pairing code for {args.pair_with}: {server.pair_token}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
