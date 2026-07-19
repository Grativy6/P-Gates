const source = document.querySelector('#source');
const provider = document.querySelector('#provider');
const status = document.querySelector('#status');
const results = document.querySelector('#results');
const modeBadge = document.querySelector('#mode-badge');
const exportStatus = document.querySelector('#export-status');
let latestResult = null;

function updateProviderBadge() {
  const live = provider.value === 'openai';
  modeBadge.textContent = live
    ? '● OpenAI live mode — submitted text will be sent to the configured provider.'
    : '● Mock mode — deterministic demo analysis; no API key or external model is used.';
  modeBadge.classList.toggle('live', live);
}

function escapeHtml(value) {
  return value.replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
}

function renderPanel(id, panel) {
  const items = panel.findings.map(f => `<li><strong>${escapeHtml(f.category)}</strong><span class="phrase">${escapeHtml(f.phrase)}</span><p>${escapeHtml(f.issue)}</p><p class="safer"><span>Safer wording</span>${escapeHtml(f.safer_wording)}</p></li>`).join('');
  document.querySelector(`#${id}`).innerHTML = `<h2>${id.toUpperCase()}</h2><p class="summary">${escapeHtml(panel.summary)}</p><ul>${items}</ul>`;
}

function render(result) {
  ['pal', 'pecan', 'pea', 'seed'].forEach(name => renderPanel(name, result[name]));
  document.querySelector('#trace').innerHTML = result.trace.map(t => `<div class="trace-row"><p><span>Original phrase</span>${escapeHtml(t.original_phrase)}</p><p><span>${escapeHtml(t.layer)} problem</span>${escapeHtml(t.detected_problem)}</p><p><span>Safer wording</span>${escapeHtml(t.safer_wording)}</p></div>`).join('');
  document.querySelector('#disclaimer').textContent = result.disclaimer;
  exportStatus.textContent = '';
  results.hidden = false;
}

async function requestAnalysis() {
  const sourceText = source.value.trim();
  if (!sourceText) { status.textContent = 'Paste or load text first.'; return; }
  status.textContent = provider.value === 'mock' ? 'Analyzing in mock mode…' : 'Analyzing with OpenAI live mode…';
  const response = await fetch('/api/analyze', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({source_text:sourceText, provider:provider.value})});
  if (!response.ok) { const body = await response.json(); status.textContent = body.detail?.message || 'The analysis could not be completed.'; return; }
  latestResult = await response.json(); render(latestResult); status.textContent = `${latestResult.provider === 'mock' ? 'Mock' : 'Live'} analysis complete (${latestResult.model_identifier}).`;
}

function markdown(result) {
  const panel = (name, value) => `## ${name}\n\n${value.summary}\n\n${value.findings.map(f => `- **${f.category}** — “${f.phrase}”\n  - Issue: ${f.issue}\n  - Safer wording: ${f.safer_wording}`).join('\n')}`;
  return `# P-Gates mock route analysis\n\nProvider: ${result.provider}\nModel: ${result.model_identifier}\nTimestamp: ${result.analysis_timestamp}\n\n## Source text\n\n${result.source_text}\n\n${panel('PAL',result.pal)}\n\n${panel('PECAN',result.pecan)}\n\n${panel('PEA',result.pea)}\n\n${panel('SEED',result.seed)}\n\n## Trace\n\n${result.trace.map(t => `- **${t.layer}**: “${t.original_phrase}” → ${t.detected_problem}\n  - Safer wording: ${t.safer_wording}`).join('\n')}\n\n> ${result.disclaimer}\n`;
}

function download(content, type, filename) {
  const url = URL.createObjectURL(new Blob([content], {type}));
  const a = document.createElement('a'); a.href = url; a.download = filename; a.click(); URL.revokeObjectURL(url);
}

provider.addEventListener('change', updateProviderBadge);
document.querySelector('#load-example').addEventListener('click', async () => { const response = await fetch('/api/example'); source.value = (await response.json()).source_text; status.textContent = 'Built-in fictional example loaded.'; });
document.querySelector('#analyze').addEventListener('click', requestAnalysis);
document.querySelector('#export-json').addEventListener('click', () => { if (latestResult) { download(JSON.stringify(latestResult, null, 2), 'application/json', 'p-gates-analysis.json'); exportStatus.textContent = 'JSON export downloaded.'; } });
document.querySelector('#export-markdown').addEventListener('click', () => { if (latestResult) { download(markdown(latestResult), 'text/markdown', 'p-gates-analysis.md'); exportStatus.textContent = 'Markdown export downloaded.'; } });
