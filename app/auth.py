"""Autenticação.

- DV_AUTH_MODE=none: formulário aberto (usar só em rede interna).
- DV_AUTH_MODE=proxy: o login institucional (AD/LDAP, Keycloak, ADFS, gov.br via OIDC) é feito por um proxy
  reverso, que repassa o usuário autenticado em cabeçalhos HTTP. A aplicação deve ficar acessível somente
  através desse proxy, que precisa remover esses cabeçalhos quando vierem do cliente.
- Leitura por pipelines: token Bearer (DV_API_TOKEN), independente do modo.
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass

from fastapi import HTTPException, Request

from .config import settings


@dataclass
class Usuario:
    login: str
    nome: str | None = None
    email: str | None = None

    @property
    def admin(self) -> bool:
        return self.login.lower() in settings.admins


def usuario(request: Request) -> Usuario | None:
    if settings.auth_mode != "proxy":
        return None
    login = (request.headers.get(settings.header_user) or "").strip()
    if not login:
        return None
    return Usuario(login=login, nome=request.headers.get(settings.header_name), email=request.headers.get(settings.header_email))


def exigir_usuario(request: Request) -> Usuario | None:
    """Em modo proxy, bloqueia quem chegou sem login; em modo none, devolve None."""
    u = usuario(request)
    if settings.auth_mode == "proxy" and u is None:
        raise HTTPException(401, "Acesso exige login institucional.")
    return u


def token_valido(request: Request) -> bool:
    if not settings.api_token:
        return False
    enviado = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    return bool(enviado) and secrets.compare_digest(enviado, settings.api_token)


def exigir_leitura(request: Request) -> None:
    """Rotas de integração (consulta em lote): somente token Bearer.

    Não se aceita login por cabeçalho aqui porque os proxies deixam /api/v1/integracao/ fora do login
    institucional, e nessas rotas um cabeçalho de identidade poderia ser forjado pelo cliente.
    """
    if token_valido(request):
        return
    raise HTTPException(401, "Token de integração ou login de administrador exigido.", headers={"WWW-Authenticate": "Bearer"})
