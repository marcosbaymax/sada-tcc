"""Modelos do SADA: mapeamento ORM do subconjunto do banco do web acadêmico.

Princípios:
* os nomes de tabelas e colunas são os do web acadêmico (`db_table` e `db_column`);
* só as colunas necessárias à análise são declaradas (minimização, LGPD art. 6º, III).
  O CPF de alunos e professores, por exemplo, não é mapeado, de modo que nenhuma consulta
  do ORM o seleciona e o papel de leitura pode ter o acesso a essa coluna negado;
* trata-se de um protótipo: as tabelas são criadas pelas migrações do Django e povoadas com dados
  simulados (`gerar_dados`). A integração com o novo web acadêmico é trabalho futuro;
  a tabela `sada_perfil_professor` é a única própria do SADA (vínculo usuário-professor).
"""
from django.conf import settings
from django.db import models
from django.db.models import Q

FORMATO_MATRICULA = r"^[0-9]{4}[12][0-9]{5}$"


class Inativo(models.Model):
    codigoinativo = models.SmallIntegerField(primary_key=True)
    descricao = models.CharField(max_length=30, unique=True)

    class Meta:
        db_table = "inativo"

    def __str__(self):
        return self.descricao


class Curso(models.Model):
    codigocurso = models.SmallIntegerField(primary_key=True)
    nomecurso = models.CharField(max_length=120)
    sigla = models.CharField(max_length=10, unique=True)

    class Meta:
        db_table = "curso"

    def __str__(self):
        return self.sigla


class GradeCurricular(models.Model):
    codigograde = models.SmallIntegerField(primary_key=True)
    curso = models.ForeignKey(Curso, on_delete=models.DO_NOTHING, db_column="codigocurso")
    nomegrade = models.CharField(max_length=80)
    anoinicio = models.SmallIntegerField()
    semestreinicio = models.SmallIntegerField()

    class Meta:
        db_table = "gradecurricular"

    def __str__(self):
        return self.nomegrade


class Disciplina(models.Model):
    codigodisciplina = models.IntegerField(primary_key=True)
    nomedisciplina = models.CharField(max_length=120)
    cargahoraria = models.SmallIntegerField()
    credito = models.SmallIntegerField()
    estagio = models.BooleanField(default=False)

    class Meta:
        db_table = "disciplina"
        ordering = ["codigodisciplina"]

    def __str__(self):
        return self.nomedisciplina


class GradeDisciplina(models.Model):
    """Posição de cada disciplina na matriz curricular (período 1 a 8 em SI)."""
    pk = models.CompositePrimaryKey("grade_id", "disciplina_id")
    grade = models.ForeignKey(GradeCurricular, on_delete=models.DO_NOTHING,
                              db_column="codigograde")
    disciplina = models.ForeignKey(Disciplina, on_delete=models.DO_NOTHING,
                                   db_column="codigodisciplina")
    periodo = models.SmallIntegerField()

    class Meta:
        db_table = "gradedisciplina"


class Professor(models.Model):
    codigoprofessor = models.IntegerField(primary_key=True)
    nomeprofessor = models.CharField(max_length=120)
    formacaoprofessor = models.CharField(max_length=30, null=True, blank=True)

    class Meta:
        db_table = "professor"

    def __str__(self):
        return self.nomeprofessor


class PeriodoLetivo(models.Model):
    codigoperiodoletivo = models.IntegerField(primary_key=True)
    ano = models.SmallIntegerField()
    semestre = models.SmallIntegerField()
    datainicio = models.DateField()
    datafim = models.DateField()

    class Meta:
        db_table = "periodoletivo"
        ordering = ["ano", "semestre"]

    def __str__(self):
        return f"{self.ano}.{self.semestre}"


class Aluno(models.Model):
    codigoaluno = models.IntegerField(primary_key=True)
    matricula = models.CharField(max_length=10, unique=True)
    anoingresso = models.SmallIntegerField()
    semestreingresso = models.SmallIntegerField()
    codigoturno = models.SmallIntegerField()
    curso = models.ForeignKey(Curso, on_delete=models.DO_NOTHING, db_column="codigocurso")
    nomealuno = models.CharField(max_length=120)
    grade = models.ForeignKey(GradeCurricular, on_delete=models.DO_NOTHING,
                              db_column="codigograde")
    periodoatual = models.SmallIntegerField(null=True, blank=True)
    concluinte = models.BooleanField(default=False)
    inativo = models.ForeignKey(Inativo, on_delete=models.DO_NOTHING, null=True, blank=True,
                                db_column="codigoinativo")

    class Meta:
        db_table = "aluno"
        ordering = ["nomealuno"]
        constraints = [models.CheckConstraint(
            condition=Q(matricula__regex=FORMATO_MATRICULA), name="ck_matricula_formato")]

    def __str__(self):
        return f"{self.matricula} - {self.nomealuno}"


class Turma(models.Model):
    codigoturma = models.IntegerField(primary_key=True)
    disciplina = models.ForeignKey(Disciplina, on_delete=models.DO_NOTHING,
                                   db_column="codigodisciplina", related_name="turmas")
    professor = models.ForeignKey(Professor, on_delete=models.DO_NOTHING,
                                  db_column="codigoprofessor", related_name="turmas")
    periodo = models.ForeignKey(PeriodoLetivo, on_delete=models.DO_NOTHING,
                                db_column="codigoperiodoletivo", related_name="turmas")
    sequenciaturma = models.SmallIntegerField()
    capacidade = models.SmallIntegerField()
    diasletivos = models.SmallIntegerField()
    diarioencerrado = models.BooleanField(default=False)

    class Meta:
        db_table = "turma"

    def __str__(self):
        return f"{self.disciplina_id}-{self.sequenciaturma} ({self.periodo})"


class Diario(models.Model):
    codigodiario = models.IntegerField(primary_key=True)
    aluno = models.ForeignKey(Aluno, on_delete=models.DO_NOTHING, db_column="codigoaluno",
                              related_name="diarios")
    turma = models.ForeignKey(Turma, on_delete=models.DO_NOTHING, db_column="codigoturma",
                              related_name="diarios")
    nota1 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    nota2 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    nota = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    notafinal = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    faltas = models.SmallIntegerField(default=0)
    resultado = models.CharField(max_length=16, null=True, blank=True)

    class Meta:
        db_table = "diario"
        constraints = [models.UniqueConstraint(fields=["aluno", "turma"], name="uq_diario")]


class PerfilProfessor(models.Model):
    """Tabela própria do SADA: vincula o usuário do Django ao professor (RN07)."""
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   primary_key=True, related_name="perfil_professor")
    professor = models.OneToOneField(Professor, on_delete=models.CASCADE,
                                     db_column="codigoprofessor", related_name="perfil")

    class Meta:
        db_table = "sada_perfil_professor"
