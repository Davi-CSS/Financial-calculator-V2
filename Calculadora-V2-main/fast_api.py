"""
fast_api.py — Calculadora Financeira v2
Rodar: uvicorn fast_api:app --reload
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
import math

# ─────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────
app = FastAPI(title="Calculadora Financeira", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Em produção: liste apenas as origens permitidas
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve o frontend (index.html, app.js, export.js) em "/"
# Descomente quando o frontend estiver na pasta ./static
# app.mount("/", StaticFiles(directory="static", html=True), name="static")


# ─────────────────────────────────────────────
# SCHEMAS (Pydantic v2)
# ─────────────────────────────────────────────
class PriceRequest(BaseModel):
    capital:    float
    taxa_mensal: float
    parcelas:   int

    @field_validator("capital")
    @classmethod
    def capital_positivo(cls, v):
        if v <= 0:
            raise ValueError("capital deve ser maior que zero")
        return v

    @field_validator("taxa_mensal")
    @classmethod
    def taxa_nao_negativa(cls, v):
        if v < 0:
            raise ValueError("taxa_mensal não pode ser negativa")
        return v

    @field_validator("parcelas")
    @classmethod
    def parcelas_positivas(cls, v):
        if v <= 0:
            raise ValueError("parcelas deve ser maior que zero")
        return v


class SACRequest(BaseModel):
    capital:    float
    taxa_mensal: float
    periodos:   int

    @field_validator("capital")
    @classmethod
    def capital_positivo(cls, v):
        if v <= 0:
            raise ValueError("capital deve ser maior que zero")
        return v

    @field_validator("taxa_mensal")
    @classmethod
    def taxa_nao_negativa(cls, v):
        if v < 0:
            raise ValueError("taxa_mensal não pode ser negativa")
        return v

    @field_validator("periodos")
    @classmethod
    def periodos_positivos(cls, v):
        if v <= 0:
            raise ValueError("periodos deve ser maior que zero")
        return v


class JurosRequest(BaseModel):
    capital:  float
    taxa:     float
    periodos: int

    @field_validator("capital")
    @classmethod
    def capital_positivo(cls, v):
        if v <= 0:
            raise ValueError("capital deve ser maior que zero")
        return v

    @field_validator("periodos")
    @classmethod
    def periodos_positivos(cls, v):
        if v <= 0:
            raise ValueError("periodos deve ser maior que zero")
        return v


# ─────────────────────────────────────────────
# ROTAS
# ─────────────────────────────────────────────
@app.get("/health")
def health():
    """Verificação rápida de que a API está no ar."""
    return {"status": "ok"}


@app.post("/api/price")
def price(req: PriceRequest):
    """
    Tabela Price — parcelas fixas, amortização crescente.
    Retorna campos normalizados: parcela, prestacao, juros, amortizacao, saldo_devedor.
    """
    capital = req.capital
    taxa    = req.taxa_mensal
    n       = req.parcelas

    # Taxa zero → divisão simples
    if taxa == 0:
        pmt = capital / n
    else:
        fator = (1 + taxa) ** n
        pmt   = capital * (taxa * fator) / (fator - 1)

    saldo = capital
    table = []

    for i in range(1, n + 1):
        juros = saldo * taxa
        amort = pmt - juros

        # Última parcela: zera o resíduo de arredondamento
        if i == n:
            amort = saldo
            pmt_i = amort + juros   # pode diferir levemente das anteriores
        else:
            pmt_i = pmt

        saldo = max(0.0, saldo - amort)

        table.append({
            "parcela":       i,
            "prestacao":     round(pmt_i, 2),
            "juros":         round(juros,  2),
            "amortizacao":   round(amort,  2),
            "saldo_devedor": round(saldo,  2),
        })

    return {"table": table, "origem": "backend"}


@app.post("/api/sac")
def sac(req: SACRequest):
    """
    Sistema SAC — amortização constante, prestações decrescentes.
    Retorna campos normalizados: parcela, prestacao, juros, amortizacao, saldo_devedor.
    """
    capital  = req.capital
    taxa     = req.taxa_mensal
    n        = req.periodos
    amort    = capital / n
    saldo    = capital
    table    = []

    for p in range(1, n + 1):
        juros = saldo * taxa

        # Última parcela: garante saldo zero
        amort_p = saldo if p == n else amort
        pmt     = amort_p + juros
        saldo   = max(0.0, saldo - amort_p)

        table.append({
            "parcela":       p,
            "prestacao":     round(pmt,     2),
            "juros":         round(juros,   2),
            "amortizacao":   round(amort_p, 2),
            "saldo_devedor": round(saldo,   2),
        })

    return {"table": table, "origem": "backend"}


@app.post("/api/juros")
def juros_compostos(req: JurosRequest):
    """
    Juros compostos — retorna montante acumulado período a período.
    Inclui também total de juros pagos e taxa efetiva anual.
    """
    capital  = req.capital
    taxa     = req.taxa
    n        = req.periodos

    montantes = []
    for p in range(1, n + 1):
        montante = capital * ((1 + taxa) ** p)
        montantes.append({
            "periodo":  p,
            "montante": round(montante, 2),
            "juros":    round(montante - capital, 2),
        })

    montante_final  = capital * ((1 + taxa) ** n)
    taxa_efetiva_aa = round(((1 + taxa) ** 12 - 1) * 100, 4)  # assume taxa mensal

    return {
        "montantes":       montantes,
        "montante_final":  round(montante_final, 2),
        "total_juros":     round(montante_final - capital, 2),
        "taxa_efetiva_aa": taxa_efetiva_aa,
    }