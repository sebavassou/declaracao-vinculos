import copy
import json
from pathlib import Path

import pytest

EXEMPLO = json.loads((Path(__file__).parent.parent / "examples" / "exemplo_declaracao.json").read_text(encoding="utf-8"))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DV_DB_PATH", str(tmp_path / "t.sqlite3"))
    monkeypatch.setenv("DV_API_TOKEN", "segredo")
    monkeypatch.setenv("DV_AUTH_MODE", "none")
    return _carregar()


def _carregar():
    import importlib

    import app.auth
    import app.config
    import app.espelho
    import app.main

    for m in (app.config, app.auth, app.espelho, app.main):
        importlib.reload(m)
    from fastapi.testclient import TestClient

    return TestClient(app.main.app)


H = {"Authorization": "Bearer segredo"}


def test_envio_retificacao_e_consulta(client):
    r = client.post("/api/v1/declaracoes", json=EXEMPLO)
    assert r.status_code == 201
    d = r.json()
    assert d["versao"] == 1 and d["indicadores"]["carga_semanal_efetiva_total"] == 64 and d["indicadores"]["acima_60h_semanais"]
    r2 = client.post("/api/v1/declaracoes", json=EXEMPLO).json()
    assert r2["versao"] == 2 and r2["declaracao_id"] == d["declaracao_id"]
    assert client.get("/api/v1/integracao/declaracoes", headers=H).json()["total"] == 1
    assert client.get("/api/v1/integracao/declaracoes?historico=true", headers=H).json()["total"] == 2
    csv_v = client.get("/api/v1/integracao/export/vinculos.csv", headers=H).text
    assert csv_v.splitlines()[0].lstrip("﻿").startswith("declaracao_id;matricula_siape") and len(csv_v.splitlines()) == 3


def test_leitura_exige_token(client):
    assert client.get("/api/v1/integracao/declaracoes").status_code == 401
    assert client.get("/api/v1/integracao/indicadores", headers={"Authorization": "Bearer errado"}).status_code == 401


def test_rejeita_cpf_invalido(client):
    ruim = copy.deepcopy(EXEMPLO)
    ruim["identificacao"]["cpf"] = "12345678900"
    r = client.post("/api/v1/declaracoes", json=ruim)
    assert r.status_code == 422 and "cpf" in json.dumps(r.json())


def test_rejeita_sem_aceite(client):
    ruim = copy.deepcopy(EXEMPLO)
    ruim["manifestacao"]["declara_veracidade"] = False
    assert client.post("/api/v1/declaracoes", json=ruim).status_code == 422


def test_espelho_pdf_html_e_verificacao(client):
    d = client.post("/api/v1/declaracoes", json=EXEMPLO).json()
    pdf = client.get(d["links"]["espelho_pdf"])
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"
    html = client.get(d["links"]["espelho_html"]).text
    assert d["protocolo"] in html and "Médico plantonista" in html
    assert client.get(f"/api/v1/espelho/{d['protocolo']}.pdf").status_code == 404  # sem chave
    assert client.get(f"/api/v1/espelho/{d['protocolo']}.pdf?chave=errada").status_code == 404
    v = client.get(f"/api/v1/verificar/{d['protocolo']}", params={"codigo": d["hash_sha256"]}).json()
    assert v["autentico"] is True
    assert client.get(f"/api/v1/verificar/{d['protocolo']}", params={"codigo": "0" * 64}).json()["autentico"] is False


def test_formulario_injeta_configuracao(client):
    html = client.get("/").text
    assert 'window.DV_BACKEND="api"' in html and "window.DV_CONFIG=" in html


def test_modo_proxy(tmp_path, monkeypatch):
    monkeypatch.setenv("DV_DB_PATH", str(tmp_path / "p.sqlite3"))
    monkeypatch.setenv("DV_AUTH_MODE", "proxy")
    monkeypatch.setenv("DV_ADMINS", "chefe.coape")
    monkeypatch.setenv("DV_API_TOKEN", "")
    c = _carregar()
    assert c.get("/").status_code == 401
    assert c.post("/api/v1/declaracoes", json=EXEMPLO).status_code == 401
    eu = {"X-Remote-User": "maria.silva", "X-Remote-Name": "Maria Silva"}
    d = c.post("/api/v1/declaracoes", json=EXEMPLO, headers=eu).json()
    assert d["declarante_login"] == "maria.silva"
    assert c.get("/api/v1/sessao", headers=eu).json()["autenticado"] is True
    assert c.get("/api/v1/minha-declaracao", headers=eu).json()["protocolo"] == d["protocolo"]
    assert c.get(f"/api/v1/espelho/{d['protocolo']}.pdf", headers=eu).status_code == 200
    assert c.get(f"/api/v1/espelho/{d['protocolo']}.pdf", headers={"X-Remote-User": "outra.pessoa"}).status_code == 404
    assert c.get(f"/api/v1/espelho/{d['protocolo']}.pdf", headers={"X-Remote-User": "chefe.coape"}).status_code == 200
    assert c.get("/api/v1/integracao/declaracoes", headers={"X-Remote-User": "chefe.coape"}).status_code == 401  # integração só por token
