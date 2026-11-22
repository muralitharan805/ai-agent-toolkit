let state = {catalog: [], projects: []}, selected, previewToken;
let folder;
let revision = 0;
let inventoryRevision = 0;
let installedItems = [];
let apiOrigin = '';
const hosted = document.querySelector('meta[name="context-manager-mode"]')?.content === 'hosted';
const $ = id => document.getElementById(id);
const el = (tag, text, cls) => { const node = document.createElement(tag); node.textContent = text; if (cls) node.className = cls; return node; };
function notice(text, error = false) { $('notice').textContent = text; $('notice').className = error ? 'error' : ''; $('notice').hidden = false; }
function request(path, data, token = state.token) {
  const options = data ? {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-Context-Token': token},
    body: JSON.stringify(data),
  } : {};
  if (hosted) options.targetAddressSpace = 'loopback';
  return fetch(apiOrigin + '/api/' + path, options);
}
async function api(path, data, token) {
  const response = await request(path, data, token);
  const result = await response.json(); if (!response.ok) throw new Error(result.error); return result;
}

async function downloadZip(button) {
  const bundle = selected;
  const status = $('zip-status');
  const platform = button.dataset.zip;
  if (!bundle) return;
  button.disabled = true;
  status.textContent = 'Preparing ZIP…';
  status.classList.remove('error');
  status.hidden = false;
  try {
    const response = await request('export-zip', {selector: bundle.id, platform});
    if (!response.ok) throw new Error((await response.json()).error);
    const disposition = response.headers.get('Content-Disposition') ?? '';
    const filename = disposition.split("filename*=UTF-8''")[1];
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement('a');
    link.href = url;
    link.download = filename ? decodeURIComponent(filename) : `${platform}-${bundle.name}.zip`;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
    if (selected === bundle) {
      status.textContent = 'ZIP download started.';
      status.classList.remove('error');
    }
  } catch (error) {
    if (selected === bundle) {
      status.textContent = error.message;
      status.classList.add('error');
    }
  } finally {
    button.disabled = false;
  }
}

for (const button of document.querySelectorAll('[data-zip]')) {
  button.onclick = () => downloadZip(button);
}
async function busy(button, action) {
  const label = button.textContent;
  button.disabled = true;
  button.textContent = 'Working…';
  try {
    await action();
  } catch (error) {
    $('sync-error').textContent = error.message;
    $('sync-error').hidden = false;
    if (button === $('sync')) button.hidden = true;
  } finally {
    button.disabled = false;
    button.textContent = label;
    syncOptions();
  }
}
function projects() {
  $('project-list').replaceChildren(); $('target').replaceChildren();
  for (const project of state.projects) {
    const row = el('div', '', 'project');
    row.append(el('strong', project.name));
    row.title = project.path;
    $('project-list').append(row);
    const option = el('option', project.path);
    option.value = project.id;
    $('target').append(option);
  }
  syncOptions();
  if (!state.projects.length) { const option = el('option', 'Choose a target directory first'); $('target').append(option); }
  selectWorkspaceAgent();
}
function render() {
  const query = $('search').value.toLowerCase(), category = $('category').value;
  const items = state.catalog.filter(c => (!category || c.category === category) && `${c.name} ${c.description} ${c.id}`.toLowerCase().includes(query));
  $('count').textContent = state.catalog.length; $('results').textContent = `${items.length} bundles`; $('catalog').replaceChildren(); $('empty').hidden = !!items.length;
  for (const c of items) {
    const card = el('button', '', 'card'); card.append(el('span', c.category.toUpperCase(), 'eyebrow'), el('h3', c.name.replaceAll('-', ' ')), el('p', c.description), el('div', `${c.rules ? `${c.rules} rule${c.rules > 1 ? 's' : ''} · ` : ''}Skill bundle`, 'card-footer')); card.onclick = () => open(c); $('catalog').append(card);
  }
}
function invalidate() {
  revision++;
  previewToken = null;
  $('preview-result').hidden = true;
  $('sync-error').hidden = true;
}
function syncOptions() {
  const global = $('scope').value === 'global';
  const remove = $('sync-operation').value === 'remove';
  $('workspace-options').hidden = global;
  $('global-options').hidden = !global;
  if ($('preview').textContent !== 'Working…') {
    $('preview').disabled = global ? !state.globalSync : !state.projects.length;
    $('preview').textContent = remove ? 'Preview removal' : 'Preview changes';
  }
  if (!global || !state.globalSync) return;
  const bundle = $('global-bundle');
  $('all-global-context').disabled = !remove;
  $('all-global-context').hidden = !remove;
  if (!remove && bundle.value === 'all') bundle.value = selected ? 'selected' : 'default';
  const layout = state.globalSync[$('global-agent').value];
  $('global-scope-hint').textContent = layout.instructions
    ? 'Global changes affect skills and bundled instructions for your user account.'
    : 'Claude Code global changes affect personal skills.';
  const allInstalled = bundle.value === 'all';
  $('all-global-hint').hidden = !allInstalled;
  $('global-modules').hidden = allInstalled;
  const ids = allInstalled ? [] : bundle.value === 'default' ? layout.defaults : [selected.id];
  const names = ids.map(id => state.catalog.find(item => item.id === id)?.name ?? id);
  $('global-modules').replaceChildren(...names.map(name => el('li', name.replaceAll('-', ' '))));
  $('global-paths').replaceChildren(...layout.destinations.map(path => el('li', path)));
}
function open(c) {
  selected = c;
  $('back-to-installed').hidden = true;
  $('detail-title').textContent = c?.name ?? 'Global sync';
  $('detail-description').textContent = c?.description ?? 'Manage toolkit context installed globally for an agent.';
  $('detail-path').textContent = c?.id ?? '';
  $('zip-downloads').hidden = !c;
  $('zip-status').hidden = true;
  $('content').textContent = c?.content ?? '';
  $('detail-tabs').hidden = !c;
  $('scope-field').hidden = !c;
  $('scope').value = c ? 'workspace' : 'global';
  $('sync-operation').value = 'sync';
  $('global-bundle').options[1].disabled = !c;
  $('global-bundle').value = c ? 'selected' : 'default';
  invalidate();
  syncOptions();
  tab(!c);
  $('detail').showModal();
}
$('open-global').onclick = () => open(null);
for (const id of ['scope', 'workspace-agent', 'global-agent', 'global-bundle', 'sync-operation']) {
  $(id).onchange = () => { invalidate(); syncOptions(); };
}
function tab(sync) { $('content').hidden = sync; $('sync-panel').hidden = !sync; $('tab-content').classList.toggle('active', !sync); $('tab-sync').classList.toggle('active', sync); }
$('tab-content').onclick = () => tab(false); $('tab-sync').onclick = () => tab(true);
$('search').oninput = render; $('category').onchange = render;
function selectWorkspaceAgent() {
  const directory = state.projects.find(project => project.id === $('target').value);
  $('workspace-agent').value = ['codex', 'antigravity', 'claude'].includes(directory?.tool) ? directory.tool : 'codex';
}
$('target').onchange = () => { selectWorkspaceAgent(); invalidate(); };

const installedLabels = {
  'up-to-date': 'Up to date',
  'update-available': 'Update available',
  'locally-modified': 'Locally modified',
  'missing': 'Missing from destination',
  'source-unavailable': 'Source unavailable',
  'instructions-registered': 'Instructions registered',
};
const installedPreferencesKey = 'context-manager:installed-selection';

function saveInstalledSelection() {
  try {
    sessionStorage.setItem(installedPreferencesKey, JSON.stringify({
      scope: $('installed-scope').value,
      project: $('installed-target').value,
      tool: $('installed-agent').value,
      onlyUpdates: $('installed-updates').checked,
    }));
  } catch {
    // The view can still work when browser storage is unavailable.
  }
}

function restoreInstalledSelection() {
  try {
    return JSON.parse(sessionStorage.getItem(installedPreferencesKey)) ?? {};
  } catch {
    return {};
  }
}

function renderInstalled() {
  const onlyUpdates = $('installed-updates').checked;
  const groups = new Map();
  const catalogByPath = [...state.catalog].sort((a, b) => b.id.length - a.id.length);
  for (const item of installedItems) {
    const bundle = catalogByPath.find(context => item.source &&
      (item.source === context.id || item.source.startsWith(context.id + '/')));
    const key = bundle?.id ?? item.source ?? item.target;
    if (!groups.has(key)) groups.set(key, {bundle, items: []});
    groups.get(key).items.push(item);
  }

  const list = $('installed-list');
  list.replaceChildren();
  for (const [key, group] of groups) {
    const hasUpdate = group.items.some(item => item.status === 'update-available');
    if (onlyUpdates && !hasUpdate) continue;
    const row = el('article', '', 'installed-bundle');
    row.append(el('h3', group.bundle?.name.replaceAll('-', ' ') ?? key));
    const files = el('ul', '');
    for (const item of group.items) {
      files.append(el('li', `${installedLabels[item.status]} · ${item.target}`));
    }
    row.append(files);
    if (group.bundle) {
      const button = el('button', hasUpdate ? 'Review update or removal' : 'Review context');
      button.onclick = () => {
        const scope = $('installed-scope').value;
        const tool = $('installed-agent').value;
        open(group.bundle);
        $('back-to-installed').hidden = false;
        $('scope').value = scope;
        if (scope === 'global') {
          $('global-agent').value = tool;
        } else {
          $('target').value = $('installed-target').value;
          $('workspace-agent').value = tool;
        }
        syncOptions();
        tab(true);
      };
      row.append(button);
    }
    list.append(row);
  }
  $('installed-status').textContent = list.children.length
    ? `${list.children.length} tracked contexts`
    : onlyUpdates ? 'No tracked files have updates available.' : 'No toolkit context tracked for this agent and scope.';
}

async function refreshInstalled() {
  saveInstalledSelection();
  const requestRevision = ++inventoryRevision;
  const scope = $('installed-scope').value;
  const project = $('installed-target').value;
  $('installed-target-field').hidden = scope === 'global';
  $('installed-list').replaceChildren();
  $('installed-updates').disabled = true;
  if (scope === 'workspace' && !project) {
    $('installed-status').textContent = 'Save a target directory to see its installed context.';
    return;
  }
  $('installed-status').textContent = 'Checking installed context…';
  try {
    const result = await api('installed', {scope, project, tool: $('installed-agent').value});
    if (requestRevision !== inventoryRevision) return;
    installedItems = result.items;
    renderInstalled();
    $('installed-updates').disabled = false;
  } catch (error) {
    if (requestRevision === inventoryRevision) $('installed-status').textContent = error.message;
  }
}

$('open-installed').onclick = () => {
  const target = $('installed-target');
  const preferences = restoreInstalledSelection();
  const previous = target.value || preferences.project;
  target.replaceChildren(...state.projects.map(project => {
    const option = el('option', project.path);
    option.value = project.id;
    return option;
  }));
  if (state.projects.some(project => project.id === previous)) target.value = previous;
  if (!state.projects.length) $('installed-scope').value = 'global';
  else if (['workspace', 'global'].includes(preferences.scope)) $('installed-scope').value = preferences.scope;
  if (['codex', 'antigravity', 'claude'].includes(preferences.tool)) $('installed-agent').value = preferences.tool;
  if (typeof preferences.onlyUpdates === 'boolean') $('installed-updates').checked = preferences.onlyUpdates;
  $('installed-dialog').showModal();
  refreshInstalled();
};
for (const id of ['installed-scope', 'installed-target', 'installed-agent']) {
  $(id).onchange = refreshInstalled;
}
$('refresh-installed').onclick = refreshInstalled;
$('installed-updates').onchange = () => {
  saveInstalledSelection();
  renderInstalled();
};
$('back-to-installed').onclick = () => $('detail').close();

function projectError(message = '') {
  $('project-error').textContent = message;
  $('project-error').hidden = !message;
}

function openProjectDialog() {
  projectError();
  $('project-dialog').showModal();
}

async function browse(path) {
  projectError();
  const picker = $('folder-picker');
  picker.hidden = false;
  $('browse-folders').setAttribute('aria-expanded', 'true');
  $('folder-list').inert = true;
  $('browse-folders').disabled = true;
  $('folder-up').disabled = true;
  $('folder-use').disabled = true;
  try {
    folder = await api('directories', {path});
    $('folder-location').textContent = folder.path;
    $('folder-list').replaceChildren();
    for (const child of folder.children) {
      const button = el('button', child.name);
      button.type = 'button';
      button.onclick = () => browse(child.path);
      $('folder-list').append(button);
    }
    if (!folder.children.length) {
      $('folder-list').append(el('p', 'No subfolders'));
    }
  } catch (error) {
    projectError(error.message);
  } finally {
    $('folder-list').inert = false;
    $('browse-folders').disabled = false;
    $('folder-up').disabled = !folder?.parent;
    $('folder-use').disabled = !folder;
  }
}

$('add-project').onclick = openProjectDialog;
$('add-target').onclick = openProjectDialog;
$('browse-folders').onclick = () => browse($('project-path').value.trim() || folder?.path);
$('folder-up').onclick = () => browse(folder.parent);
$('folder-use').onclick = () => {
  $('project-path').value = folder.path;
  $('folder-picker').hidden = true;
  $('browse-folders').setAttribute('aria-expanded', 'false');
  $('project-path').focus();
};
for (const button of document.querySelectorAll('.close')) button.onclick = () => button.closest('dialog').close();
$('project-form').onsubmit = async event => {
  event.preventDefault();
  projectError();
  const form = event.target;
  const button = event.submitter;
  const fields = Object.fromEntries(new FormData(form));
  fields.path = fields.path.trim();
  button.disabled = true;
  try {
    const project = await api('projects', fields);
    if (!state.projects.some(item => item.id === project.id)) state.projects.push(project);
    projects();
    $('target').value = project.id;
    selectWorkspaceAgent();
    invalidate();
    $('project-dialog').close();
    form.reset();
    $('folder-picker').hidden = true;
    $('browse-folders').setAttribute('aria-expanded', 'false');
    notice('Target directory saved. Preview a context to load it.');
  } catch (error) {
    projectError(error.message);
  } finally {
    button.disabled = false;
  }
};
$('preview').onclick = () => busy($('preview'), async () => {
  invalidate();
  const requestRevision = revision;
  const global = $('scope').value === 'global';
  const operation = $('sync-operation').value;
  const remove = operation === 'remove';
  const allInstalled = global && $('global-bundle').value === 'all';
  const params = global
    ? {scope: 'global', tool: $('global-agent').value, allInstalled,
       selector: $('global-bundle').value === 'selected' ? selected.id : null}
    : {project: $('target').value, tool: $('workspace-agent').value, selector: selected.id};
  const result = await api('preview', {...params, operation});
  if (requestRevision !== revision) return;
  previewToken = result.token;
  $('diffs').replaceChildren();
  $('change-count').textContent = result.changes.length
    ? `${result.changes.length} file changes to review`
    : 'No content changes. Check engine output for protected files.';
  for (const change of result.changes) {
    const detail = el('details');
    const label = {add: 'Add', update: 'Update', remove: 'Remove'}[change.change];
    detail.append(el('summary', `${label} · ${change.path}`), el('pre', change.diff, 'diff'));
    $('diffs').append(detail);
  }
  $('logs').textContent = result.output;
  $('logs').parentElement.open = remove;
  const removeLabel = allInstalled ? 'Remove all global toolkit context'
    : global ? 'Remove global context' : 'Remove context from target';
  $('sync').textContent = remove ? removeLabel : (global ? 'Apply global sync' : 'Apply reviewed sync');
  $('sync').classList.toggle('remove-action', remove);
  $('sync').hidden = false;
  $('preview-result').hidden = false;
});
$('sync').onclick = () => busy($('sync'), async () => {
  const requestRevision = revision;
  const remove = $('sync-operation').value === 'remove';
  let result;
  try {
    result = await api('sync', {token: previewToken});
  } finally {
    if ($('installed-dialog').open) await refreshInstalled();
  }
  if (requestRevision !== revision) return;
  invalidate();
  $('logs').textContent = result.output;
  $('preview-result').hidden = false;
  $('logs').parentElement.open = true;
  $('change-count').textContent = remove ? 'Removal result' : 'Sync result';
  $('diffs').replaceChildren();
  $('sync').hidden = true;
});
function loadContextManager(data) {
  state = data;
  $('open-global').disabled = !state.globalSync;
  $('open-installed').disabled = false;
  projects();
  render();
}

function connectContextManager() {
  document.body.dataset.hosted = 'disconnected';
  $('pair-panel').hidden = false;
  const devOrigins = ['http://127.0.0.1:4200', 'http://localhost:4200'];
  if (devOrigins.includes(location.origin)) {
    $('pair-command').textContent = 'python3 apps/context-manager/server.py --pair-with ' + location.origin;
  }
  if (!hosted) {
    $('pair-command').textContent = 'python3 apps/context-manager/server.py';
    $('pair-code-label').textContent = 'Local access code';
    $('pair-instructions').textContent = 'Enter the local access code printed in your terminal.';
    $('pair-port').parentElement.hidden = true;
  }
  $('pair-disconnect').onclick = () => location.reload();
  $('pair-form').onsubmit = async event => {
    event.preventDefault();
    const button = event.submitter;
    const error = $('pair-error');
    button.disabled = true;
    error.hidden = true;
    if (hosted) apiOrigin = 'http://127.0.0.1:' + $('pair-port').valueAsNumber;
    try {
      const data = await api('bootstrap', {}, $('pair-code').value.trim());
      loadContextManager(data);
      $('pair-form').reset();
      $('pair-panel').hidden = true;
      $('pair-disconnect').hidden = false;
      document.body.dataset.hosted = 'connected';
    } catch (failure) {
      error.textContent = failure instanceof TypeError
        ? (hosted
          ? `Could not connect to ${apiOrigin}. Start the companion with the command above and match the port printed in your terminal. Allow browser loopback access if prompted.`
          : 'Could not reach Context Manager. Check that the local server is still running.')
        : failure.message;
      error.hidden = false;
    } finally {
      button.disabled = false;
    }
  };
}

connectContextManager();
