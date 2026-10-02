const $ = (id) => document.getElementById(id);
const state = {papers: [], selected: new Set(), task: 'summarize', busy: false, job: null};
const titles = {summarize: 'Paper overview', compare: 'Method comparison', ideas: 'Experiment notebook', question: 'Research answer', related: 'Related work'};

function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

async function api(path, body, method = 'POST') {
  const options = body === undefined ? {} : {method};
  if (body instanceof FormData) options.body = body;
  else if (body !== undefined) {
    options.body = JSON.stringify(body);
    options.headers = {'Content-Type': 'application/json'};
  }
  const response = await fetch(path, options);
  const value = await response.json();
  if (!response.ok) throw new Error(typeof value.detail === 'string' ? value.detail : 'Please check the input and try again.');
  return value;
}

function message(text = '') {
  $('message').textContent = text;
  $('message').classList.toggle('hidden', !text);
}

function syncSelection() {
  $('selection-note').textContent = state.selected.size ? `${state.selected.size} paper${state.selected.size > 1 ? 's' : ''} selected` : 'Select a paper to begin';
}

async function refreshLibrary() {
  state.papers = await api('/api/papers');
  const list = $('library'); list.replaceChildren();
  $('paper-count').textContent = state.papers.length;
  state.papers.forEach(paper => {
    const label = el('label', undefined, 'paper-item');
    const check = document.createElement('input'); check.type = 'checkbox';
    check.checked = state.selected.has(paper.id); check.setAttribute('aria-label', `Select ${paper.title} (${paper.kind})`);
    check.addEventListener('change', () => {
      if (check.checked && state.selected.size >= 4) { check.checked = false; message('Select at most four papers per analysis.'); return; }
      check.checked ? state.selected.add(paper.id) : state.selected.delete(paper.id);
      syncSelection();
    });
    const text = el('div'); text.append(el('strong', paper.title), el('small', `${paper.kind === 'demo' ? 'Synthetic demo' : paper.kind} · ${paper.pages} page${paper.pages > 1 ? 's' : ''}`));
    label.append(check, text); list.append(label);
  });
  syncSelection();
}

function selectTask(task) {
  if (state.busy) return;
  state.task = task;
  document.querySelectorAll('.task').forEach(button => button.classList.toggle('active', button.dataset.task === task));
  $('report-title').textContent = titles[task];
  $('run').textContent = task === 'related' ? 'Search arXiv ↗' : task === 'ideas' ? 'Draft experiment plan ↗' : task === 'question' ? 'Answer from papers ↗' : 'Build research brief ↗';
  $('external-note').classList.toggle('hidden', task !== 'related');
  $('focus-label').textContent = task === 'related' ? 'SEARCH KEYWORDS · REQUIRED' : task === 'question' ? 'RESEARCH QUESTION · REQUIRED' : 'RESEARCH FOCUS · OPTIONAL';
  $('focus').placeholder = task === 'related' ? 'e.g. low rank adaptation language models' : task === 'question' ? 'e.g. Which evaluation datasets did the authors use?' : 'e.g. How could I test the memory–quality tradeoff on a small GPU?';
}

function appendInline(parent, text) {
  // All model/PDF text becomes text nodes. No HTML or model-supplied links are executed.
  const parts = text.split(/(\[E\d+\]|\*\*[^*]+\*\*)/g);
  for (const part of parts) {
    if (/^\[E\d+\]$/.test(part)) {
      const button = el('button', part, 'citation');
      button.addEventListener('click', () => {
        const target = document.getElementById(`source-${part.slice(1,-1)}`);
        if (!target) return;
        document.querySelectorAll('.evidence-card').forEach(c => c.classList.remove('selected'));
        target.classList.add('selected'); target.open = true;
        target.scrollIntoView({behavior: 'smooth', block: 'nearest'});
      });
      parent.append(button);
    } else if (part.startsWith('**') && part.endsWith('**')) parent.append(el('strong', part.slice(2,-2)));
    else parent.append(document.createTextNode(part));
  }
}

function renderMarkdown(text, target) {
  target.replaceChildren();
  let paragraph = [], list = null;
  function flush() {
    if (paragraph.length) { const p = el('p'); appendInline(p, paragraph.join(' ')); target.append(p); paragraph = []; }
    list = null;
  }
  for (const line of text.split('\n')) {
    if (!line.trim()) { flush(); continue; }
    const heading = line.match(/^#{1,4}\s+(.+)/);
    const bullet = line.match(/^(?:[-*]|\d+[.)])\s+(.+)/);
    if (heading) { flush(); const h = el(line.startsWith('###') ? 'h3' : 'h2'); appendInline(h, heading[1]); target.append(h); }
    else if (bullet) {
      if (paragraph.length) flush();
      if (!list) { list = el('ul'); target.append(list); }
      const item = el('li'); appendInline(item, bullet[1]); list.append(item);
    } else { list = null; paragraph.push(line); }
  }
  flush();
}

function renderEvidence(evidence) {
  $('evidence').replaceChildren(); $('evidence-count').textContent = evidence.length;
  evidence.forEach((source, index) => {
    const card = el('details', undefined, 'evidence-card'); card.id = `source-${source.ref}`; card.open = index === 0;
    card.append(el('summary', `[${source.ref}] ${source.title}`), el('small', `PAGE ${source.page} · ${source.kind.toUpperCase()}`), el('p', source.text));
    $('evidence').append(card);
  });
}

function renderTrace(trace) {
  $('trace').replaceChildren(); $('trace').classList.remove('hidden');
  trace.forEach(item => $('trace').append(el('span', item.step)));
}

async function research() {
  if (state.busy) return;
  const focus = $('focus').value.trim();
  if (state.task === 'related') { await searchRelated(focus); return; }
  if (!state.selected.size) { message('Choose a paper in the library, or add your first PDF.'); return; }
  if (state.task === 'compare' && state.selected.size < 2) { message('Select at least two papers for a comparison.'); return; }
  if (state.task === 'question' && !focus) { message('Enter the question you want to investigate.'); return; }
  state.busy = true; $('run').disabled = true; $('export').classList.add('hidden'); message();
  $('report').replaceChildren(el('p', 'Reading your selected papers… The first local run also loads the model.'));
  $('evidence').replaceChildren(); $('evidence-count').textContent = '0';
  try {
    const created = await api('/api/research', {task: state.task, paper_ids: [...state.selected], question: focus, language: $('language').value});
    state.job = created.job_id;
    const deadline = Date.now() + 20 * 60 * 1000;
    while (Date.now() < deadline) {
      const job = await api(`/api/jobs/${state.job}`);
      renderTrace(job.payload.trace || []);
      if (job.status === 'failed') throw new Error(job.payload.error || 'Analysis failed.');
      if (job.status === 'complete') {
        const report = job.payload;
        renderEvidence(report.evidence); renderMarkdown(report.markdown, $('report'));
        const meta = report.usage;
        $('report').append(el('div', `${meta.provider === 'evidence' ? 'Extractive baseline · no LLM' : meta.model} · ${report.seconds.toFixed(1)}s · ${report.validation.cited.length} reference IDs checked${created.cached ? ' · cached' : ''}`, 'report-meta'));
        if (report.warnings.length) message(report.warnings.join(' '));
        $('export').classList.remove('hidden'); return;
      }
      $('report').replaceChildren(el('p', `${job.payload.stage || 'Working'}…`), el('p', 'The local model may take a few minutes. You can keep this page open while it works.'));
      await new Promise(resolve => setTimeout(resolve, 1500));
    }
    throw new Error('This task is taking longer than expected. The server continues working; rerun later to retrieve a completed cached report.');
  } catch (error) { message(error.message); $('report').replaceChildren(el('p', 'The analysis did not complete. No generated claims were published.')); }
  finally { state.busy = false; $('run').disabled = false; }
}

async function searchRelated(query) {
  if (query.length < 3) { message('Enter a few research keywords to search arXiv.'); return; }
  state.busy = true; $('run').disabled = true; message(); $('export').classList.add('hidden'); $('trace').classList.add('hidden');
  renderEvidence([]);
  $('report').replaceChildren(el('p', 'Searching arXiv metadata…'));
  try {
    const result = await api('/api/related', {query, limit: 5});
    $('report').replaceChildren();
    if (!result.papers.length) $('report').append(el('p', 'No papers matched these terms. Try fewer or broader keywords.'));
    result.papers.forEach(paper => {
      const card = el('div', undefined, 'related-card'); const link = el('a', paper.title);
      link.href = paper.url; link.target = '_blank'; link.rel = 'noopener noreferrer';
      const title = el('h3'); title.append(link);
      card.append(title, el('small', `${paper.authors.slice(0,3).join(', ')} · ${paper.published}`), el('p', paper.abstract));
      const button = el('button', 'Add abstract to library +', 'primary');
      button.addEventListener('click', async () => {
        button.disabled = true;
        try { const imported = await api('/api/papers/arxiv', {arxiv_id: paper.arxiv_id});
          if (state.selected.size < 4) state.selected.add(imported.id);
          await refreshLibrary(); button.textContent = 'Abstract added ✓';
          message('Added abstract only. Upload the full PDF to analyze detailed methods and results.');
        } catch(error) { message(error.message); button.disabled = false; }
      });
      card.append(button); $('report').append(card);
    });
  } catch (error) { message(error.message); $('report').replaceChildren(el('p', 'arXiv search could not complete. Your local library is still available.')); }
  finally { state.busy = false; $('run').disabled = false; }
}

$('pdf-form').addEventListener('submit', async event => {
  event.preventDefault(); const file = $('pdf').files[0]; if (!file) return;
  if (file.size > 20 * 1024 * 1024) { message('Please choose a PDF smaller than 20 MiB.'); return; }
  const button = event.submitter; button.disabled = true; message('Extracting paper text…');
  try { const data = new FormData(); data.append('file', file);
    const paper = await api('/api/papers/pdf', data);
    if (state.selected.size < 4) state.selected.add(paper.id);
    await refreshLibrary(); message(paper.warning || (paper.duplicate ? 'This paper is already in your library.' : `${paper.title} imported with ${paper.chunk_count} evidence passages.`));
    $('import-panel').classList.add('hidden');
  } catch(error) { message(error.message); } finally { button.disabled = false; }
});
$('text-form').addEventListener('submit', async event => {
  event.preventDefault(); event.submitter.disabled = true;
  try { const paper = await api('/api/papers/text', {title: $('text-title').value, text: $('paper-text').value});
    if (state.selected.size < 4) state.selected.add(paper.id);
    await refreshLibrary(); message('Text imported. Text imports use logical pages, not PDF page numbers.'); $('import-panel').classList.add('hidden');
  } catch(error) { message(error.message); } finally { event.submitter.disabled = false; }
});
$('demo').addEventListener('click', async () => {
  $('demo').disabled = true;
  try { const papers = await api('/api/demo', {}); state.selected = new Set(papers.slice(0,1).map(p=>p.id)); await refreshLibrary(); message('Sample library loaded. These are synthetic teaching notes, not published research papers.'); }
  catch(error) { message(error.message); } finally { $('demo').disabled = false; }
});
$('import-toggle').addEventListener('click', () => $('import-panel').classList.toggle('hidden'));
$('empty-import').addEventListener('click', () => { $('import-panel').classList.remove('hidden'); $('import-panel').scrollIntoView({behavior: 'smooth'}); });
document.querySelectorAll('.task').forEach(button => button.addEventListener('click', () => selectTask(button.dataset.task)));
$('question-mode').addEventListener('click', () => { selectTask('question'); $('focus').focus(); });
$('run').addEventListener('click', research);
$('export').addEventListener('click', () => { if (state.job) window.location.href = `/api/jobs/${state.job}/export`; });
async function start() {
  try { const health = await api('/api/health'); $('model').textContent = health.provider === 'evidence' ? 'Evidence mode · no LLM' : `${health.model.split('/').pop()} · local`; await refreshLibrary(); }
  catch(error) { $('model').textContent = 'Server unavailable'; message(error.message); }
}
start();
