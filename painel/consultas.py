"""Conversão de consultas do ORM em DataFrames no layout esperado por `painel.indicadores`."""
from typing import Dict

import pandas as pd
from django.db.models import F, Q

from academico import models


def _df(qs, campos: Dict[str, str]) -> pd.DataFrame:
    """Uma única consulta SQL (`values`) por tabela; as colunas recebem o nome de saída."""
    iguais = [saida for saida, origem in campos.items() if saida == origem]
    renomeados = {saida: F(origem) for saida, origem in campos.items() if saida != origem}
    return pd.DataFrame.from_records(list(qs.values(*iguais, **renomeados)), columns=list(campos))


def registros(df: pd.DataFrame, colunas=None) -> list:
    """Lista de dicionários para os modelos de página e as exportações, com NaN/NA em None."""
    d = df if colunas is None else df[colunas]
    d = d.astype(object).where(d.notna(), None)
    return d.to_dict("records")


def filtrar_diarios(qs, filtros: dict):
    """Aplica no banco os filtros de período, disciplina e busca por estudante (RF06)."""
    if filtros.get("periodo"):
        qs = qs.filter(turma__periodo=filtros["periodo"])
    if filtros.get("disciplina"):
        qs = qs.filter(turma__disciplina=filtros["disciplina"])
    if filtros.get("busca"):
        termo = filtros["busca"]
        qs = qs.filter(Q(aluno__nomealuno__icontains=termo)
                       | Q(aluno__matricula__icontains=termo))
    return qs


def carregar_tabelas(diarios) -> Dict[str, pd.DataFrame]:
    """Carrega, a partir de um queryset de `Diario`, as tabelas usadas por `preparar`."""
    diarios = diarios.order_by("codigodiario")
    t = {}
    t["diario"] = _df(diarios, {
        "codigodiario": "codigodiario", "codigoaluno": "aluno_id", "codigoturma": "turma_id",
        "nota1": "nota1", "nota2": "nota2", "nota": "nota", "notafinal": "notafinal",
        "faltas": "faltas", "resultado": "resultado"})
    for col in ("nota1", "nota2", "nota", "notafinal"):
        t["diario"][col] = t["diario"][col].astype(float)
    ids_turma = diarios.values("turma_id")
    ids_aluno = diarios.values("aluno_id")
    turmas = models.Turma.objects.filter(pk__in=ids_turma)
    t["turma"] = _df(turmas, {
        "codigoturma": "codigoturma", "codigodisciplina": "disciplina_id",
        "codigoprofessor": "professor_id", "codigoperiodoletivo": "periodo_id",
        "sequenciaturma": "sequenciaturma", "diasletivos": "diasletivos",
        "diarioencerrado": "diarioencerrado"})
    t["aluno"] = _df(models.Aluno.objects.filter(pk__in=ids_aluno), {
        "codigoaluno": "codigoaluno", "matricula": "matricula", "nomealuno": "nomealuno",
        "codigograde": "grade_id", "concluinte": "concluinte",
        "codigoinativo": "inativo_id"})
    t["disciplina"] = _df(models.Disciplina.objects.filter(pk__in=turmas.values("disciplina_id")), {
        "codigodisciplina": "codigodisciplina", "nomedisciplina": "nomedisciplina",
        "cargahoraria": "cargahoraria", "estagio": "estagio"})
    t["gradedisciplina"] = _df(models.GradeDisciplina.objects.all(), {
        "codigograde": "grade_id", "codigodisciplina": "disciplina_id", "periodo": "periodo"})
    t["periodoletivo"] = _df(models.PeriodoLetivo.objects.all(), {
        "codigoperiodoletivo": "codigoperiodoletivo", "ano": "ano", "semestre": "semestre"})
    t["professor"] = _df(models.Professor.objects.all(), {
        "codigoprofessor": "codigoprofessor", "nomeprofessor": "nomeprofessor"})
    t["inativo"] = _df(models.Inativo.objects.all(), {
        "codigoinativo": "codigoinativo", "descricao": "descricao"})
    return t
