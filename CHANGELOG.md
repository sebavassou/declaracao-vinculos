# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versões seguem o [SemVer](https://semver.org/lang/pt-BR/).

## [Não publicado]

## [1.0.0] – 2026-11-09

### Adicionado
- Formulário web com todas as seções do Formulário de Declaração de Vínculos (IN SGP/MGI nº 30/2025), vínculos ilimitados e validações.
- API FastAPI: ingestão com validação por JSON Schema, versionamento por declarante, protocolo e hash SHA-256.
- Espelho da declaração em PDF e HTML para juntada ao SEI e rota pública de verificação de autenticidade.
- Login institucional por proxy reverso (`DV_AUTH_MODE=proxy`), com exemplos para OIDC (oauth2-proxy) e AD/LDAP (Apache).
- Rotas de integração com token: JSON incremental, CSV (`declaracoes`, `vinculos`) e indicadores agregados.
- Configuração da identidade da unidade por variáveis de ambiente.
- Docker, CI (lint, validação do esquema, testes, build) e publicação de imagem por tag.
- Esquema de dados `declaracao_vinculos` 1.0.0 e dicionário de dados.

### Observação
- O piloto publicado no claude.ai (out/2026) usava o esquema provisório `into.coape.declaracao_vinculos`, com `tipo: "INTO"` no vínculo principal. Na versão 1.0.0 o valor passou a `"principal"` para permitir a replicação.
