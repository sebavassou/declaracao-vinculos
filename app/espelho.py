"""Espelho da declaração (PDF e HTML) para juntada ao processo SEI."""
from __future__ import annotations

import html
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .config import settings

ROTULOS = {
    "finalidade": {"posse_ingresso": "Posse/ingresso", "atualizacao_cadastral": "Atualização cadastral", "alteracao_vinculo": "Alteração de vínculo",
                   "analise_acumulacao": "Análise de acumulação", "outra": "Outra"},
    "situacoes": {"servidor_empregado_ativo": "Servidor(a) ou empregado(a) público(a) em atividade", "militar_ativo": "Militar ativo",
                  "servidor_empregado_aposentado": "Servidor(a) ou empregado(a) público(a) aposentado(a)",
                  "militar_reserva_reformado": "Militar da reserva ou reformado(a)", "beneficiario_pensao": "Beneficiário(a) de pensão"},
    "jornada": {"20h": "20h", "30h": "30h", "40h": "40h", "DE": "Dedicação exclusiva", "outro": "Outra"},
    "modalidade": {"presencial": "Presencial", "teletrabalho_pgd": "Teletrabalho/PGD", "hibrida": "Híbrida", "outra": "Outra"},
    "reduzida": {"nao": "Não", "mp_2174_28_2001": "Sim – MP nº 2.174-28/2001", "decreto_1590_1995": "Sim – Decreto nº 1.590/1995", "outro": "Sim – outro fundamento"},
    "regime": {"rpps_uniao": "RPPS da União", "rpps_estadual_municipal": "RPPS estadual/municipal", "rgps": "RGPS (INSS)", "militar": "Sistema dos militares", "outro": "Outro"},
    "condicao": {"acionista": "Acionista", "cotista": "Cotista", "comanditario": "Comanditário(a)", "nenhuma_das_anteriores": "Nenhuma das anteriores"},
    "docs": {"declaracao_rh_outro_orgao": "Declaração do RH do outro órgão", "ato_aposentadoria_pensao_reserva": "Ato ou declaração de aposentadoria/pensão/reserva",
             "declaracao_jornada_orgao": "Declaração da jornada no órgão principal", "qsa_ou_contrato_social": "Extrato QSA ou contrato social"},
}


def _sn(v) -> str:
    return "Sim" if v is True else "Não" if v is False else "—"


def _txt(v) -> str:
    return "—" if v in (None, "") else str(v)


def _cpf(c: str) -> str:
    return f"{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}" if c and len(c) == 11 else _txt(c)


def _brl(v) -> str:
    return "—" if v is None else "R$ " + f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _dt(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).astimezone().strftime("%d/%m/%Y %H:%M:%S %Z")
    except (TypeError, ValueError):
        return _txt(iso)


def secoes(d: dict) -> list[tuple[str, list[tuple[str, str]]]]:
    """Conteúdo do espelho como (título da seção, [(rótulo, valor)])."""
    i, R = d["identificacao"], ROTULOS
    out = [
        ("Identificação do(a) servidor(a)", [
            ("Nome", i["nome"]), ("Nome social", _txt(i.get("nome_social"))), ("Matrícula SIAPE", i["matricula_siape"]), ("CPF", _cpf(i["cpf"])),
            ("Setor/lotação", i["setor_lotacao"]), ("Cargo/especialidade", i["cargo_especialidade"]), ("Telefone", i["telefone"]),
            ("E-mail pessoal", _txt(i.get("email_pessoal"))), ("E-mail institucional", i["email_institucional"]),
        ]),
        ("Finalidade e situações", [
            ("Finalidade", R["finalidade"].get(d["finalidade"]["tipo"], "—") + (f": {d['finalidade']['outra_descricao']}" if d["finalidade"].get("outra_descricao") else "")),
            ("Situações declaradas", "; ".join(R["situacoes"].get(s, s) for s in d["situacoes"])),
        ]),
    ]
    for v in d["vinculos"]:
        j, m, r, fc, cc = v["jornada_semanal_cargo"], v["modalidade_trabalho"], v["jornada_reduzida"], v["funcao_confianca"], v["cargo_comissionado"]
        titulo = f"Vínculo {v['ordem']} – " + ("vínculo principal" if v["tipo"] == "principal" else "outro vínculo")
        linhas = [("Órgão/entidade", v["orgao_entidade"])]
        if v["tipo"] != "principal":
            linhas += [("Esfera", _txt(v.get("esfera")).capitalize()), ("Matrícula no vínculo", _txt(v.get("matricula_vinculo")))]
        linhas += [
            ("Cargo/função", v["cargo_funcao"]), ("Jornada semanal do cargo", f"{R['jornada'].get(j['tipo'], j['tipo'])} ({j['horas']:g}h)"),
            ("Jornada efetivamente realizada", f"{v['jornada_efetiva_horas']:g}h semanais"), ("Horário/escala", _txt(v.get("horario_escala"))),
            ("Local de exercício", v["local_exercicio"]),
            ("Modalidade de trabalho", R["modalidade"].get(m["tipo"], m["tipo"]) + (f": {m['outra']}" if m.get("outra") else "")),
            ("Recebe auxílio-alimentação", _sn(v["recebe_auxilio_alimentacao"])),
            ("Jornada reduzida", R["reduzida"].get(r["tipo"], r["tipo"]) + (f": {r['fundamento']}" if r.get("fundamento") else "")),
            ("Função de confiança", _sn(fc["possui"]) + (f" – {fc['denominacao']} (técnica ou científica: {_sn(fc.get('tecnica_cientifica'))})" if fc["possui"] else "")),
            ("Cargo comissionado", _sn(cc["possui"]) + (f" – {cc['denominacao']} (técnico ou científico: {_sn(cc.get('tecnica_cientifica'))}; {cc.get('jornada_horas') or 0:g}h)" if cc["possui"] else "")),
        ]
        out.append((titulo, linhas))
    a, p, e = d["aposentadoria"], d["pensao"], d["empresa_privada"]
    esp = [("Aposentado(a)/proventos", _sn(a["possui"]))]
    if a["possui"]:
        esp += [("A partir de", _txt(a.get("data_inicio"))), ("Valor dos proventos", _brl(a.get("valor_proventos"))), ("Auxílio-alimentação na aposentadoria", _sn(a.get("recebe_auxilio_alimentacao")))]
    esp.append(("Beneficiário(a) de pensão", _sn(p["possui"])))
    if p["possui"]:
        esp += [("Origem da pensão", _txt(p.get("origem"))), ("Instituidor", _txt(p.get("instituidor"))), ("Matrícula", _txt(p.get("matricula"))),
                ("Regime previdenciário", R["regime"].get(p.get("regime_previdenciario"), "—")), ("Data da instituição", _txt(p.get("data_instituicao"))),
                ("Valor", _brl(p.get("valor"))), ("Auxílio-alimentação na pensão", _sn(p.get("recebe_auxilio_alimentacao")))]
    esp.append(("Participa de gerência/administração de empresa ou exerce o comércio", _sn(e["participa"])))
    if e["participa"]:
        esp += [("Condição", R["condicao"].get(e.get("condicao"), "—")), ("CNPJ", _txt(e.get("cnpj")))]
    esp.append(("Informações complementares", _txt(d.get("informacoes_complementares"))))
    out.append(("Situações especiais – complementação", esp))
    doc = d.get("documentos") or {}
    out.append(("Documentos comprobatórios", [
        ("Processo SEI", _txt(doc.get("processo_sei"))),
        ("Documentos juntados (declarados)", "; ".join(ROTULOS["docs"].get(x, x) for x in doc.get("juntados") or []) or "—"),
    ]))
    return out


TEXTO_MANIFESTACAO = (
    "Declaro que as informações prestadas neste formulário são verdadeiras, completas e atualizadas. Comprometo-me a comunicar "
    "imediatamente à unidade de gestão de pessoas qualquer alteração em meus vínculos ou na situação funcional que possa repercutir "
    "na análise de acumulação, inclusive alteração de jornada, local de exercício, afastamento/licença e modalidade de trabalho."
)


def gerar_pdf(d: dict, hash_sha256: str, login: str | None = None) -> bytes:
    buf = io.BytesIO()
    ss = getSampleStyleSheet()
    s_org = ParagraphStyle("org", parent=ss["Normal"], fontSize=7.5, leading=10, alignment=TA_CENTER, textColor=colors.HexColor("#444444"))
    s_tit = ParagraphStyle("tit", parent=ss["Title"], fontSize=13, leading=16, spaceAfter=2)
    s_h = ParagraphStyle("h", parent=ss["Heading2"], fontSize=9.5, leading=12, spaceBefore=8, spaceAfter=3, textColor=colors.HexColor("#0b5d7a"))
    s_cel = ParagraphStyle("cel", parent=ss["Normal"], fontSize=8.5, leading=10.5)
    s_lbl = ParagraphStyle("lbl", parent=s_cel, textColor=colors.HexColor("#555555"))
    s_txt = ParagraphStyle("txt", parent=ss["Normal"], fontSize=8.5, leading=11)

    def tabela(linhas):
        t = Table([[Paragraph(html.escape(k), s_lbl), Paragraph(html.escape(str(v)), s_cel)] for k, v in linhas], colWidths=[58 * mm, 117 * mm])
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9d3d8")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f2f5f7")), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
        return t

    m = d["manifestacao"]
    story = [
        Paragraph(html.escape(settings.cabecalho_1) + "<br/>" + html.escape(settings.cabecalho_2), s_org), Spacer(1, 6),
        Paragraph("Formulário de Declaração de Vínculos – espelho do preenchimento", s_tit),
        Paragraph("Base normativa: Instrução Normativa SGP/MGI nº 30, de 27 de janeiro de 2025, e alterações posteriores.", s_org), Spacer(1, 6),
        tabela([("Protocolo", d.get("protocolo", "—")), ("Versão", f"{d['versao']}" + (" (retificação)" if d["versao"] > 1 else "")),
                ("Enviado em", _dt(d["enviado_em"])), ("Login do declarante", login or "não exigido nesta instalação"),
                ("Código de verificação (SHA-256)", hash_sha256)]),
    ]
    for titulo, linhas in secoes(d):
        story += [Paragraph(html.escape(titulo), s_h), tabela(linhas)]
    story += [
        Paragraph("Manifestação do(a) servidor(a)", s_h),
        Paragraph(("[X] " if m.get("declara_veracidade") else "[ ] ") + TEXTO_MANIFESTACAO, s_txt), Spacer(1, 3),
        Paragraph(("[X] " if m.get("ciencia_lgpd") else "[ ] ") + "Declaro ciência do tratamento dos meus dados pessoais (Lei nº 13.709/2018).", s_txt), Spacer(1, 6),
        Paragraph(f"{html.escape(m.get('local') or settings.cidade_uf)}, {_txt(m.get('data'))}.", s_txt), Spacer(1, 8),
        Paragraph("Documento gerado eletronicamente a partir do envio registrado no sistema. Para conferir a integridade, compare o código "
                  "de verificação com o registro do protocolo. Junte este espelho ao processo SEI e assine-o eletronicamente no SEI.", s_org),
    ]

    def rodape(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#666666"))
        canvas.drawString(18 * mm, 10 * mm, f"Declaração de Vínculos · Protocolo {d.get('protocolo', '—')} · v{d['versao']}")
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Página {doc_.page}")
        canvas.restoreState()

    SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=14 * mm, bottomMargin=16 * mm,
                      title=f"Declaração de Vínculos {d.get('protocolo', '')}", author=settings.unidade_gp).build(story, onFirstPage=rodape, onLaterPages=rodape)
    return buf.getvalue()


def gerar_html(d: dict, hash_sha256: str, login: str | None = None) -> str:
    """Versão HTML simples, adequada para colar num documento interno do SEI ou enviar por WebService."""
    e = html.escape
    partes = [f"<p style='text-align:center;font-size:9pt'>{e(settings.cabecalho_1)}<br>{e(settings.cabecalho_2)}</p>",
              "<h2 style='text-align:center'>Formulário de Declaração de Vínculos</h2>",
              f"<p>Protocolo <b>{e(d.get('protocolo', '—'))}</b> · versão {d['versao']} · enviado em {e(_dt(d['enviado_em']))}"
              f" · login: {e(login or '—')}<br>Código de verificação (SHA-256): <code>{hash_sha256}</code></p>"]
    for titulo, linhas in secoes(d):
        partes.append(f"<h3>{e(titulo)}</h3><table border='1' cellpadding='4' cellspacing='0' style='border-collapse:collapse;width:100%'>"
                      + "".join(f"<tr><td style='width:35%'>{e(k)}</td><td>{e(str(v))}</td></tr>" for k, v in linhas) + "</table>")
    partes.append(f"<h3>Manifestação do(a) servidor(a)</h3><p>[X] {e(TEXTO_MANIFESTACAO)}</p><p>[X] Declaro ciência do tratamento dos meus dados pessoais (Lei nº 13.709/2018).</p>"
                  f"<p>{e(d['manifestacao'].get('local') or settings.cidade_uf)}, {e(_txt(d['manifestacao'].get('data')))}.</p>")
    return "<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><title>Declaração de Vínculos</title></head><body>" + "".join(partes) + "</body></html>"
