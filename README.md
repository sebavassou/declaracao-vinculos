# Declaração de Vínculos

Formulário eletrônico e API para a **Declaração de Vínculos** prevista na [Instrução Normativa SGP/MGI nº 30, de 27 de janeiro de 2025](https://www.gov.br/servidor/pt-br/acesso-a-informacao/gestao-de-pessoas/sistema-de-carreiras/IN30de2025AcumulaoCOMPILADA.pdf) (acumulação de cargos, empregos e funções públicas).

Desenvolvido na Coordenação de Administração de Pessoas (COAPE) do Instituto Nacional de Traumatologia e Ortopedia (INTO/MS) e pensado para ser **replicado por qualquer unidade de gestão de pessoas** do SIPEC: os textos institucionais são configuráveis e o formato dos dados é aberto.

## O que faz

- **Formulário web** com todas as seções do formulário oficial: identificação, finalidade, situações, vínculos (quantos houver), aposentadoria, pensão, participação em empresa, documentos e manifestação.
- **Validação** de CPF, CNPJ, matrícula SIAPE, e-mails e campos condicionais, no navegador e no servidor.
- **Indicadores de triagem** calculados a cada envio (soma de jornadas, mais de 60h semanais, dedicação exclusiva com outro vínculo, aposentadoria com cargo ativo, gerência de empresa, auxílio-alimentação em duplicidade). São apoio à análise, não decisão.
- **Retificação versionada**: cada envio gera nova versão; o histórico completo fica guardado.
- **Espelho em PDF e HTML** com protocolo e código de verificação SHA-256, para juntada ao processo SEI.
- **Login institucional** opcional, feito por proxy reverso (AD/LDAP, Keycloak, ADFS, Entra ID ou gov.br).
- **API para pipelines e dashboards**: JSON com carga incremental, CSV em duas tabelas e indicadores agregados, com token.

## Início rápido

```bash
cp .env.example .env            # ajuste o token e os textos da sua unidade
docker compose up -d --build
# formulário: http://127.0.0.1:8000/   documentação da API: http://127.0.0.1:8000/docs
```

Sem Docker:

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Documentação

| Documento | Conteúdo |
|---|---|
| [docs/arquitetura.md](docs/arquitetura.md) | Componentes, fluxos, modelo de dados e decisões |
| [docs/implantacao.md](docs/implantacao.md) | Instalação em servidor, HTTPS, login institucional, backup |
| [docs/api.md](docs/api.md) | Rotas, autenticação e exemplos de ingestão (pandas, Power BI) |
| [docs/replicacao.md](docs/replicacao.md) | Como adaptar para outra unidade ou órgão |
| [docs/lgpd.md](docs/lgpd.md) | Tratamento de dados pessoais |
| [docs/fase2-sigepe-sougov.md](docs/fase2-sigepe-sougov.md) | Proposta de disponibilização e integração com SIGEPE/SouGov.br |
| [docs/adr/](docs/adr/) | Registros de decisões de arquitetura |
| [schema/](schema/) | JSON Schema e dicionário de dados |

## Estrutura

```
app/                 API FastAPI, regras, armazenamento, autenticação, espelho PDF
app/static/          formulário (HTML único, sem dependências externas além de fontes)
schema/              contrato de dados (JSON Schema) e dicionário de dados
deploy/              exemplos de proxy com login institucional (OIDC e AD/LDAP)
docs/                arquitetura, implantação, API, LGPD, replicação, fase 2
examples/            declaração fictícia para testes
tests/               testes automatizados (pytest)
```

## Versionamento

O projeto segue o [Versionamento Semântico](https://semver.org/lang/pt-BR/). O esquema de dados tem versão própria (`schema_version` em cada documento): mudanças incompatíveis no esquema exigem nova versão MAJOR do esquema e do software. Veja o [CHANGELOG](CHANGELOG.md).

## Licença

[MIT](LICENSE). Contribuições são bem-vindas; veja [CONTRIBUTING.md](CONTRIBUTING.md).

> Os indicadores de triagem não substituem a análise da unidade de gestão de pessoas. Confira sempre a redação vigente das normas citadas no Sigepe Legis.
