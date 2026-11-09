"""Persistência em SQLite: cada envio é uma nova linha (trilha de auditoria); a visão `declaracoes_atuais` traz a versão vigente."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path

DDL = """
CREATE TABLE IF NOT EXISTS declaracoes (
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  protocolo TEXT UNIQUE NOT NULL,
  declaracao_id TEXT NOT NULL,
  versao INTEGER NOT NULL,
  chave_declarante TEXT NOT NULL,          -- login institucional ou, sem login, a matrícula SIAPE
  matricula_siape TEXT NOT NULL,
  enviado_em TEXT NOT NULL,
  hash_sha256 TEXT NOT NULL,               -- hash do JSON canônico, impresso no espelho
  chave_acesso_hash TEXT NOT NULL,         -- hash da chave que dá acesso ao espelho
  payload TEXT NOT NULL,
  UNIQUE (declaracao_id, versao)
);
CREATE INDEX IF NOT EXISTS ix_decl_chave ON declaracoes (chave_declarante);
CREATE INDEX IF NOT EXISTS ix_decl_enviado ON declaracoes (enviado_em);
CREATE VIEW IF NOT EXISTS declaracoes_atuais AS
  SELECT d.* FROM declaracoes d
  JOIN (SELECT declaracao_id, MAX(versao) v FROM declaracoes GROUP BY declaracao_id) m
    ON m.declaracao_id = d.declaracao_id AND m.v = d.versao;
"""


def json_canonico(doc: dict) -> str:
    return json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


class Store:
    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with closing(self._conn()) as c, c:
            c.executescript(DDL)

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        return c

    def ultima(self, chave_declarante: str) -> sqlite3.Row | None:
        with closing(self._conn()) as c:
            return c.execute(
                "SELECT * FROM declaracoes WHERE chave_declarante=? ORDER BY versao DESC LIMIT 1", (chave_declarante,)
            ).fetchone()

    def inserir(self, *, protocolo: str, doc: dict, chave_declarante: str, chave_acesso: str) -> str:
        texto = json_canonico(doc)
        h = sha256(texto)
        with closing(self._conn()) as c, c:
            c.execute(
                "INSERT INTO declaracoes (protocolo, declaracao_id, versao, chave_declarante, matricula_siape, enviado_em, hash_sha256, chave_acesso_hash, payload)"
                " VALUES (?,?,?,?,?,?,?,?,?)",
                (protocolo, doc["declaracao_id"], doc["versao"], chave_declarante, doc["identificacao"]["matricula_siape"],
                 doc["enviado_em"], h, sha256(chave_acesso), texto),
            )
        return h

    def por_protocolo(self, protocolo: str) -> sqlite3.Row | None:
        with closing(self._conn()) as c:
            return c.execute("SELECT * FROM declaracoes WHERE protocolo=?", (protocolo,)).fetchone()

    def listar(self, *, desde: str | None = None, siape: str | None = None, historico: bool = False) -> list[sqlite3.Row]:
        sql = f"SELECT * FROM {'declaracoes' if historico else 'declaracoes_atuais'} WHERE 1=1"
        args: list = []
        if desde:
            sql += " AND enviado_em >= ?"
            args.append(desde)
        if siape:
            sql += " AND matricula_siape = ?"
            args.append(siape)
        with closing(self._conn()) as c:
            return c.execute(sql + " ORDER BY enviado_em, seq", args).fetchall()


def documento(row: sqlite3.Row) -> dict:
    return {"protocolo": row["protocolo"], **json.loads(row["payload"])}
