# ADR 0002 – Login institucional delegado ao proxy reverso

**Status:** aceita (2026-11-09)

## Contexto
Cada órgão usa um provedor de identidade diferente: Active Directory/LDAP, Keycloak, ADFS, Microsoft Entra ID ou gov.br.

## Decisão
A aplicação não implementa protocolos de login. Em `DV_AUTH_MODE=proxy`, confia em cabeçalhos (`X-Remote-User`, `X-Remote-Email`, `X-Remote-Name`, configuráveis) definidos por um proxy reverso que fez a autenticação. Exemplos em `deploy/`.

## Consequências
- O mesmo código serve qualquer provedor, e a TI usa a ferramenta que já opera.
- **Requisito de segurança**: a aplicação só pode ser alcançada pelo proxy, que precisa sobrescrever esses cabeçalhos. As rotas de integração ficam fora do login e aceitam apenas token.
- Para o gov.br (Login Único), o órgão precisa credenciar a aplicação; o proxy OIDC é o mesmo.
