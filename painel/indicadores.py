"""Indicadores de desempenho acadêmico (pandas), independentes de Django.

A entrada é o dicionário de tabelas do esquema do web acadêmico (aluno, diario, turma,
disciplina, gradedisciplina, periodoletivo, professor, inativo), na forma produzida por
`academico.simulacao.gerar_base` ou obtida por consulta ao banco. A função `preparar`
reúne as tabelas em um DataFrame plano (uma linha por registro de diário) e recalcula,
com as regras do módulo `regras`, média, frequência, resultado e nível de risco. Todos os
indicadores partem desse DataFrame.
"""
from decimal import Decimal
from typing import Dict, Optional

import numpy as np
import pandas as pd

from academico import matricula as mat
from academico import regras

# faixas da média do semestre alinhadas às regras: abaixo de 4,0 (sem direito a exame),
# de 4,0 a 6,9 (exame final), de 7,0 a 8,9 e de 9,0 a 10 (aprovação direta)
FAIXAS_MEDIA = [(0.0, 4.0, "0 a 3,9"), (4.0, 7.0, "4,0 a 6,9"),
                (7.0, 9.0, "7,0 a 8,9"), (9.0, 10.01, "9,0 a 10")]


def _f(valor) -> float:
    return np.nan if valor is None else float(valor)


def preparar(t: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Une as tabelas e recalcula as grandezas derivadas, uma linha por registro de diário."""
    per = t["periodoletivo"].assign(
        periodo=lambda d: d["ano"].astype(str) + "." + d["semestre"].astype(str))
    df = (t["diario"].rename(columns={"nota": "nota_armazenada",
                                      "notafinal": "notafinal_armazenada",
                                      "resultado": "resultado_armazenado"})
          .merge(t["turma"][["codigoturma", "codigodisciplina", "codigoprofessor",
                             "codigoperiodoletivo", "sequenciaturma", "diasletivos",
                             "diarioencerrado"]], on="codigoturma")
          .merge(t["aluno"][["codigoaluno", "matricula", "nomealuno", "codigograde"]],
                 on="codigoaluno")
          .merge(t["disciplina"][["codigodisciplina", "nomedisciplina", "cargahoraria",
                                  "estagio"]], on="codigodisciplina")
          .merge(t["gradedisciplina"].rename(columns={"periodo": "periodocurricular"}),
                 on=["codigograde", "codigodisciplina"], how="left")
          .merge(per[["codigoperiodoletivo", "periodo", "ano", "semestre"]],
                 on="codigoperiodoletivo")
          .merge(t["professor"][["codigoprofessor", "nomeprofessor"]],
                 on="codigoprofessor"))
    df["coorte"] = [mat.interpretar(m).coorte for m in df["matricula"]]
    df["concluida"] = df["diarioencerrado"].astype(bool)
    df["aulas"] = [regras.aulas_ministradas(d) for d in df["diasletivos"]]
    medias = [regras.media_semestral(a, b) for a, b in zip(df["nota1"], df["nota2"])]
    freqs = [regras.percentual_frequencia(int(f), int(a))
             for f, a in zip(df["faltas"], df["aulas"])]
    df["media"] = [_f(m) for m in medias]
    df["frequencia"] = [_f(x) for x in freqs]
    # o exame final é identificado quando a nota final difere da média do semestre
    exames = [None if (c is False or pd.isna(nf) or pd.isna(n) or nf == n) else nf
              for c, nf, n in zip(df["concluida"], df["notafinal_armazenada"],
                                  df["nota_armazenada"])]
    df["nota_exame"] = [_f(e) for e in exames]
    df["resultado"] = [
        regras.classificar_resultado(m, f, bool(c), e)
        for m, f, c, e in zip(medias, freqs, df["concluida"], exames)]
    df["nota_final"] = [_f(regras.nota_final(m, e)) for m, e in zip(medias, exames)]
    df["risco"] = [None if c else regras.nivel_risco(m, f)
                   for m, f, c in zip(medias, freqs, df["concluida"])]
    return df


def concluidas(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["concluida"]]


def _media(serie: pd.Series, casas: int = 2) -> float:
    """Média com arredondamento "meio para cima", como o ROUND do SQL (valores com 2 casas)."""
    v = serie.dropna()
    if v.empty:
        return float("nan")
    total = Decimal(int(round(float(v.sum()) * 100))) / 100
    return float(regras.arredondar(total / len(v), casas))


def _percentual(parte: int, total: int) -> float:
    return float(regras.arredondar(Decimal(100 * parte) / Decimal(total), 1))


def _taxa_aprovacao(s: pd.Series) -> float:
    return _percentual(int((s == regras.APROVADO).sum()), len(s))


def kpis(df: pd.DataFrame) -> dict:
    """Cartões do painel: aprovação, média, frequência e estudantes em risco."""
    c = concluidas(df)
    em_curso = df[~df["concluida"]]
    return {
        "taxa_aprovacao": _taxa_aprovacao(c["resultado"]) if len(c) else None,
        "media_geral": _media(c["media"], 2) if len(c) else None,
        "frequencia_media": _media(c["frequencia"], 1) if len(c) else None,
        "alunos_em_risco": int(em_curso.loc[em_curso["risco"].notna(),
                                            "codigoaluno"].nunique()),
        "alunos_em_risco_critico": int(em_curso.loc[em_curso["risco"] == regras.CRITICO,
                                                    "codigoaluno"].nunique()),
        "total_alunos": int(df["codigoaluno"].nunique()),
    }


def aprovacao_por_disciplina(df: pd.DataFrame) -> pd.DataFrame:
    """Taxa de aprovação e média por disciplina da grade (registros concluídos)."""
    c = concluidas(df)
    g = c.groupby(["periodocurricular", "codigodisciplina", "nomedisciplina"]).agg(
        registros=("codigodiario", "count"),
        taxa_aprovacao=("resultado", _taxa_aprovacao),
        media=("media", lambda s: _media(s, 2)),
    ).reset_index()
    return g.sort_values(["taxa_aprovacao", "codigodisciplina"]).reset_index(drop=True)


def aprovacao_por_periodo_curricular(df: pd.DataFrame) -> pd.DataFrame:
    """Taxa de aprovação, média e reprovação por falta em cada período da matriz."""
    c = concluidas(df)
    return c.groupby("periodocurricular").agg(
        registros=("codigodiario", "count"),
        taxa_aprovacao=("resultado", _taxa_aprovacao),
        reprovacao_falta=("resultado", lambda s: _percentual(
            int((s == regras.REPROVADO_FALTA).sum()), len(s))),
        media=("media", lambda s: _media(s, 2)),
    ).reset_index()


def evolucao_por_periodo(df: pd.DataFrame) -> pd.DataFrame:
    c = concluidas(df)
    return c.groupby("periodo").agg(
        registros=("codigodiario", "count"),
        estudantes=("codigoaluno", "nunique"),
        taxa_aprovacao=("resultado", _taxa_aprovacao),
        media=("media", lambda s: _media(s, 2)),
        frequencia=("frequencia", lambda s: _media(s, 1)),
    ).reset_index()


def distribuicao_notas(df: pd.DataFrame) -> pd.DataFrame:
    """Contagem de registros concluídos por faixa da média do semestre."""
    c = concluidas(df)
    linhas = []
    for lo, hi, rotulo in FAIXAS_MEDIA:
        n = int(((c["media"] >= lo) & (c["media"] < hi)).sum())
        linhas.append({"faixa": rotulo, "quantidade": n})
    return pd.DataFrame(linhas)


def distribuicao_resultados(df: pd.DataFrame) -> pd.DataFrame:
    c = concluidas(df)
    cont = c["resultado"].value_counts()
    return pd.DataFrame([{"resultado": r, "quantidade": int(cont.get(r, 0)),
                          "percentual": round(100 * cont.get(r, 0) / len(c), 1)}
                         for r in regras.RESULTADOS])


def exame_final(df: pd.DataFrame) -> dict:
    """Quantos registros foram a exame final e qual a taxa de aprovação nele."""
    c = concluidas(df)
    elegiveis = c[[regras.tem_direito_a_exame(m, f)
                   for m, f in zip(c["media"], c["frequencia"])]]
    feitos = c[c["nota_exame"].notna()]
    return {"elegiveis": int(len(elegiveis)), "realizados": int(len(feitos)),
            "aprovados_no_exame": int((feitos["resultado"] == regras.APROVADO).sum())}


def alunos_em_risco(df: pd.DataFrame, periodo: Optional[str] = None) -> pd.DataFrame:
    """RF08: registros em andamento com algum nível de risco (RN09)."""
    sel = df[~df["concluida"] & df["risco"].notna()]
    if periodo:
        sel = sel[sel["periodo"] == periodo]
    ordem = {regras.CRITICO: 0, regras.ATENCAO: 1}
    sel = sel.assign(_o=sel["risco"].map(ordem)).sort_values(["_o", "media", "matricula"])
    return sel[["matricula", "nomealuno", "nomedisciplina", "media", "frequencia",
                "risco"]].reset_index(drop=True)


def cr_por_aluno(df: pd.DataFrame) -> pd.DataFrame:
    """RN05: CR ponderado pela carga horária, com as disciplinas concluídas."""
    c = concluidas(df)
    linhas = []
    for codigo, g in c.groupby("codigoaluno"):
        cr = regras.coeficiente_rendimento(
            list(zip(g["nota_final"], g["cargahoraria"], g["estagio"])))
        if cr is not None:
            linhas.append({"codigoaluno": codigo, "matricula": g["matricula"].iloc[0],
                           "cr": float(cr)})
    return pd.DataFrame(linhas)


def historico_aluno(df: pd.DataFrame, matricula: str) -> pd.DataFrame:
    """Histórico de um estudante, em ordem cronológica e curricular."""
    h = df[df["matricula"] == matricula]
    return h.sort_values(["ano", "semestre", "periodocurricular", "codigodisciplina"])[
        ["periodo", "periodocurricular", "nomedisciplina", "media", "nota_final",
         "frequencia", "resultado"]].reset_index(drop=True)


def situacao_por_coorte(t: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Situação atual de cada coorte de ingresso, derivada do número de matrícula (AA.S).

    Considera concluinte quem tem `concluinte` verdadeiro; trancado ou evadido, conforme o
    código em `inativo`; ativo, quem não tem código de inativação nem concluiu.
    """
    a = t["aluno"].copy()
    a["coorte"] = [mat.interpretar(m).coorte for m in a["matricula"]]
    desc = t["inativo"].set_index("codigoinativo")["descricao"].to_dict()
    a["situacao"] = [
        "Concluído" if c else ("Ativo" if pd.isna(i) else desc[int(i)])
        for c, i in zip(a["concluinte"], a["codigoinativo"])]
    tab = a.pivot_table(index="coorte", columns="situacao", values="codigoaluno",
                        aggfunc="count", fill_value=0)
    for col in ("Ativo", "Trancado", "Evadido", "Concluído"):
        if col not in tab.columns:
            tab[col] = 0
    tab = tab[["Ativo", "Trancado", "Evadido", "Concluído"]].reset_index()
    tab["ingressantes"] = tab[["Ativo", "Trancado", "Evadido", "Concluído"]].sum(axis=1)
    tab["taxa_evasao"] = (100 * tab["Evadido"] / tab["ingressantes"]).round(1)
    tab["taxa_conclusao"] = (100 * tab["Concluído"] / tab["ingressantes"]).round(1)
    return tab.sort_values("coorte").reset_index(drop=True)


def divergencias_resultado(df: pd.DataFrame) -> pd.DataFrame:
    """Controle de qualidade: registros em que o dado armazenado difere do recalculado.

    Compara a média e o resultado gravados no diário com os obtidos pelas regras do SADA.
    """
    c = concluidas(df)
    dif_media = (c["nota_armazenada"] - c["media"]).abs() > 0.005
    dif_resultado = c["resultado_armazenado"] != c["resultado"]
    return c.loc[dif_media | dif_resultado,
                 ["codigodiario", "matricula", "nomedisciplina", "periodo", "nota_armazenada",
                  "media", "resultado_armazenado", "resultado"]].reset_index(drop=True)


def filtrar_situacao(df: pd.DataFrame, situacao: Optional[str]) -> pd.DataFrame:
    """Filtro de situação do formulário (RF06), aplicado ao resultado recalculado.

    Aceita EM_CURSO, um dos resultados, ATENCAO, CRITICO ou RISCO (qualquer nível).
    """
    if not situacao:
        return df
    if situacao == "EM_CURSO":
        return df[~df["concluida"]]
    if situacao == "RISCO":
        return df[df["risco"].notna()]
    if situacao in (regras.ATENCAO, regras.CRITICO):
        return df[df["risco"] == situacao]
    return df[df["resultado"] == situacao]
