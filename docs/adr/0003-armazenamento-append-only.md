# ADR 0003 – Armazenamento append-only com hash

**Status:** aceita (2026-11-09)

## Contexto
A declaração tem efeitos disciplinares e penais (CP, art. 299). É preciso provar o que foi declarado e quando.

## Decisão
Cada envio é uma nova linha, nunca atualizada. Guardamos o JSON canônico (chaves ordenadas), seu SHA-256 e o horário do servidor. A versão vigente é obtida por visão.

## Consequências
- Trilha completa de retificações para a análise e para eventual processo.
- O código de verificação impresso no espelho permite conferir que o PDF corresponde ao registro.
- O volume cresce com as retificações; continua pequeno para o porte esperado.
