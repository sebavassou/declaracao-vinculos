# API

Documentação interativa (OpenAPI) em `/docs` de cada instalação.

## Autenticação
- **Declarante**: login institucional via proxy (`DV_AUTH_MODE=proxy`) ou acesso pela rede interna (`none`).
- **Integração**: `Authorization: Bearer <DV_API_TOKEN>` em todas as rotas `/api/v1/integracao/*`.

## Rotas

| Método e rota | Acesso | Descrição |
|---|---|---|
| `GET /` | declarante | Formulário |
| `GET /api/v1/sessao` | declarante | Usuário autenticado (nome e e-mail para pré-preenchimento) |
| `GET /api/v1/minha-declaracao` | declarante com login | Última versão enviada (retificação) |
| `POST /api/v1/declaracoes` | declarante | Envia declaração. `201` com protocolo, versão, hash e links do espelho; `422` com lista de erros |
| `GET /api/v1/espelho/{protocolo}.pdf` · `.html` | declarante (login ou `?chave=`), `DV_ADMINS`, token | Espelho para o SEI |
| `GET /api/v1/verificar/{protocolo}?codigo=<sha256>` | público | Confere autenticidade do espelho |
| `GET /api/v1/integracao/declaracoes` | token | Lista versões vigentes. Parâmetros: `desde` (ISO 8601), `siape`, `historico=true`, `limit`, `offset` |
| `GET /api/v1/integracao/declaracoes/{declaracao_id}` | token | Versão vigente de uma declaração |
| `GET /api/v1/integracao/export/declaracoes.csv` | token | Uma linha por declarante, com indicadores (`;`, UTF-8 com BOM) |
| `GET /api/v1/integracao/export/vinculos.csv` | token | Uma linha por vínculo |
| `GET /api/v1/integracao/indicadores` | token | Contagens agregadas para painel |
| `GET /api/v1/schema` | público | JSON Schema vigente |
| `GET /saude` | público | Verificação de funcionamento |

Colunas dos CSV: [schema/dicionario_dados.csv](../schema/dicionario_dados.csv).

## Exemplos

### Python (pandas), carga completa e incremental
```python
import io, os, requests, pandas as pd
from dotenv import load_dotenv

load_dotenv()
BASE = os.environ["DV_API_URL"]              # ex.: https://formulario.orgao.gov.br/api/v1
H = {"Authorization": f"Bearer {os.environ['DV_API_TOKEN']}"}

def csv(nome):
    r = requests.get(f"{BASE}/integracao/export/{nome}.csv", headers=H, timeout=60)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.content.decode("utf-8-sig")), sep=";", dtype={"matricula_siape": str, "cpf": str})

declaracoes, vinculos = csv("declaracoes"), csv("vinculos")

# job incremental: só o que chegou desde a última execução
novos = requests.get(f"{BASE}/integracao/declaracoes", params={"desde": "2026-11-08T00:00:00+00:00"}, headers=H, timeout=60).json()["itens"]
```

### Power BI
*Obter dados → Web → Avançado*: URL `.../api/v1/integracao/export/declaracoes.csv`, cabeçalho `Authorization` = `Bearer <token>`. Repita para `vinculos.csv` e relacione `declaracao_id` (1:N). Não publique CPF nem valores individuais em painéis abertos.

### curl
```bash
curl -H "Authorization: Bearer $DV_API_TOKEN" "$DV_API_URL/integracao/indicadores"
curl -X POST -H "Content-Type: application/json" --data @examples/exemplo_declaracao.json http://127.0.0.1:8000/api/v1/declaracoes
```
