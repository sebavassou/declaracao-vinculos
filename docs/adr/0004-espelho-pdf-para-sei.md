# ADR 0004 – Espelho PDF/HTML para o SEI antes da integração por WebService

**Status:** aceita (2026-11-09)

## Contexto
A declaração precisa constar no processo SEI. A inclusão automática exige que a administração do SEI do órgão cadastre a aplicação como sistema autorizado a usar os WebServices do SEI, o que depende de outro setor e de prazo.

## Decisão
Na versão 1.0, o sistema gera um espelho em PDF (para juntar como documento externo) e em HTML (para colar num documento interno). O servidor assina no SEI.

## Consequências
- Funciona em qualquer órgão sem integração.
- A integração automática fica para a fase 2 (ver `docs/fase2-sigepe-sougov.md`), reaproveitando `espelho.gerar_html`.
