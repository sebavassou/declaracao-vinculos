"""Configuração por variáveis de ambiente (arquivo .env aceito)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent


def _lista(nome: str) -> list[str]:
    return [x.strip() for x in os.getenv(nome, "").split(",") if x.strip()]


@dataclass(frozen=True)
class Settings:
    # Armazenamento e esquema
    db_path: str = os.getenv("DV_DB_PATH", str(ROOT / "dados" / "declaracoes.sqlite3"))
    schema_path: Path = Path(os.getenv("DV_SCHEMA_PATH", ROOT / "schema" / "declaracao_vinculos.schema.json"))
    # Leitura por pipelines/dashboards
    api_token: str = os.getenv("DV_API_TOKEN", "")
    cors_origins: list[str] = field(default_factory=lambda: _lista("DV_CORS_ORIGINS"))
    # Autenticação: "none" (rede interna) ou "proxy" (login institucional feito pelo proxy reverso)
    auth_mode: str = os.getenv("DV_AUTH_MODE", "none").lower()
    header_user: str = os.getenv("DV_AUTH_HEADER_USER", "X-Remote-User")
    header_name: str = os.getenv("DV_AUTH_HEADER_NAME", "X-Remote-Name")
    header_email: str = os.getenv("DV_AUTH_HEADER_EMAIL", "X-Remote-Email")
    admins: list[str] = field(default_factory=lambda: [a.lower() for a in _lista("DV_ADMINS")])
    # Identidade da unidade (textos do formulário e do espelho em PDF)
    cabecalho_1: str = os.getenv("DV_CABECALHO_1", "Ministério da Saúde · Secretaria de Atenção Especializada à Saúde")
    cabecalho_2: str = os.getenv("DV_CABECALHO_2", "Instituto Nacional de Traumatologia e Ortopedia · Coordenação de Administração de Pessoas")
    orgao_sigla: str = os.getenv("DV_ORGAO_SIGLA", "INTO")
    orgao_titulo: str = os.getenv("DV_ORGAO_TITULO", "INTO – Instituto Nacional de Traumatologia e Ortopedia")
    orgao_nome: str = os.getenv("DV_ORGAO_NOME", "Instituto Nacional de Traumatologia e Ortopedia (INTO/MS)")
    unidade_gp: str = os.getenv("DV_UNIDADE_GP", "COAPE/INTO")
    cidade_uf: str = os.getenv("DV_CIDADE_UF", "Rio de Janeiro/RJ")

    def config_publica(self) -> dict:
        """Textos enviados ao navegador (nada sensível)."""
        return {k: getattr(self, k) for k in ("cabecalho_1", "cabecalho_2", "orgao_sigla", "orgao_titulo", "orgao_nome", "unidade_gp", "cidade_uf")}


settings = Settings()
