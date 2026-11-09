# Implantação

Roteiro para a equipe de TI publicar o formulário na intranet ou na internet do órgão.

## 1. Pré-requisitos
- Servidor Linux com Docker (ou Python 3.11+).
- Nome DNS (ex.: `formulario.orgao.gov.br`) e certificado HTTPS.
- Para login: acesso ao AD/LDAP ou a um provedor OIDC (Keycloak, ADFS, Entra ID, gov.br).

## 2. Configuração
```bash
git clone https://github.com/sebavassou/declaracao-vinculos.git
cd declaracao-vinculos
cp .env.example .env
python -c "import secrets;print(secrets.token_urlsafe(32))"   # cole em DV_API_TOKEN
```
Ajuste os textos `DV_CABECALHO_*`, `DV_ORGAO_*`, `DV_UNIDADE_GP` e `DV_CIDADE_UF` (ver [replicacao.md](replicacao.md)).

## 3. Escolha o modo de acesso

| Cenário | Configuração |
|---|---|
| Só intranet, sem login | `DV_AUTH_MODE=none`; `docker compose up -d`; proxy HTTPS apontando para `127.0.0.1:8000`. |
| Login com conta de rede (AD/LDAP) | `DV_AUTH_MODE=proxy`; Apache conforme `deploy/apache-ldap/declaracao-vinculos.conf`. |
| Login OIDC (Keycloak, ADFS, Entra ID, gov.br) | `DV_AUTH_MODE=proxy`; `deploy/oauth2-proxy/docker-compose.yml`. |

Em `DV_AUTH_MODE=proxy`, a aplicação **não** pode ficar exposta diretamente: publique só o proxy. Inclua em `DV_ADMINS` os logins da equipe de GP que podem abrir espelhos de qualquer servidor.

Rotas que devem ficar **fora** do login do proxy: `/saude`, `/api/v1/integracao/*` (token), `/api/v1/verificar/*` e `/api/v1/schema`.

## 4. Verificação
```bash
curl -s https://formulario.orgao.gov.br/saude
curl -s -H "Authorization: Bearer $DV_API_TOKEN" https://formulario.orgao.gov.br/api/v1/integracao/indicadores
```
Envie uma declaração de teste com dados fictícios, baixe o espelho, confira o código em `/api/v1/verificar/{protocolo}?codigo=...` e depois apague o banco de teste.

## 5. Operação
- **Backup**: copie diariamente o volume `/dados` (arquivo `declaracoes.sqlite3`) para armazenamento criptografado. Para cópia consistente com o serviço no ar: `sqlite3 declaracoes.sqlite3 ".backup copia.sqlite3"`.
- **Atualização**: `git pull && docker compose up -d --build` (ou use a imagem `ghcr.io/sebavassou/declaracao-vinculos:<versão>`). Leia o CHANGELOG antes.
- **Logs**: a saída do contêiner registra as requisições; não registre corpos de requisição (contêm dados pessoais).
- **Fuso horário**: a imagem usa `America/Sao_Paulo`; os registros são gravados em UTC.
