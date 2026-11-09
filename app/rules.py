"""Regras de negócio: validação de documentos, indicadores de triagem e achatamento em tabelas."""
from __future__ import annotations


def cpf_valido(c: str | None) -> bool:
    c = "".join(ch for ch in (c or "") if ch.isdigit())
    if len(c) != 11 or c == c[0] * 11:
        return False
    for t in (9, 10):
        s = sum(int(c[i]) * (t + 1 - i) for i in range(t))
        if (s * 10 % 11) % 10 != int(c[t]):
            return False
    return True


def cnpj_valido(c: str | None) -> bool:
    c = "".join(ch for ch in (c or "") if ch.isdigit())
    if len(c) != 14 or c == c[0] * 14:
        return False

    def dv(n: int) -> int:
        pesos = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2] if n == 12 else [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        r = sum(p * int(c[i]) for i, p in enumerate(pesos)) % 11
        return 0 if r < 2 else 11 - r

    return dv(12) == int(c[12]) and dv(13) == int(c[13])


def validar_regras(doc: dict) -> list[str]:
    """Regras que o JSON Schema não expressa bem (dígitos verificadores, condicionais)."""
    erros = []
    if not cpf_valido(doc["identificacao"]["cpf"]):
        erros.append("identificacao/cpf: dígitos verificadores inválidos")
    emp = doc.get("empresa_privada") or {}
    if emp.get("participa") and not cnpj_valido(emp.get("cnpj")):
        erros.append("empresa_privada/cnpj: obrigatório e válido quando participa = true")
    if sum(1 for v in doc["vinculos"] if v["tipo"] == "principal") != 1:
        erros.append("vinculos: deve haver exatamente um vínculo do tipo 'principal'")
    return erros


def indicadores(d: dict) -> dict:
    """Indicadores de triagem. Não constituem decisão sobre a licitude da acumulação."""
    vs = d.get("vinculos") or []
    n = lambda x: float(x or 0)
    contratual = sum(n((v.get("jornada_semanal_cargo") or {}).get("horas")) for v in vs)
    efetiva = sum(n(v.get("jornada_efetiva_horas")) for v in vs)
    apos, pens, emp = d.get("aposentadoria") or {}, d.get("pensao") or {}, d.get("empresa_privada") or {}
    aux = sum(1 for v in vs if v.get("recebe_auxilio_alimentacao")) + bool(apos.get("recebe_auxilio_alimentacao")) + bool(pens.get("recebe_auxilio_alimentacao"))
    principal = next((v for v in vs if v.get("tipo") == "principal"), {})
    i = {
        "qtd_vinculos_publicos": len(vs),
        "qtd_outros_vinculos": sum(1 for v in vs if v.get("tipo") != "principal"),
        "carga_semanal_contratual_total": contratual,
        "carga_semanal_efetiva_total": efetiva,
        "acima_60h_semanais": efetiva > 60 or contratual > 60,
        "possui_acumulacao_declarada": len(vs) > 1 or bool(apos.get("possui")) or bool(pens.get("possui")),
        "recebe_proventos_aposentadoria": bool(apos.get("possui")),
        "recebe_pensao": bool(pens.get("possui")),
        "dedicacao_exclusiva_com_outro_vinculo": any((v.get("jornada_semanal_cargo") or {}).get("tipo") == "DE" for v in vs) and len(vs) > 1,
        "alerta_gerencia_empresa": emp.get("participa") is True and emp.get("condicao") == "nenhuma_das_anteriores",
        "auxilio_alimentacao_multiplo": aux > 1,
        "jornada_efetiva_divergente": any(
            (v.get("jornada_semanal_cargo") or {}).get("horas") is not None and v.get("jornada_efetiva_horas") is not None
            and float(v["jornada_efetiva_horas"]) != float(v["jornada_semanal_cargo"]["horas"])
            for v in vs
        ),
        "teletrabalho_orgao_principal": (principal.get("modalidade_trabalho") or {}).get("tipo") in ("teletrabalho_pgd", "hibrida"),
    }
    i["qtd_alertas"] = sum(i[k] for k in ("acima_60h_semanais", "dedicacao_exclusiva_com_outro_vinculo", "alerta_gerencia_empresa", "auxilio_alimentacao_multiplo")) + int(
        i["recebe_proventos_aposentadoria"] and len(vs) > 0
    )
    return i


COLS_DECLARACOES = [
    "declaracao_id", "protocolo", "versao", "enviado_em", "nome", "nome_social", "matricula_siape", "cpf", "setor_lotacao", "cargo_especialidade",
    "finalidade", "situacoes", "qtd_vinculos_publicos", "qtd_outros_vinculos", "carga_semanal_contratual_total", "carga_semanal_efetiva_total",
    "acima_60h_semanais", "possui_acumulacao_declarada", "recebe_proventos_aposentadoria", "aposentadoria_valor", "recebe_pensao", "pensao_regime",
    "pensao_valor", "empresa_participa", "empresa_condicao", "empresa_cnpj", "alerta_gerencia_empresa", "dedicacao_exclusiva_com_outro_vinculo",
    "auxilio_alimentacao_multiplo", "teletrabalho_orgao_principal", "qtd_alertas", "processo_sei",
]
COLS_VINCULOS = [
    "declaracao_id", "matricula_siape", "ordem", "tipo", "orgao_entidade", "esfera", "cargo_funcao", "jornada_tipo", "jornada_horas",
    "jornada_efetiva_horas", "horario_escala", "local_exercicio", "modalidade", "recebe_auxilio_alimentacao", "jornada_reduzida",
    "fc_possui", "fc_denominacao", "fc_tecnica_cientifica", "cc_possui", "cc_denominacao", "cc_tecnica_cientifica", "cc_jornada_horas",
]


def linha_declaracao(d: dict) -> dict:
    i, a, p, e = d["identificacao"], d.get("aposentadoria") or {}, d.get("pensao") or {}, d.get("empresa_privada") or {}
    return {
        **{k: d.get(k) for k in ("declaracao_id", "protocolo", "versao", "enviado_em")}, **i, **(d.get("indicadores") or {}),
        "finalidade": d["finalidade"]["tipo"], "situacoes": "|".join(d.get("situacoes") or []),
        "aposentadoria_valor": a.get("valor_proventos"), "pensao_regime": p.get("regime_previdenciario"), "pensao_valor": p.get("valor"),
        "empresa_participa": e.get("participa"), "empresa_condicao": e.get("condicao"), "empresa_cnpj": e.get("cnpj"),
        "processo_sei": (d.get("documentos") or {}).get("processo_sei"),
    }


def linhas_vinculos(d: dict) -> list[dict]:
    out = []
    for v in d.get("vinculos") or []:
        j, m, r, fc, cc = (v.get(k) or {} for k in ("jornada_semanal_cargo", "modalidade_trabalho", "jornada_reduzida", "funcao_confianca", "cargo_comissionado"))
        out.append({
            "declaracao_id": d["declaracao_id"], "matricula_siape": d["identificacao"]["matricula_siape"],
            **{k: v.get(k) for k in ("ordem", "tipo", "orgao_entidade", "esfera", "cargo_funcao", "jornada_efetiva_horas", "horario_escala", "local_exercicio", "recebe_auxilio_alimentacao")},
            "jornada_tipo": j.get("tipo"), "jornada_horas": j.get("horas"), "modalidade": m.get("tipo"), "jornada_reduzida": r.get("tipo"),
            "fc_possui": fc.get("possui"), "fc_denominacao": fc.get("denominacao"), "fc_tecnica_cientifica": fc.get("tecnica_cientifica"),
            "cc_possui": cc.get("possui"), "cc_denominacao": cc.get("denominacao"), "cc_tecnica_cientifica": cc.get("tecnica_cientifica"), "cc_jornada_horas": cc.get("jornada_horas"),
        })
    return out
