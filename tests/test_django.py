"""Testes de integração (pytest-django). Executar: pytest -q

Usam o banco de teste criado pelas migrações.
"""
import datetime

import pytest
from django.contrib.auth.models import Group, User
from django.db import IntegrityError, transaction
from django.urls import NoReverseMatch, reverse

from academico import services
from academico.models import (Aluno, Curso, Diario, Disciplina, GradeCurricular,
                              GradeDisciplina, Inativo, PerfilProfessor, PeriodoLetivo,
                              Professor, Turma)

pytestmark = pytest.mark.django_db


@pytest.fixture
def cenario(db):
    coord_g = Group.objects.create(name="Coordenador")
    prof_g = Group.objects.create(name="Professor")
    coord = User.objects.create_user("coord", password="x")
    coord.groups.add(coord_g)
    u1 = User.objects.create_user("prof1", password="x")
    u1.groups.add(prof_g)
    u2 = User.objects.create_user("prof2", password="x")
    u2.groups.add(prof_g)

    Inativo.objects.create(codigoinativo=2, descricao="Evadido")
    curso = Curso.objects.create(codigocurso=1, nomecurso="Sistemas de Informação", sigla="SI")
    grade = GradeCurricular.objects.create(codigograde=1, curso=curso, nomegrade="SI 2020/1",
                                           anoinicio=2020, semestreinicio=1)
    bd = Disciplina.objects.create(codigodisciplina=25, nomedisciplina="Banco de Dados I",
                                   cargahoraria=60, credito=4)
    GradeDisciplina.objects.create(grade=grade, disciplina=bd, periodo=5)
    p1 = Professor.objects.create(codigoprofessor=1, nomeprofessor="Professor Um")
    p2 = Professor.objects.create(codigoprofessor=2, nomeprofessor="Professor Dois")
    PerfilProfessor.objects.create(usuario=u1, professor=p1)
    PerfilProfessor.objects.create(usuario=u2, professor=p2)
    enc = PeriodoLetivo.objects.create(codigoperiodoletivo=1, ano=2026, semestre=1,
                                       datainicio=datetime.date(2026, 2, 2),
                                       datafim=datetime.date(2026, 6, 26))
    cur = PeriodoLetivo.objects.create(codigoperiodoletivo=2, ano=2026, semestre=2,
                                       datainicio=datetime.date(2026, 8, 3),
                                       datafim=datetime.date(2026, 12, 11))
    t1 = Turma.objects.create(codigoturma=1, disciplina=bd, professor=p1, periodo=enc,
                              sequenciaturma=1, capacidade=50, diasletivos=30,
                              diarioencerrado=True)
    t2 = Turma.objects.create(codigoturma=2, disciplina=bd, professor=p2, periodo=enc,
                              sequenciaturma=2, capacidade=50, diasletivos=30,
                              diarioencerrado=True)
    t3 = Turma.objects.create(codigoturma=3, disciplina=bd, professor=p1, periodo=cur,
                              sequenciaturma=1, capacidade=50, diasletivos=21,
                              diarioencerrado=False)

    def aluno(i, matricula, nome):
        return Aluno.objects.create(codigoaluno=i, matricula=matricula, anoingresso=2025,
                                    semestreingresso=1, codigoturno=3, curso=curso,
                                    nomealuno=nome, grade=grade)
    a1 = aluno(1, "2501130001", "Ana Aprovada")
    a2 = aluno(2, "2501130002", "Bruno Reprovado")
    a3 = aluno(3, "2501130003", "Carla Crítica")
    d1 = Diario.objects.create(codigodiario=1, aluno=a1, turma=t1, nota1=8, nota2=7, nota=7.5,
                               notafinal=7.5, faltas=4, resultado="APROVADO")
    Diario.objects.create(codigodiario=2, aluno=a2, turma=t1, nota1=5, nota2=4, nota=4.5,
                          notafinal=4.5, faltas=2, resultado="REPROVADO_NOTA")
    Diario.objects.create(codigodiario=3, aluno=a3, turma=t2, nota1=9, nota2=9, nota=9,
                          notafinal=9, faltas=0, resultado="APROVADO")
    Diario.objects.create(codigodiario=4, aluno=a1, turma=t3, nota1=3.0, faltas=2)
    return dict(coord=coord, u1=u1, u2=u2, t1=t1, t2=t2, t3=t3, d1=d1)


def test_login_obrigatorio(client):
    resp = client.get(reverse("painel"))
    assert resp.status_code == 302 and "login" in resp.url


def test_professor_ve_apenas_suas_turmas(cenario):
    ids = set(services.turmas_visiveis(cenario["u1"]).values_list("pk", flat=True))
    assert ids == {cenario["t1"].pk, cenario["t3"].pk}


def test_coordenador_ve_todas_as_turmas(cenario):
    assert services.turmas_visiveis(cenario["coord"]).count() == 3


def test_diarios_visiveis_ao_professor(cenario):
    assert set(services.diarios_visiveis(cenario["u2"]).values_list("pk", flat=True)) == {3}


def test_painel_acessivel_ao_coordenador(client, cenario):
    client.force_login(cenario["coord"])
    resp = client.get(reverse("painel"))
    assert resp.status_code == 200 and "Taxa de aprovação" in resp.content.decode()


def test_painel_exibe_coortes_apenas_ao_coordenador(client, cenario):
    client.force_login(cenario["u1"])
    resp = client.get(reverse("painel"))
    assert resp.status_code == 200 and "g_coortes" not in resp.context
    client.force_login(cenario["coord"])
    assert "g_coortes" in client.get(reverse("painel")).context


def test_consulta_destaca_o_risco_critico(client, cenario):
    client.force_login(cenario["u1"])
    resp = client.get(reverse("consulta"), {"situacao": "CRITICO"})
    assert resp.status_code == 200
    linhas = list(resp.context["pagina"])
    assert [l["matricula"] for l in linhas] == ["2501130001"]
    assert linhas[0]["risco"] == "CRITICO"


def test_consulta_filtra_por_resultado(client, cenario):
    client.force_login(cenario["coord"])
    resp = client.get(reverse("consulta"), {"situacao": "REPROVADO_NOTA"})
    assert [l["matricula"] for l in resp.context["pagina"]] == ["2501130002"]


def test_historico_com_cr(client, cenario):
    client.force_login(cenario["coord"])
    resp = client.get(reverse("historico", args=["2501130001"]))
    assert resp.status_code == 200 and resp.context["cr"] == pytest.approx(7.5)


def test_historico_fora_do_escopo_do_professor(client, cenario):
    client.force_login(cenario["u2"])
    assert client.get(reverse("historico", args=["2501130001"])).status_code == 404


def test_divergencias_apenas_para_coordenador(client, cenario):
    client.force_login(cenario["u1"])
    assert client.get(reverse("divergencias")).status_code == 403
    client.force_login(cenario["coord"])
    resp = client.get(reverse("divergencias"))
    assert resp.status_code == 200 and resp.context["total"] == 0


def test_divergencia_aparece_quando_o_dado_difere(client, cenario):
    Diario.objects.filter(pk=1).update(resultado="REPROVADO_NOTA")
    client.force_login(cenario["coord"])
    assert client.get(reverse("divergencias")).context["total"] == 1


def test_exportacao_csv(client, cenario):
    client.force_login(cenario["coord"])
    resp = client.get(reverse("exportar", args=["csv"]))
    assert resp["Content-Type"].startswith("text/csv")
    assert b"2501130001" in resp.content


def test_exportacao_pdf(client, cenario):
    client.force_login(cenario["coord"])
    assert client.get(reverse("exportar", args=["pdf"])).content.startswith(b"%PDF")


def test_formato_de_exportacao_inexistente(client, cenario):
    client.force_login(cenario["coord"])
    assert client.get(reverse("exportar", args=["xml"])).status_code == 404


def test_nao_ha_rota_de_lancamento_de_notas():
    """O SADA é somente leitura: o lançamento permanece no web acadêmico."""
    with pytest.raises(NoReverseMatch):
        reverse("lancar_nota", args=[1, 1, 1])


def test_banco_rejeita_matricula_malformada(cenario):
    curso, grade = Curso.objects.get(), GradeCurricular.objects.get()
    with pytest.raises(IntegrityError), transaction.atomic():
        Aluno.objects.create(codigoaluno=99, matricula="123", anoingresso=2025,
                             semestreingresso=1, codigoturno=3, curso=curso,
                             nomealuno="X", grade=grade)


def test_modelo_nao_mapeia_o_cpf():
    nomes = {f.name for f in Aluno._meta.get_fields()} | {f.name for f in Professor._meta.get_fields()}
    assert "cpf" not in nomes
