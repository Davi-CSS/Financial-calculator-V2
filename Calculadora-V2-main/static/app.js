// ═══════════════════════════════════════════════════════════
//  app.js — Calculadora Financeira v2
//  Depende de: Chart.js (global window.Chart)
// ═══════════════════════════════════════════════════════════

'use strict';

// ─────────────────────────────────────────────
// NAVEGAÇÃO
// ─────────────────────────────────────────────
document.querySelectorAll('.nav button').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tool').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.target).classList.add('active');
    if (btn.dataset.target === 'cambio' && !cambio.loaded) cambio.fetchRates();
  });
});

// ─────────────────────────────────────────────
// UTILITÁRIOS COMPARTILHADOS
// ─────────────────────────────────────────────
const charts = {};

function destroyChart(id) {
  if (charts[id]) { charts[id].destroy(); delete charts[id]; }
}

/**
 * Formata número como moeda BRL.
 * Ex: 1234.5 → "R$ 1.234,50"
 */
function fmtBRL(v) {
  return 'R$ ' + Number(v).toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

/**
 * Formata número como moeda genérica.
 * @param {number} v
 * @param {'brl'|'usd'|'eur'} cur
 */
function fmtCur(v, cur) {
  const syms = { brl: 'R$ ', usd: 'US$ ', eur: '€ ' };
  return (syms[cur] ?? '') + Number(v).toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

/**
 * Valida um array de [valor, nomeLabel] e exibe erro se inválido.
 * Retorna true se todos passam.
 */
function validate(fields, errId) {
  const el = document.getElementById(errId);
  el.textContent = '';
  for (const [val, label] of fields) {
    if (val === null || isNaN(val)) {
      el.textContent = `⚠ Campo "${label}" inválido.`; return false;
    }
    if (val <= 0) {
      el.textContent = `⚠ "${label}" deve ser maior que zero.`; return false;
    }
  }
  return true;
}

/**
 * Gera HTML de tabela a partir de rows + definição de colunas.
 * @param {Object[]} rows
 * @param {{ key: string, label: string, fmt?: Function }[]} cols
 */
function buildTable(rows, cols) {
  const head = cols.map(c => `<th>${c.label}</th>`).join('');
  const body = rows.map(r =>
    '<tr>' + cols.map(c => `<td>${c.fmt ? c.fmt(r[c.key]) : r[c.key]}</td>`).join('') + '</tr>'
  ).join('');
  return `<thead><tr>${head}</tr></thead><tbody>${body}</tbody>`;
}

/**
 * Cria (ou recria) um gráfico de linha no canvas indicado.
 */
function makeLineChart(canvasId, labels, data, label, color) {
  destroyChart(canvasId);
  charts[canvasId] = new Chart(document.getElementById(canvasId), {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label,
        data,
        borderColor: color,
        backgroundColor: color + '18',
        borderWidth: 1.5,
        pointRadius: 0,
        fill: true,
        tension: 0.35
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          ticks: { color: '#555', maxTicksLimit: 10, font: { family: 'DM Mono', size: 10 } },
          grid:  { color: 'rgba(255,255,255,.04)' }
        },
        y: {
          ticks: {
            color: '#555',
            font: { family: 'DM Mono', size: 10 },
            callback: v => 'R$' + (v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v.toFixed(0))
          },
          grid: { color: 'rgba(255,255,255,.04)' }
        }
      }
    }
  });
}

function showEl(id)  { document.getElementById(id).style.display = 'block'; }
function setInfo(id, text) {
  const el = document.getElementById(id);
  el.textContent = text;
  el.style.display = text ? 'inline-block' : 'none';
}

// ─────────────────────────────────────────────
// BÁSICO
// ─────────────────────────────────────────────
function calcBasic() {
  const a   = parseFloat(document.getElementById('b1').value);
  const b   = parseFloat(document.getElementById('b2').value);
  const err = document.getElementById('basic-err');
  err.textContent = '';

  if (isNaN(a) || isNaN(b)) {
    err.textContent = '⚠ Preencha ambos os campos.'; return;
  }

  const fmt = n => Number(n).toLocaleString('pt-BR', { maximumFractionDigits: 6 });

  document.getElementById('b-soma').textContent  = fmt(a + b);
  document.getElementById('b-sub').textContent   = fmt(a - b);
  document.getElementById('b-mult').textContent  = fmt(a * b);
  document.getElementById('b-div').textContent   = b !== 0 ? fmt(a / b) : 'Divisão por zero';

  document.getElementById('basic-res').style.display = 'grid';
}

// ─────────────────────────────────────────────
// PRICE
// ─────────────────────────────────────────────

/**
 * Tenta chamar o endpoint backend /api/price.
 * Retorna o array de linhas já normalizado, ou null se falhar.
 */
async function _priceFromBackend(payload) {
  try {
    const res = await fetch('/api/price', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) return null;
    const data = await res.json();

    // Normaliza campos do backend → padrão interno { p, pmt, juros, amort, saldo }
    if (!Array.isArray(data.table)) return null;
    return data.table.map((r, idx) => ({
      p:     r.parcela ?? r.p ?? idx + 1,
      pmt:   r.prestacao ?? r.pmt ?? 0,
      juros: r.juros ?? r.interest ?? 0,
      amort: r.amortizacao ?? r.amort ?? 0,
      saldo: r.saldo_devedor ?? r.saldo ?? r.ending ?? 0
    }));
  } catch {
    return null;
  }
}

/**
 * Calcula Price localmente — fallback garantido.
 */
function _priceLocal(cap, taxa, n) {
  const fator = Math.pow(1 + taxa, n);
  const pmt   = cap * (taxa * fator) / (fator - 1);
  let saldo   = cap;
  const rows  = [];

  for (let i = 1; i <= n; i++) {
    const juros = saldo * taxa;
    const amort = pmt - juros;
    saldo = Math.max(0, saldo - amort);
    rows.push({ p: i, pmt, juros, amort, saldo });
  }
  return rows;
}

async function calcPrice() {
  const cap  = parseFloat(document.getElementById('p-cap').value);
  const taxa = parseFloat(document.getElementById('p-taxa').value) / 100;
  const n    = parseInt(document.getElementById('p-n').value);

  if (!validate([[cap,'Capital'],[taxa * 100,'Taxa'],[n,'Parcelas']], 'p-err')) return;

  // Tenta backend; usa cálculo local como fallback
  let rows = await _priceFromBackend({ capital: cap, taxa_mensal: taxa, parcelas: n });
  let origem = 'backend';
  if (!rows) {
    rows   = _priceLocal(cap, taxa, n);
    origem = 'local';
  }

  const totalJuros = rows.reduce((s, r) => s + r.juros, 0);
  setInfo('p-info', `Prestação fixa: ${fmtBRL(rows[0].pmt)} · Total juros: ${fmtBRL(totalJuros)} · via ${origem}`);

  document.getElementById('p-table').innerHTML = buildTable(rows, [
    { key: 'p',     label: '#' },
    { key: 'pmt',   label: 'Prestação', fmt: fmtBRL },
    { key: 'juros', label: 'Juros',     fmt: fmtBRL },
    { key: 'amort', label: 'Amort.',    fmt: fmtBRL },
    { key: 'saldo', label: 'Saldo',     fmt: fmtBRL }
  ]);

  showEl('p-chart-wrap');
  showEl('p-table-wrap');
  makeLineChart('p-chart', rows.map(r => r.p), rows.map(r => r.saldo), 'Saldo Price', '#34d399');
}

// ─────────────────────────────────────────────
// SAC
// ─────────────────────────────────────────────
function calcSAC() {
  const cap  = parseFloat(document.getElementById('s-cap').value);
  const taxa = parseFloat(document.getElementById('s-taxa').value) / 100;
  const n    = parseInt(document.getElementById('s-n').value);

  if (!validate([[cap,'Capital'],[taxa * 100,'Taxa'],[n,'Períodos']], 's-err')) return;

  const amort = cap / n;
  let saldo   = cap;
  const rows  = [];

  for (let i = 1; i <= n; i++) {
    const juros = saldo * taxa;
    const pmt   = amort + juros;
    saldo = Math.max(0, saldo - amort);
    rows.push({ p: i, pmt, juros, amort, saldo });
  }

  const totalJuros = rows.reduce((s, r) => s + r.juros, 0);
  setInfo('s-info', `Amort. fixa: ${fmtBRL(amort)} · Total juros: ${fmtBRL(totalJuros)}`);

  document.getElementById('s-table').innerHTML = buildTable(rows, [
    { key: 'p',     label: '#' },
    { key: 'pmt',   label: 'Prestação', fmt: fmtBRL },
    { key: 'juros', label: 'Juros',     fmt: fmtBRL },
    { key: 'amort', label: 'Amort.',    fmt: fmtBRL },
    { key: 'saldo', label: 'Saldo',     fmt: fmtBRL }
  ]);

  showEl('s-chart-wrap');
  showEl('s-table-wrap');
  makeLineChart('s-chart', rows.map(r => r.p), rows.map(r => r.saldo), 'Saldo SAC', '#fbbf24');
}

// ─────────────────────────────────────────────
// CÂMBIO
// ─────────────────────────────────────────────
const cambio = {
  rates:  { usd: null, eur: null },
  loaded: false,

  curNames: { brl: 'Real (BRL)', usd: 'Dólar (USD)', eur: 'Euro (EUR)' },

  /**
   * Retorna a taxa de conversão entre dois pares suportados.
   * Suporta: USD↔BRL, EUR↔BRL, USD↔EUR (e inversos), além de mesmo-par.
   */
  getRate(de, para) {
    const { usd, eur } = this.rates;
    if (de === para)                        return 1;
    if (de === 'usd' && para === 'brl')     return usd;
    if (de === 'brl' && para === 'usd')     return 1 / usd;
    if (de === 'eur' && para === 'brl')     return eur;
    if (de === 'brl' && para === 'eur')     return 1 / eur;
    if (de === 'usd' && para === 'eur')     return usd / eur;
    if (de === 'eur' && para === 'usd')     return eur / usd;
    return null;
  },

  setStatus(text, live = false) {
    const dot  = document.getElementById('cambio-status-dot');
    const txt  = document.getElementById('cambio-status-text');
    dot.className  = 'status-dot' + (live ? ' live' : '');
    txt.textContent = text;
  },

  setRateCard(cur, value) {
    document.getElementById(`rate-${cur}`).textContent =
      'R$ ' + value.toLocaleString('pt-BR', { minimumFractionDigits: 4, maximumFractionDigits: 4 });
    document.getElementById(`rate-${cur}-sub`).textContent = 'Cotação de compra (bid) — ao vivo';
  },

  async fetchRates() {
    this.setStatus('Consultando API…');
    document.getElementById('c-err').textContent = '';
    try {
      const res  = await fetch('https://economia.awesomeapi.com.br/json/last/USD-BRL,EUR-BRL');
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();

      this.rates.usd = parseFloat(data.USDBRL.bid);
      this.rates.eur = parseFloat(data.EURBRL.bid);

      this.setRateCard('usd', this.rates.usd);
      this.setRateCard('eur', this.rates.eur);
      this.setStatus('Cotações atualizadas', true);
      this.loaded = true;

    } catch (e) {
      this.setStatus('Erro ao carregar cotações');
      document.getElementById('c-err').textContent =
        '⚠ Não foi possível obter as cotações. Verifique sua conexão e tente novamente.';
    }
  },

  convert() {
    const errEl = document.getElementById('c-err');
    errEl.textContent = '';

    if (!this.loaded) {
      errEl.textContent = '⚠ Cotações ainda não carregadas. Clique em "↻ Atualizar".';
      this.fetchRates();
      return;
    }

    const valor = parseFloat(document.getElementById('c-valor').value);
    const de    = document.getElementById('c-de').value;
    const para  = document.getElementById('c-para').value;

    if (isNaN(valor) || valor < 0) {
      errEl.textContent = '⚠ Informe um valor válido.'; return;
    }

    const taxa       = this.getRate(de, para);
    const convertido = valor * taxa;

    document.getElementById('c-de-label').textContent   = this.curNames[de];
    document.getElementById('c-de-val').textContent     = fmtCur(valor, de);
    document.getElementById('c-para-label').textContent = this.curNames[para];
    document.getElementById('c-para-val').textContent   = fmtCur(convertido, para);
    document.getElementById('c-result').style.display   = 'flex';

    // Gráfico de barras comparativo
    const barColors = { brl: '#34d399', usd: '#60a5fa', eur: '#818cf8' };
    destroyChart('c-chart');
    charts['c-chart'] = new Chart(document.getElementById('c-chart'), {
      type: 'bar',
      data: {
        labels: [this.curNames[de], this.curNames[para]],
        datasets: [{
          data: [valor, convertido],
          backgroundColor: [barColors[de] + 'bb', barColors[para] + 'bb'],
          borderColor:     [barColors[de],         barColors[para]],
          borderWidth: 1,
          borderRadius: 6,
          barThickness: 60
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: '#555', font: { family: 'DM Mono', size: 11 } }, grid: { display: false } },
          y: { ticks: { color: '#555', font: { family: 'DM Mono', size: 10 } }, grid: { color: 'rgba(255,255,255,.04)' } }
        }
      }
    });
    showEl('c-chart-wrap');
  }
};

// Expõe funções chamadas diretamente pelo HTML (onclick="...")
window.calcBasic  = calcBasic;
window.calcPrice  = calcPrice;
window.calcSAC    = calcSAC;
window.converter  = () => cambio.convert();
window.fetchRates = () => cambio.fetchRates();  