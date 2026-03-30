// ===== MODAL =====
function openModal(catId) {
  document.getElementById('modal-overlay').classList.remove('hidden');
  document.getElementById('m-amount').focus();
  if (catId) {
    const radio = document.getElementById('cat-' + catId);
    if (radio) radio.checked = true;
  }
}

function closeModal(e) {
  if (e && e.target !== document.getElementById('modal-overlay')) return;
  document.getElementById('modal-overlay').classList.add('hidden');
  document.getElementById('tx-form').reset();
  hideSuggestions();
}

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.getElementById('modal-overlay').classList.add('hidden');
    hideSuggestions();
  }
});

// ===== FORMATAÇÃO DE VALOR =====
function formatAmount(input) {
  let v = input.value.replace(/\D/g, '');
  if (!v) { input.value = ''; return; }
  v = (parseInt(v, 10) / 100).toFixed(2);
  input.value = v.replace('.', ',');
  // Armazena valor numérico para o form (com ponto)
  input.dataset.numeric = v;
}

document.getElementById('tx-form')?.addEventListener('submit', function() {
  const inp = document.getElementById('m-amount');
  if (inp.dataset.numeric) inp.value = inp.dataset.numeric;
});

// ===== AUTOCOMPLETE DE TAGS =====
let tagTimeout = null;

function searchTags(q) {
  clearTimeout(tagTimeout);
  if (q.length < 2) { hideSuggestions(); return; }
  tagTimeout = setTimeout(() => {
    fetch('/api/tags?q=' + encodeURIComponent(q))
      .then(r => r.json())
      .then(tags => showSuggestions(tags))
      .catch(() => {});
  }, 200);
}

function showSuggestions(tags) {
  const ul = document.getElementById('tag-suggestions');
  if (!tags.length) { hideSuggestions(); return; }
  ul.innerHTML = '';
  tags.forEach(t => {
    const li = document.createElement('li');
    li.textContent = t;
    li.addEventListener('mousedown', () => {
      document.getElementById('m-tag').value = t;
      hideSuggestions();
    });
    ul.appendChild(li);
  });
  ul.classList.remove('hidden');
}

function hideSuggestions() {
  document.getElementById('tag-suggestions')?.classList.add('hidden');
}

document.getElementById('m-tag')?.addEventListener('blur', () => {
  setTimeout(hideSuggestions, 150);
});

// ===== APAGAR TRANSAÇÃO =====
function deleteTx(id) {
  if (!confirm('Apagar esta movimentação?')) return;
  fetch('/transacao/' + id + '/apagar', { method: 'POST' })
    .then(r => r.json())
    .then(data => {
      if (data.ok) {
        const row = document.getElementById('tx-' + id);
        row?.remove();
      }
    })
    .catch(() => alert('Erro ao apagar.'));
}
