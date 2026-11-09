# Segurança e dados pessoais

Este sistema processa dados pessoais (CPF, vínculos, valores de proventos). Para relatar uma vulnerabilidade, **não abra issue pública**: use o recurso *Report a vulnerability* (aba Security) do repositório.

Recomendações mínimas de implantação:
- Publicar apenas atrás de HTTPS e, de preferência, apenas na rede interna ou com login institucional.
- Em `DV_AUTH_MODE=proxy`, a aplicação não pode ser alcançável diretamente: só o proxy, que deve **sobrescrever ou remover** os cabeçalhos de identidade vindos do cliente.
- Gerar `DV_API_TOKEN` aleatório e longo, guardá-lo em cofre de segredos e trocá-lo periodicamente.
- Fazer backup criptografado do volume `/dados` e restringir o acesso ao servidor.
- Nunca versionar `.env`, bancos `.sqlite3` ou espelhos PDF reais.
