"""Real CLI integration checks for the local review-and-sync flow."""
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
import zipfile
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('context_manager', ROOT / 'apps/context-manager/server.py')
app = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(app)


class ContextManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / 'project'
        self.project.mkdir()
        self.manager = app.Manager(Path(self.temp.name) / 'state.json')
        self.registered = self.manager.register(dict(path=str(self.project)))
        self.request = dict(project=self.registered['id'], tool='codex',
                            selector='shared/pnpm-package-management')

    def test_preview_is_read_only_and_sync_installs_real_bundle(self):
        preview = self.manager.preview(self.request)
        self.assertEqual(list(self.project.iterdir()), [])
        paths = [change['path'] for change in preview['changes']]
        self.assertTrue(any(path.endswith('SKILL.md') for path in paths))
        self.assertIn('AGENTS.md', paths)
        self.manager.sync(dict(token=preview['token']))
        installed = self.project / '.agents/skills/pnpm-package-management/SKILL.md'
        self.assertTrue(installed.exists())
        self.assertTrue((self.project / 'AGENTS.md').exists())
        items = self.manager.installed(self.request)['items']
        self.assertTrue(any(item['kind'] == 'skill' and item['status'] == 'up-to-date' for item in items))
        self.assertTrue(any(item['status'] == 'instructions-registered' for item in items))
        self.assertEqual(self.manager.installed(dict(self.request, tool='antigravity'))['items'], [])
        second = self.manager.preview(self.request)
        self.assertEqual(second['changes'], [])
        installed.write_text(installed.read_text() + '\nLOCAL CUSTOMIZATION\n')
        items = self.manager.installed(self.request)['items']
        self.assertTrue(any(item['status'] == 'locally-modified' for item in items))
        protected = self.manager.preview(self.request)
        self.assertIn('Local modifications', protected['output'])
        self.manager.sync(dict(token=protected['token']))
        self.assertIn('LOCAL CUSTOMIZATION', installed.read_text())

    def test_inventory_clears_update_after_apply_for_same_agent_and_target(self):
        request = dict(self.request, tool='antigravity')
        self.manager.sync({'token': self.manager.preview(request)['token']})
        manifest_root = self.project / '.agents'
        installed = manifest_root / 'skills/pnpm-package-management'
        (installed / 'SKILL.md').write_text('Previous installed revision\n')
        subprocess.run([
            'python3', str(ROOT / 'bin/toolkit_manifest.py'), 'record',
            '--root', str(manifest_root), '--key', 'skills/pnpm-package-management',
            '--target', str(installed), '--source', str(ROOT / self.request['selector'] / 'skills'),
            '--toolkit-root', str(ROOT), '--kind', 'skill', '--scope', 'workspace',
            '--tool', 'antigravity',
        ], check=True, capture_output=True)

        def skill_status():
            return next(item['status'] for item in self.manager.installed(request)['items']
                        if item['kind'] == 'skill')

        self.assertEqual(skill_status(), 'update-available')
        preview = self.manager.preview(request)
        self.assertEqual(skill_status(), 'update-available')
        self.manager.sync({'token': preview['token']})
        self.assertEqual(skill_status(), 'up-to-date')

    def test_target_changes_require_another_preview(self):
        preview = self.manager.preview(self.request)
        (self.project / 'AGENTS.md').write_text('New user instructions')
        with self.assertRaisesRegex(ValueError, 'changed'):
            self.manager.sync(dict(token=preview['token']))
        self.assertEqual((self.project / 'AGENTS.md').read_text(), 'New user instructions')

    def test_invalid_selector_and_symlink_rejected(self):
        with self.assertRaisesRegex(ValueError, 'catalog'):
            self.manager.preview(dict(self.request, selector='../../tmp'))
        (self.project / '.agents').symlink_to(Path(self.temp.name), target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            self.manager.preview(self.request)

    def test_antigravity_rules_are_included(self):
        preview = self.manager.preview(dict(self.request, tool='antigravity'))
        self.assertTrue(any('/rules/' in c['path'] for c in preview['changes']))
        self.assertNotIn('AGENTS.md', [c['path'] for c in preview['changes']])

    def test_claude_workspace_skill_lifecycle_on_existing_target(self):
        (self.project / '.claude').mkdir()
        settings = self.project / '.claude/settings.json'
        settings.write_text('{}\n')
        instructions = self.project / 'CLAUDE.md'
        instructions.write_text('Existing project instructions\n')
        request = dict(self.request, tool='claude')
        preview = self.manager.preview(request)
        installed = self.project / '.claude/skills/pnpm-package-management/SKILL.md'
        self.assertFalse(installed.exists())
        self.assertTrue(preview['changes'])
        self.assertTrue(all(change['path'].startswith('.claude/skills/') for change in preview['changes']))
        self.manager.sync({'token': preview['token']})
        self.assertTrue(installed.is_file())
        self.assertEqual([item['status'] for item in self.manager.installed(request)['items']],
                         ['up-to-date'])
        self.assertEqual(self.manager.installed(self.request)['items'], [])
        removal = self.manager.preview({**request, 'operation': 'remove'})
        self.assertTrue(any(change['change'] == 'remove' for change in removal['changes']))
        self.manager.sync({'token': removal['token']})
        self.assertFalse(installed.exists())
        self.assertEqual(settings.read_text(), '{}\n')
        self.assertEqual(instructions.read_text(), 'Existing project instructions\n')

    def test_claude_global_preview_uses_isolated_custom_config(self):
        home = Path(self.temp.name) / 'home'
        config = Path(self.temp.name) / 'custom-claude'
        home.mkdir()
        config.mkdir()
        settings = config / 'settings.json'
        settings.write_text('{}\n')
        unmanaged = config / 'skills/my-skill/SKILL.md'
        unmanaged.parent.mkdir(parents=True)
        unmanaged.write_text('User-owned skill\n')
        with patch.dict('os.environ', {'HOME': str(home), 'CLAUDE_CONFIG_DIR': str(config)}):
            layout = app.global_layout('claude')
            self.assertEqual(layout['destinations'], [str(config / 'skills')])
            request = dict(scope='global', tool='claude')
            preview = self.manager.preview(request)
            installed = config / 'skills/thanglish-mentor-persona/SKILL.md'
            self.assertTrue(any(item['path'] == str(installed) for item in preview['changes']))
            self.assertFalse(installed.exists())
            self.manager.sync({'token': preview['token']})
            self.assertTrue(installed.is_file())
            items = self.manager.installed(request)['items']
            self.assertEqual(len(items), len(layout['defaults']))
            self.assertTrue(all(item['status'] == 'up-to-date' for item in items))
            removal = self.manager.preview({**request, 'operation': 'remove', 'allInstalled': True})
            self.manager.sync({'token': removal['token']})
            self.assertFalse(installed.exists())
            self.assertEqual(unmanaged.read_text(), 'User-owned skill\n')
            self.assertEqual(settings.read_text(), '{}\n')
            self.assertFalse((home / '.claude').exists())

    def test_registry_persists(self):
        reopened = app.Manager(self.manager.state)
        self.assertEqual(reopened.projects, self.manager.projects)

    def test_legacy_directory_duplicates_are_combined(self):
        state = self.manager.state
        state.write_text(json.dumps([
            {**self.registered, 'tool': 'codex'},
            {**self.registered, 'id': 'old-antigravity', 'tool': 'antigravity'},
        ]))
        reopened = app.Manager(state)
        self.assertEqual(len(reopened.projects), 1)
        self.assertEqual(reopened.register({'path': str(self.project)})['id'], self.registered['id'])

    def test_browse_existing_folder_then_load_bundle(self):
        selected = Path(self.temp.name) / 'Another project'
        selected.mkdir()
        (Path(self.temp.name) / 'file.txt').touch()
        folders = self.manager.directories({'path': self.temp.name})
        self.assertEqual([child['name'] for child in folders['children']], ['Another project', 'project'])
        folder = self.manager.directories({'path': folders['children'][0]['path']})
        self.assertEqual(folder['parent'], str(selected.parent))
        self.assertEqual(folder['children'], [])
        project = self.manager.register({'path': folder['path']})
        preview = self.manager.preview(dict(self.request, project=project['id'], tool='antigravity'))
        self.manager.sync({'token': preview['token']})
        self.assertTrue((selected / '.agents/skills/pnpm-package-management/SKILL.md').is_file())
        self.assertEqual(list(self.project.iterdir()), [])

    def test_global_default_preview_and_apply(self):
        root = Path(self.temp.name)
        for tool in ('codex', 'antigravity'):
            with self.subTest(tool=tool):
                home = root / tool
                config = root / 'custom-codex'
                instructions = (config / 'AGENTS.md' if tool == 'codex'
                                else home / '.gemini/GEMINI.md')
                instructions.parent.mkdir(parents=True)
                instructions.write_text('User instructions\n')
                home.mkdir(exist_ok=True)
                with patch.dict('os.environ', {'HOME': str(home), 'CODEX_HOME': str(config)}):
                    layout = app.global_layout(tool)
                    for tree in layout['trees']:
                        self.assertFalse(Path(tree).exists())
                    preview = self.manager.preview({'scope': 'global', 'tool': tool})
                    paths = {item['path'] for item in preview['changes']}
                    self.assertIn(str(instructions), paths)
                    self.assertEqual(instructions.read_text(), 'User instructions\n')
                    for tree in layout['trees']:
                        self.assertFalse(Path(tree).exists())
                    self.manager.sync({'token': preview['token']})
                    self.assertIn('User instructions\n', instructions.read_text())
                    self.assertIn('<!-- AGENT_TOOLKIT_START -->', instructions.read_text())
                    items = self.manager.installed({'scope': 'global', 'tool': tool})['items']
                    self.assertTrue(any(item['kind'] == 'skill' and item['status'] == 'up-to-date' for item in items))
                    self.assertTrue(any(item['target'] == str(instructions)
                                        and item['status'] == 'instructions-registered' for item in items))
                    skill_roots = [Path(path) for path in layout['trees'] if Path(path).name == 'skills']
                    for skill_root in skill_roots:
                        for selector in layout['defaults']:
                            self.assertTrue((skill_root / Path(selector).name / 'SKILL.md').is_file())

    def test_global_selected_bundle_requires_fresh_preview_after_change(self):
        root = Path(self.temp.name)
        config = root / 'custom-codex'
        with patch.dict('os.environ', {'HOME': str(root), 'CODEX_HOME': str(config)}):
            preview = self.manager.preview({'scope': 'global', 'tool': 'codex',
                                            'selector': self.request['selector']})
            skills = [item['path'] for item in preview['changes'] if item['path'].endswith('/SKILL.md')]
            self.assertEqual(skills, [str(root / '.agents/skills/pnpm-package-management/SKILL.md')])
            config.mkdir()
            (config / 'AGENTS.md').write_text('User updated instructions')
            with self.assertRaisesRegex(ValueError, 'changed'):
                self.manager.sync({'token': preview['token']})
            self.assertFalse((root / '.agents').exists())

    def test_workspace_removal_releases_shared_claim_and_preserves_local_edits(self):
        request = {**self.request, 'tool': 'antigravity'}
        (self.project / 'AGENTS.md').write_text('User instructions\n')
        for params in (self.request, request):
            self.manager.sync({'token': self.manager.preview(params)['token']})
        installed = self.project / '.agents/skills/pnpm-package-management/SKILL.md'
        codex = self.manager.preview({**self.request, 'operation': 'remove'})
        self.assertIn('retained for other tool owners', codex['output'])
        self.assertTrue(installed.is_file())
        self.assertIn('AGENT_TOOLKIT_START', (self.project / 'AGENTS.md').read_text())
        self.manager.sync({'token': codex['token']})
        self.assertTrue(installed.is_file())
        self.assertEqual((self.project / 'AGENTS.md').read_text(), 'User instructions\n')
        installed.write_text('Local customization\n')
        removal = self.manager.preview({**request, 'operation': 'remove'})
        self.assertTrue(any(change['change'] == 'remove' and '/rules/' in change['path']
                            for change in removal['changes']))
        self.assertIn('preserved locally modified', removal['output'])
        self.manager.sync({'token': removal['token']})
        self.assertEqual(installed.read_text(), 'Local customization\n')
        self.assertEqual(list((self.project / '.agents/rules').glob('*.md')), [])

    def test_global_removal_preserves_other_bundles_and_user_instructions(self):
        root = Path(self.temp.name)
        for tool in ('codex', 'antigravity'):
            with self.subTest(tool=tool):
                home = root / tool
                config = home / 'custom-config'
                with patch.dict('os.environ', {'HOME': str(home), 'CODEX_HOME': str(config)}):
                    layout = app.global_layout(tool)
                    instructions = Path(next(path for path in layout['destinations'] if path.endswith('.md')))
                    instructions.parent.mkdir(parents=True)
                    instructions.write_text('User instructions\n')
                    request = dict(scope='global', tool=tool)
                    extra = {**request, 'selector': self.request['selector']}
                    for params in (request, extra):
                        self.manager.sync({'token': self.manager.preview(params)['token']})
                    for params in (request, extra):
                        before = app.global_snapshot(layout)
                        preview = self.manager.preview({**params, 'operation': 'remove'})
                        self.assertEqual(app.global_snapshot(layout), before)
                        self.assertTrue(any(c['change'] == 'remove' for c in preview['changes']))
                        self.manager.sync({'token': preview['token']})
                        if params is request:
                            remaining = app.global_snapshot(layout)
                            self.assertTrue(any('pnpm-package-management/SKILL.md' in path for path in remaining))
                            self.assertFalse(any('thanglish-mentor-persona/SKILL.md' in path for path in remaining))
                    self.assertEqual(instructions.read_text(), 'User instructions\n')

    def test_remove_all_global_context_is_agent_scoped_and_preserves_local_files(self):
        home = Path(self.temp.name) / 'home'
        home.mkdir()
        with patch.dict('os.environ', {'HOME': str(home), 'CODEX_HOME': str(home / '.codex')}):
            codex = dict(scope='global', tool='codex')
            extra = {**codex, 'selector': self.request['selector']}
            antigravity = {**extra, 'tool': 'antigravity'}
            instructions = home / '.codex/AGENTS.md'
            instructions.parent.mkdir()
            instructions.write_text('User instructions\n')
            for request in (codex, extra, antigravity):
                self.manager.sync({'token': self.manager.preview(request)['token']})
            skills = home / '.agents/skills'
            edited = skills / 'thanglish-mentor-persona/SKILL.md'
            edited.write_text('Local customization\n')
            unmanaged = skills / 'own-skill/SKILL.md'
            unmanaged.parent.mkdir()
            unmanaged.write_text('User-owned skill\n')
            other_layout = app.global_layout('antigravity')
            other_before = app.global_snapshot(other_layout)
            layout = app.global_layout('codex')
            before = app.global_snapshot(layout)

            with self.assertRaises(ValueError):
                self.manager.preview({**codex, 'allInstalled': True})
            preview = self.manager.preview({**codex, 'operation': 'remove', 'allInstalled': True})
            removed = {item['path'] for item in preview['changes'] if item['change'] == 'remove'}
            self.assertIn(str(skills / 'pnpm-package-management/SKILL.md'), removed)
            self.assertIn(str(skills / 'agent-action-guard/SKILL.md'), removed)
            self.assertIn('preserved locally modified', preview['output'])
            self.assertEqual(app.global_snapshot(layout), before)
            self.manager.sync({'token': preview['token']})
            self.assertFalse(any(Path(path).exists() for path in removed))
            self.assertEqual(edited.read_text(), 'Local customization\n')
            self.assertEqual(unmanaged.read_text(), 'User-owned skill\n')
            self.assertEqual(instructions.read_text(), 'User instructions\n')
            self.assertEqual(app.global_snapshot(other_layout), other_before)

    def test_hosted_gui_pairs_and_runs_a_reviewed_workspace_sync(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        server.manager = self.manager
        server.token = 'local-test-token'
        server.pair_origin = 'https://seyalicraft.com'
        server.pair_token = 'hosted-test-token'
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f'http://127.0.0.1:{server.server_port}/api/'
            command = subprocess.run([
                'python3', str(ROOT / 'apps/context-manager/server.py'), '--help',
            ], check=True, capture_output=True, text=True)
            localhost = 'http://localhost:4200'
            loopback_ip = 'http://127.0.0.1:4200'
            for origin in ('https://seyalicraft.com', loopback_ip, localhost):
                self.assertIn(origin, command.stdout)

            def preflight(origin):
                return Request(base + 'bootstrap', method='OPTIONS', headers={
                    'Origin': origin, 'Access-Control-Request-Method': 'POST',
                })

            with urlopen(preflight('https://seyalicraft.com')) as response:
                self.assertEqual(response.headers['Access-Control-Allow-Origin'], 'https://seyalicraft.com')
            with self.assertRaises(HTTPError) as error:
                urlopen(preflight(localhost))
            self.assertEqual(error.exception.code, 403)
            error.exception.close()

            server.pair_origin = loopback_ip
            for origin in (loopback_ip, localhost):
                with urlopen(preflight(origin)) as response:
                    self.assertEqual(response.status, 204)
                    self.assertEqual(response.headers['Access-Control-Allow-Origin'], origin)

            headers = {'Origin': localhost, 'X-Context-Token': server.pair_token,
                       'Content-Type': 'application/json'}

            for denied in ({**headers, 'Origin': 'https://example.org'},
                           {**headers, 'Origin': 'http://localhost:4300'},
                           {**headers, 'X-Context-Token': server.token},
                           {'X-Context-Token': server.pair_token}):
                with self.assertRaises(HTTPError) as error:
                    urlopen(Request(base + 'bootstrap', data=b'{}', headers=denied))
                self.assertEqual(error.exception.code, 403)
                error.exception.close()
            with self.assertRaises(HTTPError) as error:
                urlopen(Request(base + 'bootstrap', headers={'Origin': localhost}))
            self.assertEqual(error.exception.code, 403)
            error.exception.close()

            def post(route, body):
                request = Request(base + route, data=json.dumps(body).encode(), headers=headers)
                with urlopen(request) as response:
                    self.assertEqual(response.headers['Access-Control-Allow-Origin'], localhost)
                    return json.load(response)

            self.assertEqual(post('bootstrap', {})['token'], server.pair_token)
            preview = post('preview', self.request)
            self.assertFalse((self.project / '.agents').exists())
            post('sync', {'token': preview['token']})
            installed = post('installed', self.request)['items']
            self.assertTrue(any(item['status'] == 'up-to-date' for item in installed))
            export = Request(base + 'export-zip',
                             data=json.dumps(dict(self.request, platform='gemini')).encode(),
                             headers=headers)
            with urlopen(export) as response:
                self.assertEqual(response.headers['Access-Control-Expose-Headers'], 'Content-Disposition')
                self.assertEqual(response.headers.get_content_type(), 'application/zip')
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_http_request_protection_and_zip_downloads(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        server.manager = self.manager
        server.token = 'test-token'
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f'http://127.0.0.1:{server.server_port}'
            for data in (None, b'{}'):
                with self.assertRaises(HTTPError) as error:
                    urlopen(Request(base + '/api/bootstrap', data=data))
                self.assertEqual(error.exception.code, 403)
                self.assertNotIn('token', json.load(error.exception))
                error.exception.close()
            bootstrap = Request(base + '/api/bootstrap', data=b'{}',
                                headers={'X-Context-Token': 'test-token'})
            with urlopen(bootstrap) as response:
                self.assertTrue(json.load(response)['catalog'])
            request = Request(base + '/api/installed', data=json.dumps(self.request).encode(),
                              headers={'X-Context-Token': 'test-token'})
            with urlopen(request) as response:
                self.assertEqual(json.load(response)['items'], [])
            for headers in ({}, {'X-Context-Token': 'test-token', 'Origin': 'https://evil.example'}):
                request = Request(base + '/api/projects', data=b'{}', headers=headers)
                with self.assertRaises(HTTPError) as error:
                    urlopen(request)
                self.assertEqual(error.exception.code, 403)
                error.exception.close()
            for platform, skill_path in (
                ('chatgpt', 'pnpm-package-management/SKILL.md'),
                ('gemini', 'SKILL.md'),
            ):
                payload = dict(selector=self.request['selector'], platform=platform)
                request = Request(base + '/api/export-zip', data=json.dumps(payload).encode(),
                                  headers={'X-Context-Token': 'test-token'})
                with urlopen(request) as response:
                    self.assertEqual(response.headers.get_content_type(), 'application/zip')
                    self.assertIn(f'{platform}-pnpm-package-management.zip',
                                  response.headers['Content-Disposition'])
                    with zipfile.ZipFile(io.BytesIO(response.read())) as archive:
                        self.assertIn(skill_path, archive.namelist())
            invalid = Request(base + '/api/export-zip',
                              data=b'{"selector":"shared/*","platform":"chatgpt"}',
                              headers={'X-Context-Token': 'test-token'})
            with self.assertRaises(HTTPError) as error:
                urlopen(invalid)
            self.assertEqual(error.exception.code, 400)
            error.exception.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
