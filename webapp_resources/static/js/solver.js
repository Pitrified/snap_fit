/* Solver page interactions (v1: full page reload after each action). */

let SESSION_ID = '';
let DATASET_TAG = '';
let API_BASE = '';

function initSolver(sessionId, datasetTag) {
  SESSION_ID = sessionId;
  DATASET_TAG = datasetTag;
  API_BASE = '/api/v1/interactive/sessions/' + SESSION_ID;
}

function tagParam() {
  return DATASET_TAG ? '?dataset_tag=' + encodeURIComponent(DATASET_TAG) : '';
}

async function apiPost(path, body) {
  const res = await fetch(API_BASE + path + tagParam(), {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: body !== undefined ? JSON.stringify(body) : '{}',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({detail: res.statusText}));
    alert('Error: ' + (err.detail || JSON.stringify(err)));
    return null;
  }
  return res.json();
}

async function nextSuggestion(overridePos) {
  const body = overridePos ? {override_pos: overridePos} : {};
  const data = await apiPost('/next_suggestion', body);
  if (data) location.reload();
}

async function acceptSuggestion() {
  const data = await apiPost('/accept', {});
  if (data) location.reload();
}

async function skipSuggestion() {
  const data = await apiPost('/reject', {});
  if (data) location.reload();
}

async function undoLast() {
  const data = await apiPost('/undo', {});
  if (data) location.reload();
}

function selectSlot(posKey) {
  nextSuggestion(posKey);
}
