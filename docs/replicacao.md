# Replicação em outra unidade ou órgão

O código não tem nada fixo de um órgão. Para adotar:

1. **Faça um fork** (ou use a imagem publicada) e preserve o crédito da licença MIT.
2. **Configure a identidade** no `.env`:

| Variável | Uso | Exemplo |
|---|---|---|
| `DV_CABECALHO_1` | 1ª linha do timbre | `Ministério da Saúde · Secretaria de Atenção Especializada à Saúde` |
| `DV_CABECALHO_2` | 2ª linha do timbre | `Hospital Federal X · Divisão de Gestão de Pessoas` |
| `DV_ORGAO_SIGLA` | Sigla em textos curtos | `HFX` |
| `DV_ORGAO_TITULO` | Título do bloco do vínculo principal | `HFX – Hospital Federal X` |
| `DV_ORGAO_NOME` | Valor gravado em `orgao_entidade` do vínculo principal | `Hospital Federal X (MS)` |
| `DV_UNIDADE_GP` | Unidade que trata os dados (texto LGPD, metadado do PDF) | `DIGEP/HFX` |
| `DV_CIDADE_UF` | Local da manifestação | `Brasília/DF` |

3. **Revise os textos legais** do formulário (seção 8 de `app/static/formulario.html`) com a área jurídica, se o órgão tiver orientações próprias.
4. **Implante** conforme [implantacao.md](implantacao.md) e faça o teste com dados fictícios.
5. **Mantenha o esquema**: não altere `schema/` localmente. Assim, painéis e pipelines podem ser compartilhados entre órgãos. Para precisar de campo novo, abra issue ou PR no repositório principal.

Adaptações locais que não quebram compatibilidade: cores e fontes (variáveis CSS no topo do formulário), textos de ajuda, lista de documentos comprobatórios (desde que os códigos existentes continuem válidos).
