"""
flask_app.py — Calculadora Financeira v2
Rodar: python flask_app.py   (dev)
       flask run              (prod com gunicorn na frente)
"""

from flask import Flask, request, jsonify, make_response
from functools import wraps

app = Flask(__name__)


# ─────────────────────────────────────────────
# UTILITÁRIOS
# ─────────────────────────────────────────────

def json_error(mensagem: str, code: int = 400):
    """Atalho para respostas de erro padronizadas."""
    return make_response(jsonify({"erro": mensagem}), code)


def parse_json_body(*campos):
    """
    Extrai e converte campos do body JSON.
    `campos` é uma lista de tuplas (nome, tipo).
    Retorna (dict, None) em sucesso ou (None, resposta_erro) em falha.
    """
    data = request.get_json(silent=True) or {}
    parsed = {}
    for nome, tipo in campos:
        valor = data.get(nome)
        if valor is None:
            return None, json_error(f"Campo obrigatório ausente: '{nome}'")
        try:
            parsed[nome] = tipo(valor)
        except (TypeError, ValueError):
            return None, json_error(f"Valor inválido para '{nome}': esperado {tipo.__name__}")
    return parsed, None


def validar_positivo(valor, nome, permite_zero=False):
    """Retorna mensagem de erro ou None se válido."""
    if permite_zero and valor < 0:
        return f"'{nome}' não pode ser negativo"
    if not permite_zero and valor <= 0:
        return f"'{nome}' deve ser maior que zero"
    return None


# ─────────────────────────────────────────────
# LÓGICA DE CÁLCULO (separada das rotas)
# ─────────────────────────────────────────────

def calcular_price(capital: float, taxa_mensal: float, parcelas: int) -> list:
    """
    Tabela Price — parcelas fixas, amortização crescente.
    Campos retornados: parcela, prestacao, juros, amortizacao, saldo_devedor.
    """
    if taxa_mensal == 0:
        pmt = capital / parcelas
    else:
        fator = (1 + taxa_mensal) ** parcelas
        pmt   = capital * (taxa_mensal * fator) / (fator - 1)

    saldo  = capital
    tabela = []

    for i in range(1, parcelas + 1):
        juros = saldo * taxa_mensal
        amort = pmt - juros

        # Última parcela: zera resíduo de arredondamento
        if i == parcelas:
            amort = saldo
            pmt_i = amort + juros
        else:
            pmt_i = pmt

        saldo = max(0.0, saldo - amort)

        tabela.append({
            "parcela":       i,
            "prestacao":     round(pmt_i, 2),
            "juros":         round(juros,  2),
            "amortizacao":   round(amort,  2),
            "saldo_devedor": round(saldo,  2),
        })

    return tabela


def calcular_sac(capital: float, taxa_mensal: float, periodos: int) -> list:
    """
    Sistema SAC — amortização constante, prestações decrescentes.
    Campos retornados: parcela, prestacao, juros, amortizacao, saldo_devedor.

    CORREÇÃO: campo era 'principal'/'periods' no original — agora usa
    'capital'/'periodos', consistente com o frontend e com /api/price.
    """
    amort_fixo = capital / periodos
    saldo      = capital
    tabela     = []

    for p in range(1, periodos + 1):
        juros = saldo * taxa_mensal

        # Última parcela: garante saldo zero
        amort = saldo if p == periodos else amort_fixo
        pmt   = amort + juros
        saldo = max(0.0, saldo - amort)

        tabela.append({
            "parcela":       p,
            "prestacao":     round(pmt,   2),
            "juros":         round(juros, 2),
            "amortizacao":   round(amort, 2),
            "saldo_devedor": round(saldo, 2),
        })

    return tabela


def calcular_juros(capital: float, taxa: float, periodos: int) -> dict:
    """
    Juros compostos — montante acumulado período a período.
    Inclui resumo com total de juros e taxa efetiva anual.
    """
    montantes = []
    for p in range(1, periodos + 1):
        montante = capital * ((1 + taxa) ** p)
        montantes.append({
            "periodo":  p,
            "montante": round(montante, 2),
            "juros":    round(montante - capital, 2),
        })

    montante_final = capital * ((1 + taxa) ** periodos)

    return {
        "montantes":       montantes,
        "montante_final":  round(montante_final, 2),
        "total_juros":     round(montante_final - capital, 2),
        "taxa_efetiva_aa": round(((1 + taxa) ** 12 - 1) * 100, 4),  # assume taxa mensal
    }


# ─────────────────────────────────────────────
# ROTAS
# ─────────────────────────────────────────────

@app.get("/health")
def health():
    """Verificação rápida de disponibilidade da API."""
    return jsonify({"status": "ok"})


@app.post("/api/price")
def api_price():
    dados, erro = parse_json_body(
        ("capital",     float),
        ("taxa_mensal", float),
        ("parcelas",    int),
    )
    if erro:
        return erro

    for campo, permite_zero in [("capital", False), ("taxa_mensal", True), ("parcelas", False)]:
        msg = validar_positivo(dados[campo], campo, permite_zero=(campo == "taxa_mensal"))
        if msg:
            return json_error(msg)

    tabela = calcular_price(dados["capital"], dados["taxa_mensal"], dados["parcelas"])
    return jsonify({"table": tabela, "origem": "backend"})


@app.post("/api/sac")
def api_sac():
    """
    CORREÇÃO: o original recebia 'principal' e 'periods'.
    Agora usa 'capital' e 'periodos' — igual ao /api/price e ao frontend.
    """
    dados, erro = parse_json_body(
        ("capital",     float),
        ("taxa_mensal", float),
        ("periodos",    int),
    )
    if erro:
        return erro

    for campo in ["capital", "periodos"]:
        msg = validar_positivo(dados[campo], campo)
        if msg:
            return json_error(msg)
    msg = validar_positivo(dados["taxa_mensal"], "taxa_mensal", permite_zero=True)
    if msg:
        return json_error(msg)

    tabela = calcular_sac(dados["capital"], dados["taxa_mensal"], dados["periodos"])
    return jsonify({"table": tabela, "origem": "backend"})


@app.post("/api/juros")
def api_juros():
    dados, erro = parse_json_body(
        ("capital",  float),
        ("taxa",     float),
        ("periodos", int),
    )
    if erro:
        return erro

    for campo in ["capital", "periodos"]:
        msg = validar_positivo(dados[campo], campo)
        if msg:
            return json_error(msg)

    resultado = calcular_juros(dados["capital"], dados["taxa"], dados["periodos"])
    return jsonify(resultado)


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # debug=True apenas em desenvolvimento — nunca em produção
    app.run(debug=True, port=5000)