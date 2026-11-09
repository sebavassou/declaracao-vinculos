"""API e formulário web da Declaração de Vínculos.

Execução: uvicorn app.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import csv
import io
import json
import secrets
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from jsonschema import Draft202012Validator, FormatChecker

from . import __version__, espelho, rules
from .auth import Usuario, exigir_leitura, exigir_usuario, token_valido, usuario
from .config import settings
from .storage import Store, documento, sha256

SCHEMA = json.loads(settings.schema_path.read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
FORM = Path(__file__).parent / "static" / "formulario.html"
store = Store(settings.db_path)

app = FastAPI(
    title="Declaração de Vínculos",
    version=__version__,
    description="Formulário eletrônico e API da Declaração de Vínculos (IN SGP/MGI nº 30/2025). "
    "Rotas de consulta em lote exigem token Bearer. Os dados são pessoais: tratar conforme a LGPD.",
)
if settings.cors_origins:
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["GET", "POST"], allow_headers=["*"])


@app.middleware("http")
async def cabecalhos_seguranca(request: Request, call_next):
    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    resp.headers.setdefault("Cache-Control", "no-store")
    return resp


def _links(protocolo: str, chave: str | None) -> dict:
    q = f"?chave={chave}" if chave else ""
    return {"espelho_pdf": f"/api/v1/espelho/{protocolo}.pdf{q}", "espelho_html": f"/api/v1/espelho/{protocolo}.html{q}"}


# ---------- Formulário ----------
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def formulario(request: Request):
    exigir_usuario(request)
    cfg = json.dumps(settings.config_publica(), ensure_ascii=False).replace("</", "<\\/")
    return (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        f'<script>window.DV_BACKEND="api";window.DV_API_BASE="/api/v1";window.DV_CONFIG={cfg};</script>'
        "</head><body>" + FORM.read_text(encoding="utf-8") + "</body></html>"
    )


@app.get("/saude", include_in_schema=False)
def saude():
    return {"status": "ok", "versao": __version__, "schema": SCHEMA.get("$id")}


# ---------- Sessão do declarante ----------
@app.get("/api/v1/sessao", tags=["declarante"])
def sessao(request: Request):
    u = usuario(request)
    return {"modo": settings.auth_mode, "autenticado": bool(u), "login": u.login if u else None,
            "nome": u.nome if u else None, "email": u.email if u else None, "admin": bool(u and u.admin)}


@app.get("/api/v1/minha-declaracao", tags=["declarante"])
def minha_declaracao(u: Usuario | None = Depends(exigir_usuario)):
    """Última versão enviada pelo usuário autenticado (para retificação). Só existe em DV_AUTH_MODE=proxy."""
    if not u:
        raise HTTPException(404, "Disponível apenas com login institucional.")
    row = store.ultima(u.login)
    if not row:
        raise HTTPException(404, "Nenhuma declaração enviada.")
    # nova chave de acesso não é emitida aqui: o usuário autenticado acessa o espelho pelo login
    return {**documento(row), "links": _links(row["protocolo"], None)}


# ---------- Ingestão ----------
@app.post("/api/v1/declaracoes", status_code=201, tags=["ingestão"])
def receber(doc: dict, u: Usuario | None = Depends(exigir_usuario)):
    for k in ("historico", "protocolo", "links", "declarante_uid"):
        doc.pop(k, None)
    erros = [f"{'/'.join(map(str, e.absolute_path)) or '(raiz)'}: {e.message}" for e in VALIDATOR.iter_errors(doc)]
    if not erros:
        erros = rules.validar_regras(doc)
    if erros:
        raise HTTPException(422, {"erros": erros[:50]})

    chave_declarante = u.login if u else doc["identificacao"]["matricula_siape"]
    anterior = store.ultima(chave_declarante)
    doc["declaracao_id"] = anterior["declaracao_id"] if anterior else str(uuid.uuid4())
    doc["versao"] = (anterior["versao"] if anterior else 0) + 1
    doc["enviado_em"] = datetime.now(UTC).isoformat(timespec="seconds")  # relógio do servidor prevalece
    doc["declarante_login"] = u.login if u else None
    doc["indicadores"] = rules.indicadores(doc)
    protocolo = f"DV-{datetime.now(UTC):%Y%m%d}-{secrets.token_hex(4).upper()}"
    chave_acesso = secrets.token_urlsafe(24)
    h = store.inserir(protocolo=protocolo, doc=doc, chave_declarante=chave_declarante, chave_acesso=chave_acesso)
    return {"protocolo": protocolo, "hash_sha256": h, **doc, "links": _links(protocolo, chave_acesso)}


# ---------- Espelho para o SEI ----------
def _autorizar_espelho(request: Request, protocolo: str, chave: str | None):
    row = store.por_protocolo(protocolo)
    if not row:
        raise HTTPException(404, "Protocolo não encontrado.")
    u = usuario(request)
    if (chave and secrets.compare_digest(sha256(chave), row["chave_acesso_hash"])) or token_valido(request) \
            or (u and (u.admin or u.login == row["chave_declarante"])):
        return row
    raise HTTPException(404, "Protocolo não encontrado.")  # não revela a existência do protocolo


@app.get("/api/v1/espelho/{protocolo}.pdf", tags=["espelho SEI"])
def espelho_pdf(protocolo: str, request: Request, chave: str | None = None):
    row = _autorizar_espelho(request, protocolo, chave)
    pdf = espelho.gerar_pdf(documento(row), row["hash_sha256"], json.loads(row["payload"]).get("declarante_login"))
    return Response(pdf, media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="declaracao_vinculos_{protocolo}.pdf"'})


@app.get("/api/v1/espelho/{protocolo}.html", response_class=HTMLResponse, tags=["espelho SEI"])
def espelho_html(protocolo: str, request: Request, chave: str | None = None):
    row = _autorizar_espelho(request, protocolo, chave)
    return espelho.gerar_html(documento(row), row["hash_sha256"], json.loads(row["payload"]).get("declarante_login"))


@app.get("/api/v1/verificar/{protocolo}", tags=["espelho SEI"])
def verificar(protocolo: str, codigo: str = Query(..., min_length=64, max_length=64)):
    """Confere se um código de verificação impresso no espelho corresponde ao registro. Não devolve dados pessoais."""
    row = store.por_protocolo(protocolo)
    ok = bool(row) and secrets.compare_digest(row["hash_sha256"], codigo.lower())
    return {"protocolo": protocolo, "autentico": ok, **({"versao": row["versao"], "enviado_em": row["enviado_em"]} if ok else {})}


# ---------- Consulta (pipelines e dashboards) ----------
@app.get("/api/v1/integracao/declaracoes", dependencies=[Depends(exigir_leitura)], tags=["consulta"])
def listar(desde: str | None = Query(None, description="ISO 8601; carga incremental pela data de envio"),
           siape: str | None = None, historico: bool = Query(False, description="true = todas as versões"),
           limit: int = Query(500, ge=1, le=5000), offset: int = Query(0, ge=0)):
    dados = [documento(r) for r in store.listar(desde=desde, siape=siape, historico=historico)]
    return {"total": len(dados), "itens": dados[offset: offset + limit]}


@app.get("/api/v1/integracao/declaracoes/{declaracao_id}", dependencies=[Depends(exigir_leitura)], tags=["consulta"])
def obter(declaracao_id: str):
    for r in store.listar():
        if r["declaracao_id"] == declaracao_id:
            return documento(r)
    raise HTTPException(404, "Declaração não encontrada.")


def _csv(linhas: list[dict], colunas: list[str], nome: str) -> Response:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=colunas, delimiter=";", extrasaction="ignore", lineterminator="\r\n")
    w.writeheader()
    w.writerows(linhas)
    return Response("﻿" + buf.getvalue(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="{nome}"'})


@app.get("/api/v1/integracao/export/declaracoes.csv", dependencies=[Depends(exigir_leitura)], tags=["exportação"])
def csv_declaracoes(desde: str | None = None):
    return _csv([rules.linha_declaracao(documento(r)) for r in store.listar(desde=desde)], rules.COLS_DECLARACOES, "declaracoes.csv")


@app.get("/api/v1/integracao/export/vinculos.csv", dependencies=[Depends(exigir_leitura)], tags=["exportação"])
def csv_vinculos(desde: str | None = None):
    return _csv([x for r in store.listar(desde=desde) for x in rules.linhas_vinculos(documento(r))], rules.COLS_VINCULOS, "vinculos.csv")


@app.get("/api/v1/integracao/indicadores", dependencies=[Depends(exigir_leitura)], tags=["consulta"])
def resumo():
    ind = [json.loads(r["payload"]).get("indicadores") or {} for r in store.listar()]
    conta = lambda k: sum(1 for i in ind if i.get(k))
    chaves = ("possui_acumulacao_declarada", "acima_60h_semanais", "recebe_proventos_aposentadoria", "recebe_pensao",
              "dedicacao_exclusiva_com_outro_vinculo", "alerta_gerencia_empresa", "auxilio_alimentacao_multiplo", "teletrabalho_orgao_principal")
    return {"gerado_em": datetime.now(UTC).isoformat(timespec="seconds"), "declaracoes": len(ind),
            "com_outro_vinculo": sum(1 for i in ind if i.get("qtd_outros_vinculos", 0) > 0), **{k: conta(k) for k in chaves}}


@app.get("/api/v1/schema", tags=["metadados"])
def schema():
    return SCHEMA
