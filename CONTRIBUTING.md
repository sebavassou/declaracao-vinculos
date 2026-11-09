# Como contribuir

1. Abra uma *issue* descrevendo a necessidade (use os modelos). Não inclua dados pessoais reais.
2. Crie um *branch* a partir de `main`, faça a alteração e rode `ruff check app tests` e `pytest`.
3. Abra um *pull request* preenchendo o modelo. A CI precisa passar.

## Regras do projeto

- **Duas implementações das regras de triagem**: `app/rules.py` (servidor) e o JavaScript de `app/static/formulario.html` (prévia no navegador). Alterou uma, altere a outra e o teste correspondente. O servidor sempre recalcula e prevalece.
- **Esquema de dados**: toda mudança em `schema/` atualiza o dicionário de dados, o exemplo e o CHANGELOG. Campo novo opcional = versão MINOR; remoção, renomeação ou mudança de tipo = versão MAJOR.
- **Textos legais**: indique norma e dispositivo no PR. Não cite número de norma, acórdão ou nota técnica sem conferir a fonte oficial.
- **Identidade da unidade**: nada específico de um órgão no código; use as variáveis `DV_*` (ver `docs/replicacao.md`).
- **Mensagens de commit**: em português, no imperativo ("Adiciona…", "Corrige…").

## Lançando uma versão

1. Atualize `app/__init__.py`, `pyproject.toml` e o CHANGELOG.
2. Crie a tag `vX.Y.Z` em `main`. O workflow *Release* publica a imagem em `ghcr.io` e cria a release.
