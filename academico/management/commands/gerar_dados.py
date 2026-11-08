"""Comando: python manage.py gerar_dados --semente 42 --senha <senha-de-teste>.

Povoa o banco de desenvolvimento com a base simulada no esquema do web acadêmico.
Não deve ser executado contra o banco real da instituição.
"""
import pandas as pd
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from faker import Faker

from academico import models, simulacao


def _linhas(df):
    """Registros do DataFrame com NaN/NA convertidos em None."""
    return [{k: (None if pd.isna(v) else v) for k, v in r.items()}
            for r in df.to_dict("records")]


class Command(BaseCommand):
    help = "Popula o banco com dados acadêmicos simulados (sem dados pessoais reais)."

    def add_arguments(self, parser):
        parser.add_argument("--semente", type=int, default=simulacao.SEMENTE_PADRAO)
        parser.add_argument("--senha", required=True, help="Senha dos usuários de teste")

    @transaction.atomic
    def handle(self, *args, **opcoes):
        if models.Aluno.objects.exists() or User.objects.filter(username="coordenador").exists():
            raise CommandError("O banco já contém dados. Para recarregar, recrie o banco "
                               "(dropdb/createdb) e aplique as migrações novamente.")
        semente = opcoes["semente"]
        fake = Faker("pt_BR")
        Faker.seed(semente)
        nomes = lambda: f"{fake.first_name()} {fake.last_name()} {fake.last_name()}"
        t = simulacao.gerar_base(semente, gerador_nomes=nomes)

        coord, _ = Group.objects.get_or_create(name="Coordenador")
        prof, _ = Group.objects.get_or_create(name="Professor")
        User.objects.create_user("coordenador", password=opcoes["senha"]).groups.add(coord)

        models.Inativo.objects.bulk_create([models.Inativo(**r) for r in _linhas(t["inativo"])])
        models.Curso.objects.bulk_create([models.Curso(**r) for r in _linhas(t["curso"])])
        models.GradeCurricular.objects.bulk_create([
            models.GradeCurricular(codigograde=r["codigograde"], curso_id=r["codigocurso"],
                                   nomegrade=r["nomegrade"], anoinicio=r["anoinicio"],
                                   semestreinicio=r["semestreinicio"])
            for r in _linhas(t["gradecurricular"])])
        models.Disciplina.objects.bulk_create(
            [models.Disciplina(**r) for r in _linhas(t["disciplina"])])
        models.GradeDisciplina.objects.bulk_create([
            models.GradeDisciplina(grade_id=r["codigograde"],
                                   disciplina_id=r["codigodisciplina"], periodo=r["periodo"])
            for r in _linhas(t["gradedisciplina"])])
        for r in _linhas(t["professor"]):
            r.pop("cpf", None)                 # o CPF não é mapeado nem armazenado
            professor = models.Professor.objects.create(**r)
            usuario = User.objects.create_user(f"docente{r['codigoprofessor']:02d}",
                                               password=opcoes["senha"])
            usuario.groups.add(prof)
            models.PerfilProfessor.objects.create(usuario=usuario, professor=professor)
        models.PeriodoLetivo.objects.bulk_create(
            [models.PeriodoLetivo(**r) for r in _linhas(t["periodoletivo"])])
        models.Aluno.objects.bulk_create([
            models.Aluno(codigoaluno=r["codigoaluno"], matricula=r["matricula"],
                         anoingresso=r["anoingresso"], semestreingresso=r["semestreingresso"],
                         codigoturno=r["codigoturno"], curso_id=r["codigocurso"],
                         nomealuno=r["nomealuno"], grade_id=r["codigograde"],
                         periodoatual=r["periodoatual"], concluinte=r["concluinte"],
                         inativo_id=r["codigoinativo"])
            for r in _linhas(t["aluno"])])
        models.Turma.objects.bulk_create([
            models.Turma(codigoturma=r["codigoturma"], disciplina_id=r["codigodisciplina"],
                         professor_id=r["codigoprofessor"],
                         periodo_id=r["codigoperiodoletivo"],
                         sequenciaturma=r["sequenciaturma"], capacidade=r["capacidade"],
                         diasletivos=r["diasletivos"], diarioencerrado=r["diarioencerrado"])
            for r in _linhas(t["turma"])])
        models.Diario.objects.bulk_create([
            models.Diario(codigodiario=r["codigodiario"], aluno_id=r["codigoaluno"],
                          turma_id=r["codigoturma"], nota1=r["nota1"], nota2=r["nota2"],
                          nota=r["nota"], notafinal=r["notafinal"], faltas=r["faltas"],
                          resultado=r["resultado"])
            for r in _linhas(t["diario"])], batch_size=1000)
        self.stdout.write(self.style.SUCCESS(
            f"Base simulada carregada: {len(t['aluno'])} estudantes, "
            f"{len(t['diario'])} registros de diário."))
