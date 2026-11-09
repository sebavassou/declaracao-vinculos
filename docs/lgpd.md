# Tratamento de dados pessoais (Lei nº 13.709/2018)

| Item | Definição adotada |
|---|---|
| Controlador | Órgão que instala o sistema (por meio da unidade de gestão de pessoas) |
| Finalidade | Verificação de acumulação de cargos, empregos e funções e atualização cadastral (CF, art. 37, XVI e XVII; Lei nº 8.112/1990, arts. 117, X, e 118; IN SGP/MGI nº 30/2025) |
| Base legal | Cumprimento de obrigação legal e execução de políticas públicas (LGPD, arts. 7º, II e III, e 23) |
| Dados | Identificação (nome, CPF, SIAPE, contatos), vínculos e jornadas, proventos e pensão, participação societária |
| Dados de terceiros | Instituidor da pensão: apenas nome e matrícula |
| Minimização | E-mail pessoal opcional; anexos ficam no SEI, não na base |
| Acesso | Declarante (própria declaração), equipe de GP (`DV_ADMINS`), integrações com token |
| Compartilhamento | Somente nas hipóteses legais (órgão correcional, Polícia Federal em caso de falsidade, conforme IN 30/2025, art. 6º, § 3º) |
| Retenção | Conforme a tabela de temporalidade aplicável aos assentamentos funcionais |
| Segurança | HTTPS, login institucional, token de integração, trilha append-only com hash, backup criptografado (ver SECURITY.md) |

Antes de entrar em produção:
1. Submeter ao Encarregado pelo Tratamento de Dados Pessoais do órgão.
2. Avaliar a necessidade de Relatório de Impacto à Proteção de Dados (RIPD).
3. Registrar o tratamento no inventário de dados pessoais do órgão.
4. Em painéis, publicar apenas agregados, sem CPF e sem valores individuais.
