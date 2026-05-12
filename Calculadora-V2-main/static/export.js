/**
 * export.js — Calculadora Financeira v2
 * Exporta tabelas para CSV, Excel (.xlsx) e PDF.
 *
 * Dependências externas (carregadas sob demanda):
 *   XLSX  — https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js
 *   jsPDF — https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js
 *   jsPDF-AutoTable — https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.8.2/jspdf.plugin.autotable.min.js
 */

'use strict';

// ─────────────────────────────────────────────
// UTILITÁRIOS INTERNOS
// ─────────────────────────────────────────────

/**
 * Carrega um script externo uma única vez.
 * Resolve imediatamente se já estiver no DOM.
 */
function _loadScript(url) {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${url}"]`)) { resolve(); return; }
    const s = document.createElement('script');
    s.src = url;
    s.onload  = resolve;
    s.onerror = () => reject(new Error(`Falha ao carregar: ${url}`));
    document.head.appendChild(s);
  });
}

/**
 * Extrai cabeçalhos e linhas de um <table> do DOM.
 * Retorna { headers: string[], rows: string[][] }
 */
function _parseTable(tableEl) {
  if (!(tableEl instanceof HTMLElement)) {
    throw new Error('tableEl deve ser um elemento HTML <table>.');
  }

  const allRows = Array.from(tableEl.querySelectorAll('tr'));
  if (allRows.length === 0) throw new Error('A tabela está vazia.');

  // Primeira linha com <th> = cabeçalho; resto = dados
  const headerRow = allRows.find(r => r.querySelector('th'));
  const dataRows  = allRows.filter(r => !r.querySelector('th') && r.cells.length > 0);

  const headers = headerRow
    ? Array.from(headerRow.querySelectorAll('th')).map(th => th.innerText.trim())
    : [];

  const rows = dataRows.map(r =>
    Array.from(r.querySelectorAll('td')).map(td => td.innerText.trim())
  );

  return { headers, rows };
}

/**
 * Dispara o download de um Blob no navegador.
 */
function _download(blob, filename) {
  const url  = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href     = url;
  link.download = filename;
  link.click();
  // Libera memória após o clique
  setTimeout(() => URL.revokeObjectURL(url), 10_000);
}

/**
 * Retorna o timestamp atual formatado para uso em nomes de arquivo.
 * Ex: "2025-07-14_1432"
 */
function _timestamp() {
  const d = new Date();
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}_${pad(d.getHours())}${pad(d.getMinutes())}`;
}


// ─────────────────────────────────────────────
// CSV
// ─────────────────────────────────────────────

/**
 * Exporta uma <table> para CSV.
 * @param {HTMLElement} tableEl
 * @param {string} [filename]
 */
function exportCSV(tableEl, filename) {
  const { headers, rows } = _parseTable(tableEl);
  const escape = v => `"${v.replace(/"/g, '""')}"`;

  const linhas = [];
  if (headers.length) linhas.push(headers.map(escape).join(','));
  rows.forEach(r => linhas.push(r.map(escape).join(',')));

  // BOM UTF-8 garante acentos corretos ao abrir no Excel
  const csv  = '\uFEFF' + linhas.join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  _download(blob, filename ?? `tabela_${_timestamp()}.csv`);
}


// ─────────────────────────────────────────────
// EXCEL (.xlsx)
// ─────────────────────────────────────────────

/**
 * Exporta uma <table> para .xlsx usando a lib SheetJS.
 * @param {HTMLElement} tableEl
 * @param {string} [filename]
 * @param {string} [sheetName]
 */
async function exportXLSX(tableEl, filename, sheetName = 'Tabela') {
  await _loadScript('https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js');

  const { headers, rows } = _parseTable(tableEl);
  const XLSX = window.XLSX;

  // Monta array de arrays: [cabeçalho, ...linhas]
  const data = headers.length ? [headers, ...rows] : rows;

  const ws = XLSX.utils.aoa_to_sheet(data);

  // Largura automática por coluna
  const colWidths = data[0]?.map((_, ci) =>
    ({ wch: Math.max(...data.map(r => (r[ci] ?? '').length)) + 2 })
  ) ?? [];
  ws['!cols'] = colWidths;

  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, sheetName);

  const buf  = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
  const blob = new Blob([buf], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
  _download(blob, filename ?? `tabela_${_timestamp()}.xlsx`);
}


// ─────────────────────────────────────────────
// PDF
// ─────────────────────────────────────────────

/**
 * Exporta uma <table> para PDF usando jsPDF + AutoTable.
 * @param {HTMLElement} tableEl
 * @param {string} [filename]
 * @param {string} [titulo]       Título exibido no topo do PDF
 */
async function exportPDF(tableEl, filename, titulo = 'Relatório') {
  await _loadScript('https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js');
  await _loadScript('https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.8.2/jspdf.plugin.autotable.min.js');

  const { headers, rows } = _parseTable(tableEl);
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' });

  // Cabeçalho do documento
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(13);
  doc.text(titulo, 14, 16);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8);
  doc.setTextColor(150);
  doc.text(`Gerado em ${new Date().toLocaleString('pt-BR')}`, 14, 22);
  doc.setTextColor(0);

  doc.autoTable({
    head:       headers.length ? [headers] : undefined,
    body:       rows,
    startY:     28,
    styles:     { fontSize: 9, cellPadding: 3 },
    headStyles: { fillColor: [20, 20, 20], textColor: 255, fontStyle: 'bold' },
    alternateRowStyles: { fillColor: [245, 245, 245] },
    margin: { left: 14, right: 14 },
  });

  // Rodapé com número de página
  const pageCount = doc.internal.getNumberOfPages();
  for (let i = 1; i <= pageCount; i++) {
    doc.setPage(i);
    doc.setFontSize(8);
    doc.setTextColor(150);
    doc.text(
      `Página ${i} de ${pageCount}`,
      doc.internal.pageSize.getWidth() - 14,
      doc.internal.pageSize.getHeight() - 8,
      { align: 'right' }
    );
  }

  doc.save(filename ?? `tabela_${_timestamp()}.pdf`);
}


// ─────────────────────────────────────────────
// EXPORTAÇÃO PÚBLICA
// ─────────────────────────────────────────────
window.exportCSV  = exportCSV;
window.exportXLSX = exportXLSX;
window.exportPDF  = exportPDF;