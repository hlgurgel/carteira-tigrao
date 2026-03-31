// ===== ESTADO DO MODAL =====
let currentTxType = 'income';

// ===== ABRIR / FECHAR MODAL =====
function openModal(txType, catId) {
  document.getElementById('modal-overlay').classList.remove('hidden');
  setTxType(txType || 'income');
  if (catId) preselectCategory(catId);
  setTimeout(() => document.getElementById('m-amount').focus(), 50);
}

function closeModal() {
  document.getElementById('modal-overlay').classList.add('hidden');
  document.getElementById('tx-form').reset();
  hideSuggestions();
}

function closeModalOverlay(e) {
  if (e.target === document.getElementById('modal-overlay')) closeModal();
}

// ===== TIPO DE TRANSAÇÃO (Entrada / Saída) =====
function setTxType(type) {
  currentTxType = type;
  document.getElementById('hidden-tx-type').value = type;

  document.getElementById('btn-income').classList.toggle('active', type === 'income');
  document.getElementById('btn-expense').classList.toggle('active', type === 'expense');

  const label = document.getElementById('cat-label');

  if (type === 'income') {
    label.textContent = 'Como distribuir?';
    renderIncomeCategories();
  } else {
    label.textContent = 'Categoria de saída';
    renderExpenseCategories();
  }
}

function renderIncomeCategories() {
  const sel = document.getElementById('cat-selector');
  sel.innerHTML = '';

  // Opção padrão: distribuir entre categorias
  sel.appendChild(makeCatOption(
    INCOME_CAT.id,
    'Distribuir entre categorias',
    INCOME_CAT.color,
    true
  ));

  // Cada categoria de despesa = entrada direta
  EXPENSE_CATS.forEach(cat => {
    sel.appendChild(makeCatOption(
      cat.id,
      `Direta → ${cat.name}`,
      cat.color,
      false
    ));
  });
}

function renderExpenseCategories() {
  const sel = document.getElementById('cat-selector');
  sel.innerHTML = '';
  EXPENSE_CATS.forEach((cat, i) => {
    sel.appendChild(makeCatOption(cat.id, cat.name, cat.color, i === 0));
  });
}

function makeCatOption(id, name, color, checked) {
  const lbl = document.createElement('label');
  lbl.className = 'cat-option';
  lbl.style.setProperty('--cat-color', color);
  lbl.innerHTML = `
    <input type="radio" name="category_id" value="${id}" ${checked ? 'checked' : ''} required/>
    <span>${name}</span>
  `;
  return lbl;
}

function preselectCategory(catId) {
  const radios = document.querySelectorAll('#cat-selector input[type="radio"]');
  radios.forEach(r => { r.checked = r.value === String(catId); });
}

// ===== FORMATAÇÃO DE VALOR =====
document.addEventListener('DOMContentLoaded', () => {
  const amountInput = document.getElementById('m-amount');
  if (!amountInput) return;

  amountInput.addEventListener('input', function () {
    // Remove tudo exceto dígitos
    let digits = this.value.replace(/\D/g, '');
    if (!digits) { this.value = ''; this.dataset.numeric = ''; return; }
    // Converte para centavos → reais com vírgula
    const num = parseInt(digits, 10) / 100;
    const formatted = num.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    this.value = formatted;
    this.dataset.numeric = num.toFixed(2);
  });

  document.getElementById('tx-form').addEventListener('submit', function () {
    const inp = document.getElementById('m-amount');
    if (inp.dataset.numeric) inp.value = inp.dataset.numeric;
  });

  // Inicializa o seletor de categorias
  renderIncomeCategories();
});

// ===== ATALHOS DE TECLADO =====
document.addEventListener('keydown', e => {
  const tag = document.activeElement?.tagName;
  const inInput = tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT';

  if (e.key === 'Escape') {
    closeModal();
    return;
  }

  if (inInput) return;

  if (e.key === 'n' || e.key === 'N') {
    e.preventDefault();
    openModal();
    return;
  }

  if (e.key === 'ArrowLeft') {
    e.preventDefault();
    document.getElementById('nav-prev')?.click();
    return;
  }

  if (e.key === 'ArrowRight') {
    e.preventDefault();
    document.getElementById('nav-next')?.click();
    return;
  }
});

// ===== PAINEL DE ATALHOS =====
function toggleShortcuts() {
  document.getElementById('shortcuts-panel').classList.toggle('hidden');
}

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

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('m-tag')?.addEventListener('blur', () => {
    setTimeout(hideSuggestions, 150);
  });
});

// ===== APAGAR TRANSAÇÃO =====
function deleteTx(id) {
  if (!confirm('Apagar esta movimentação?')) return;
  fetch('/transacao/' + id + '/apagar', { method: 'POST' })
    .then(r => r.json())
    .then(data => { if (data.ok) document.getElementById('tx-' + id)?.remove(); })
    .catch(() => alert('Erro ao apagar.'));
}
