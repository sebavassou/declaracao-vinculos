# ADR 0001 – Aplicação única em FastAPI com formulário estático

**Status:** aceita (2026-11-09)

## Contexto
Unidades de gestão de pessoas têm pouca capacidade de TI dedicada. O sistema precisa ser fácil de instalar, auditar e replicar.

## Decisão
Um único serviço Python (FastAPI) serve o formulário (um arquivo HTML sem etapa de build) e a API. Banco SQLite por padrão.

## Consequências
- Instalação com um contêiner ou um comando `uvicorn`; sem Node, sem fila, sem banco externo.
- OpenAPI gerado automaticamente em `/docs`.
- SQLite atende ao volume de uma unidade (milhares de servidores). Para órgãos maiores ou alta disponibilidade, migrar para PostgreSQL (`app/storage.py` concentra o acesso ao banco).
