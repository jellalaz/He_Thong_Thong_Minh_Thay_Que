// Analysis of the fixed evaluation split. The slider changes only this display.
let studyEvidenceRequest;
const studyColors = {mlp:'#086a68', cnn:'#ac482c', transformer:'#5750a4'};

function confusionAt(labels, scores, threshold) {
  const counts = [[0, 0], [0, 0]];
  labels.forEach((actual, i) => counts[actual][Number(scores[i] >= threshold)]++);
  return counts;
}

function rankingChart(models, metric, prevalence) {
  const isRoc = metric === 'roc';
  const title = isRoc ? 'ROC' : 'Precision–Recall';
  const x = value => 42 + value * 226;
  const y = value => 144 - value * 117;
  const path = (points, step) => points.map(([a,b], i) =>
    i === 0 ? 'M' + x(a) + ' ' + y(b) : step ? 'H' + x(a) + 'V' + y(b) : 'L' + x(a) + ' ' + y(b)).join(' ');
  const baseline = isRoc ? [[0,0],[1,1]] : [[0,prevalence],[1,prevalence]];
  const traces = Object.entries(models).map(([version,model]) =>
    '<path d="' + path(model[metric], !isRoc) + '" stroke="' + studyColors[version] + '" stroke-width="2.2" fill="none"/>').join('');
  const summary = Object.entries(models).map(([version, model]) =>
    model.label + ' ' + (isRoc ? model.auc : model.ap).toFixed(3)).join(' · ');
  return '<figure><figcaption>' + title + '</figcaption><svg viewBox="0 0 290 179" role="img" aria-label="' + title + ', ' + summary + '">' +
    '<path d="M42 27V144H268" fill="none" stroke="#68807e"/><path d="' + path(baseline, false) + '" fill="none" stroke="#809390" stroke-dasharray="3 4"/>' + traces +
    '<g font-size="10" fill="#344d50"><text x="34" y="148" text-anchor="end">0</text><text x="34" y="31" text-anchor="end">1</text><text x="263" y="157">1</text>' +
    '<text x="44" y="17">' + (isRoc ? 'Tỷ lệ dương thật' : 'Precision') + '</text><text x="155" y="174" text-anchor="middle">' + (isRoc ? 'Tỷ lệ dương giả' : 'Recall') + '</text></g></svg>' +
    '<small>' + (isRoc ? 'AUC' : 'AP') + ' · ' + Object.entries(models).map(([id, model]) =>
      '<b style="color:' + studyColors[id] + '">' + model.label + ' ' + (isRoc ? model.auc : model.ap).toFixed(3) + '</b>').join(' · ') + '</small></figure>';
}

function renderStudyEvidence(data) {
  const record = data[document.querySelector('#proof-dataset').value];
  const labels = record.actual;
  const positive = labels.reduce((sum, n) => sum + n, 0);
  const threshold = Number(document.querySelector('#proof-threshold').value);
  document.querySelector('#proof-source').textContent = labels.length + ' mẫu test · ' + positive + ' nhãn dương · ' + record.source;
  document.querySelector('#proof-curves').innerHTML = ['roc','pr'].map(metric => rankingChart(record.models, metric, positive / labels.length)).join('');
  document.querySelector('#proof-value').textContent = threshold.toFixed(2).replace('.', ',');
  document.querySelector('#proof-matrices').innerHTML = Object.entries(record.models).map(([version, model]) => {
    const [[tn,fp],[fn,tp]] = confusionAt(labels, model.scores, threshold);
    return '<table><caption>' + version.toUpperCase() + ' · ma trận nhầm lẫn</caption><thead><tr><th>Thật / đoán</th><th>Âm</th><th>Dương</th></tr></thead><tbody><tr><th>Âm</th><td>' + tn + '</td><td>' + fp + '</td></tr><tr><th>Dương</th><td>' + fn + '</td><td>' + tp + '</td></tr></tbody></table>';
  }).join('');
}

async function loadStudyEvidence() {
  try {
    if (!studyEvidenceRequest) studyEvidenceRequest = api('/assets/study-evidence.json');
    const data = await studyEvidenceRequest;
    const render = () => renderStudyEvidence(data);
    document.querySelector('#proof-dataset').onchange = render;
    document.querySelector('#proof-threshold').oninput = render;
    render();
  } catch (err) {
    studyEvidenceRequest = null;
    document.querySelector('#proof-source').textContent = 'Chưa đọc được kết quả test. Mở lại mục này để thử lại.';
  }
}
