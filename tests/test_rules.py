from app import rules


def test_cpf():
    assert rules.cpf_valido("52998224725")
    assert not rules.cpf_valido("11111111111")
    assert not rules.cpf_valido("52998224724")


def test_cnpj():
    assert rules.cnpj_valido("11222333000181")
    assert not rules.cnpj_valido("11222333000180")


def test_indicadores_gerencia_e_de():
    d = {
        "vinculos": [
            {"tipo": "principal", "jornada_semanal_cargo": {"tipo": "DE", "horas": 40}, "jornada_efetiva_horas": 40, "recebe_auxilio_alimentacao": True, "modalidade_trabalho": {"tipo": "hibrida"}},
            {"tipo": "outro", "jornada_semanal_cargo": {"tipo": "20h", "horas": 20}, "jornada_efetiva_horas": 20, "recebe_auxilio_alimentacao": True},
        ],
        "aposentadoria": {"possui": False}, "pensao": {"possui": False},
        "empresa_privada": {"participa": True, "condicao": "nenhuma_das_anteriores"},
    }
    i = rules.indicadores(d)
    assert i["dedicacao_exclusiva_com_outro_vinculo"] and i["alerta_gerencia_empresa"] and i["auxilio_alimentacao_multiplo"]
    assert i["teletrabalho_orgao_principal"] and not i["acima_60h_semanais"] and i["qtd_alertas"] == 3
