"""Geração de dados acadêmicos simulados para o SADA, no esquema do web acadêmico.

Nenhum dado pessoal real é utilizado. Os valores são produzidos por um gerador
pseudoaleatório com semente fixa (NumPy), o que torna o experimento reprodutível. O gerador
de nomes é injetável: em uso normal emprega-se a biblioteca Faker (pt_BR); nos testes pode-se
usar `nomes_padrao`, que não exige dependências externas.

As tabelas e colunas seguem os nomes do subconjunto do banco do web acadêmico usado pelo
SADA (aluno, diario, turma, disciplina, professor e tabelas referenciadas). A matriz
curricular é a do curso de Sistemas de Informação (49 disciplinas e 2 estágios), e o número
de matrícula segue a estrutura AA CC S T NNNN (módulo `matricula`).
"""
import random
from datetime import date
from typing import Callable, Dict

import numpy as np
import pandas as pd

from academico import grade_si, matricula as mat, regras

SEMENTE_PADRAO = 42
CODIGO_CURSO = 1                       # código do curso de SI no número de matrícula (exemplo)
CODIGO_GRADE = 1
PERIODOS_LETIVOS = [(a, s) for a in range(2021, 2027) for s in (1, 2)]
PERIODO_EM_CURSO = (2026, 2)
INGRESSANTES = [42, 38, 40, 36, 39, 37, 41, 35, 38, 34, 36, 40]   # 2021.1 a 2026.2
CAPACIDADE_TURMA = 50
N_PROFESSORES = 22
DIAS_LETIVOS_SEMESTRE = 30             # 60 h = 30 dias letivos x 2 aulas
FRACAO_EM_CURSO = 0.7                  # parcela do semestre corrente já ministrada

# parâmetros de calibração do modelo de notas, frequência, evasão e trancamento
MU_NOTA = 7.80
PESO_HABILIDADE = 1.05
DESVIO_AVALIACAO = 1.05
DESVIO_TURMA = 0.25
BONUS_REPETENTE = 0.30
FREQ_BASE, FREQ_PESO_ASSIDUIDADE, FREQ_DESVIO = 90.0, 6.5, 5.0
EVASAO_INTERCEPTO, EVASAO_HABILIDADE = 3.85, 0.90
EVASAO_INICIO, EVASAO_REPROVACOES = 0.90, 0.35
P_TRANCAMENTO = 0.05
P_EXAME = 0.90
EXAME_DESLOCAMENTO, EXAME_DESVIO = -0.30, 1.60
INATIVOS = {1: "Trancado", 2: "Evadido", 3: "Concluído"}

PRIMEIROS_NOMES = (
    "Ana Beatriz Bruno Camila Carlos Daniela Eduardo Fernanda Gabriel Helena "
    "Igor Isabela João Juliana Kleber Larissa Leonardo Letícia Lucas Luiza "
    "Marcelo Mariana Mateus Natália Otávio Paula Pedro Rafael Renata Rodrigo "
    "Sabrina Samuel Tatiane Thiago Valentina Vinícius Viviane Yasmin Wesley "
    "Adriana Alexandre Amanda André Bianca Caio Diego Elaine Felipe Gustavo "
    "Heitor Inês Jéssica Karina Lorena Murilo Nicole Patrícia Raquel Sérgio "
    "Talita Ulisses Vanessa Willian Aline Breno Cecília Davi Érica Flávio"
).split()
SOBRENOMES = (
    "Almeida Araújo Azevedo Barbosa Barros Batista Cardoso Carvalho Castro "
    "Cavalcanti Correia Costa Dias Duarte Fernandes Ferreira Freitas Gomes "
    "Gonçalves Lima Lopes Machado Marques Martins Medeiros Melo Mendes "
    "Moreira Moura Nascimento Nogueira Nunes Oliveira Pereira Pinto Ramos "
    "Reis Ribeiro Rocha Rodrigues Santana Santos Silva Soares Souza Teixeira "
    "Vieira Xavier Monteiro Campos Fonseca Borges Cunha Pires Tavares"
).split()


def nomes_padrao(semente: int = SEMENTE_PADRAO) -> Callable[[], str]:
    """Gerador de nomes fictícios sem dependências externas."""
    sorteio = random.Random(semente + 1)

    def gerar() -> str:
        return " ".join([sorteio.choice(PRIMEIROS_NOMES),
                         sorteio.choice(SOBRENOMES), sorteio.choice(SOBRENOMES)])
    return gerar


def _datas(ano: int, semestre: int):
    if semestre == 1:
        return date(ano, 2, 2), date(ano, 6, 26)
    return date(ano, 8, 3), date(ano, 12, 11)


def _sigmoide(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-x))


def _primeiro_pendente(grade, aprovadas) -> int:
    """Período curricular da primeira disciplina ainda não aprovada (8 se concluiu)."""
    for d in grade:
        if d["codigodisciplina"] not in aprovadas:
            return d["periodo"]
    return grade[-1]["periodo"]


def gerar_base(semente: int = SEMENTE_PADRAO,
               gerador_nomes: Callable[[], str] = None) -> Dict[str, pd.DataFrame]:
    """Retorna um dicionário de DataFrames, um por tabela do esquema simulado."""
    rng = np.random.default_rng(semente)
    nome = gerador_nomes or nomes_padrao(semente)
    grade = grade_si.disciplinas()
    por_id = {d["codigodisciplina"]: d for d in grade}
    n_por_periodo = {}
    for d in grade:
        n_por_periodo[d["periodo"]] = n_por_periodo.get(d["periodo"], 0) + 1
    ids_todas = {d["codigodisciplina"] for d in grade}

    curso = pd.DataFrame([{"codigocurso": CODIGO_CURSO, "nomecurso": "Sistemas de Informação",
                           "sigla": "SI"}])
    gradecurricular = pd.DataFrame([{"codigograde": CODIGO_GRADE, "codigocurso": CODIGO_CURSO,
                                     "nomegrade": "SI a partir de 2020/1", "anoinicio": 2020,
                                     "semestreinicio": 1}])
    disciplina = pd.DataFrame([{k: d[k] for k in ("codigodisciplina", "nomedisciplina",
                                                   "cargahoraria", "credito", "estagio")}
                               for d in grade])
    gradedisciplina = pd.DataFrame([{"codigograde": CODIGO_GRADE,
                                     "codigodisciplina": d["codigodisciplina"],
                                     "periodo": d["periodo"]} for d in grade])
    formacoes = ["Especialista", "Mestre", "Mestre", "Doutor", "Doutor"]
    professor = pd.DataFrame([{"codigoprofessor": i + 1, "nomeprofessor": nome(), "cpf": None,
                               "formacaoprofessor": formacoes[i % len(formacoes)]}
                              for i in range(N_PROFESSORES)])
    linhas_periodo = []
    for i, (ano, sem) in enumerate(PERIODOS_LETIVOS):
        ini, fim = _datas(ano, sem)
        linhas_periodo.append({"codigoperiodoletivo": i + 1, "ano": ano, "semestre": sem,
                               "datainicio": ini, "datafim": fim})
    periodoletivo = pd.DataFrame(linhas_periodo)
    inativo = pd.DataFrame([{"codigoinativo": k, "descricao": v} for k, v in INATIVOS.items()])

    alunos, turmas, diarios = [], [], []
    id_aluno = id_turma = id_diario = 0

    for k, (ano, sem) in enumerate(PERIODOS_LETIVOS):
        em_curso = (ano, sem) == PERIODO_EM_CURSO
        # --- ingressantes do semestre: matrículas distintas, sequencial aleatório ---
        quantidade = INGRESSANTES[k]
        sequenciais = rng.choice(np.arange(1, 10000), size=quantidade, replace=False)
        for seq in sequenciais:
            id_aluno += 1
            h = float(rng.normal())
            assiduidade = float(0.5 * h + np.sqrt(0.75) * rng.normal())
            alunos.append({
                "codigoaluno": id_aluno,
                "matricula": mat.montar(ano, CODIGO_CURSO, sem, int(seq)),
                "anoingresso": ano, "semestreingresso": sem,
                "codigoturno": mat.TURNO_NOTURNO, "codigocurso": CODIGO_CURSO,
                "nomealuno": nome(), "cpf": None, "codigograde": CODIGO_GRADE,
                "h": h, "a": assiduidade, "aprovadas": set(), "reprovadas": set(),
                "status": "ATIVO", "trancado_ate": -1, "sem_trancados": 0,
                "cursados": 0, "reprov_ultimo": 0})

        # --- estado de trancamento e escolha das disciplinas de cada estudante ---
        matriculados = {}
        for al in alunos:
            if al["status"] == "TRANCADO" and k >= al["trancado_ate"]:
                al["status"] = "ATIVO"
            if al["status"] != "ATIVO":
                continue
            elegivel = len(al["aprovadas"]) >= 6 and al["sem_trancados"] < 4
            sorteio_t = rng.random()
            duracao = int(rng.integers(1, 3))
            if elegivel and not em_curso and sorteio_t < P_TRANCAMENTO:
                al["status"] = "TRANCADO"
                al["trancado_ate"] = k + duracao
                al["sem_trancados"] += duracao
                continue
            pendentes = [d["codigodisciplina"] for d in grade
                         if d["codigodisciplina"] not in al["aprovadas"]]
            if not pendentes:
                continue
            p0 = por_id[pendentes[0]]["periodo"]
            quantas = max(6, n_por_periodo[p0])
            for cod in pendentes[:quantas]:
                matriculados.setdefault(cod, []).append(al)

        # --- evasão decidida antes do semestre (abandono se reflete nas faltas) ---
        evade = {}
        if not em_curso:
            for lista in matriculados.values():
                for al in lista:
                    if al["codigoaluno"] in evade:
                        continue
                    logit = (-EVASAO_INTERCEPTO - EVASAO_HABILIDADE * al["h"]
                             + EVASAO_INICIO * (1 if al["cursados"] <= 1 else 0)
                             + EVASAO_REPROVACOES * al["reprov_ultimo"])
                    evade[al["codigoaluno"]] = bool(rng.random() < _sigmoide(logit))

        # --- turmas e diários ---
        dias_letivos = (int(round(DIAS_LETIVOS_SEMESTRE * FRACAO_EM_CURSO)) if em_curso
                        else DIAS_LETIVOS_SEMESTRE)
        aulas = regras.aulas_ministradas(dias_letivos)
        resultado_sem = {}
        for cod in sorted(matriculados):
            disc = por_id[cod]
            lista = [matriculados[cod][i] for i in rng.permutation(len(matriculados[cod]))]
            n_turmas = int(np.ceil(len(lista) / CAPACIDADE_TURMA))
            for seq_turma, fatia in enumerate(np.array_split(np.arange(len(lista)), n_turmas),
                                              start=1):
                id_turma += 1
                prof = ((cod * 5 + (seq_turma - 1) * 11) % N_PROFESSORES) + 1
                turmas.append({"codigoturma": id_turma, "codigodisciplina": cod,
                               "codigoprofessor": prof, "codigoperiodoletivo": k + 1,
                               "sequenciaturma": seq_turma, "capacidade": CAPACIDADE_TURMA,
                               "diasletivos": dias_letivos,
                               "diarioencerrado": not em_curso})
                efeito_turma = float(rng.normal(0, DESVIO_TURMA))
                for pos in fatia:
                    al = lista[pos]
                    abandona = evade.get(al["codigoaluno"], False)
                    base = (MU_NOTA + PESO_HABILIDADE * al["h"] - disc["dificuldade"]
                            + efeito_turma
                            + (BONUS_REPETENTE if cod in al["reprovadas"] else 0.0))
                    ruido1 = float(rng.normal(0, DESVIO_AVALIACAO))
                    ruido2 = float(rng.normal(0, DESVIO_AVALIACAO))
                    queda = float(rng.uniform(2, 5))
                    ruido_freq = float(rng.normal(0, FREQ_DESVIO))
                    freq_abandono = float(rng.uniform(35, 70))
                    sorteio_exame = float(rng.random())
                    ruido_exame = float(rng.normal())
                    nota1 = float(np.clip(round(base + ruido1, 1), 0, 10))
                    pct = FREQ_BASE + FREQ_PESO_ASSIDUIDADE * al["a"] + ruido_freq
                    if abandona:
                        pct = freq_abandono
                    pct = float(np.clip(pct, 30, 100))
                    faltas = 0 if disc["estagio"] else int(round(aulas * (100 - pct) / 100))
                    faltas = max(0, min(faltas, aulas))
                    id_diario += 1
                    linha = {"codigodiario": id_diario, "codigoaluno": al["codigoaluno"],
                             "codigoturma": id_turma, "nota1": nota1, "nota2": None,
                             "nota": None, "notafinal": None, "faltas": faltas,
                             "resultado": None}
                    if not em_curso:
                        base2 = base - queda if abandona else base + ruido2
                        nota2 = float(np.clip(round(base2 + (0 if abandona else 0), 1), 0, 10))
                        media = regras.media_semestral(nota1, nota2)
                        freq = regras.percentual_frequencia(faltas, aulas)
                        nota_exame = None
                        if (regras.tem_direito_a_exame(media, freq)
                                and sorteio_exame < P_EXAME):
                            nota_exame = float(np.clip(round(
                                float(media) + EXAME_DESLOCAMENTO
                                + EXAME_DESVIO * ruido_exame, 1), 0, 10))
                            if nota_exame == float(media):
                                # o exame é identificado por diferir da média (ver `preparar`)
                                nota_exame = round(nota_exame + (0.1 if nota_exame < 10
                                                                 else -0.1), 1)
                        resultado = regras.classificar_resultado(media, freq, True, nota_exame)
                        linha.update(nota2=nota2, nota=float(media),
                                     notafinal=float(regras.nota_final(media, nota_exame)),
                                     resultado=resultado)
                        resultado_sem[(al["codigoaluno"], cod)] = resultado
                    diarios.append(linha)

        # --- atualização das trajetórias ao fim do semestre ---
        vistos = set()
        for cod, lista in matriculados.items():
            for al in lista:
                if not em_curso:
                    r = resultado_sem[(al["codigoaluno"], cod)]
                    if r == regras.APROVADO:
                        al["aprovadas"].add(cod)
                        al["reprovadas"].discard(cod)
                    else:
                        al["reprovadas"].add(cod)
                if al["codigoaluno"] not in vistos:
                    vistos.add(al["codigoaluno"])
        if not em_curso:
            for id_al in vistos:
                al = alunos[id_al - 1]
                al["cursados"] += 1
                al["reprov_ultimo"] = sum(
                    1 for cod, lista in matriculados.items()
                    if any(x["codigoaluno"] == id_al for x in lista)
                    and resultado_sem[(id_al, cod)] != regras.APROVADO)
                if evade.get(id_al, False):
                    al["status"] = "EVADIDO"
                elif al["aprovadas"] >= ids_todas:
                    al["status"] = "CONCLUIDO"

    # --- tabela de alunos no formato do esquema ---
    registros = []
    for al in alunos:
        pendente = _primeiro_pendente(grade, al["aprovadas"])
        cod_inativo = {"TRANCADO": 1, "EVADIDO": 2, "CONCLUIDO": 3}.get(al["status"])
        registros.append({
            "codigoaluno": al["codigoaluno"], "matricula": al["matricula"],
            "anoingresso": al["anoingresso"], "semestreingresso": al["semestreingresso"],
            "codigoturno": al["codigoturno"], "codigocurso": al["codigocurso"],
            "nomealuno": al["nomealuno"], "cpf": None, "codigograde": al["codigograde"],
            "periodoatual": pendente, "concluinte": al["status"] == "CONCLUIDO",
            "codigoinativo": cod_inativo})
    aluno = pd.DataFrame(registros)
    aluno["codigoinativo"] = aluno["codigoinativo"].astype("Int64")

    return {"curso": curso, "gradecurricular": gradecurricular, "disciplina": disciplina,
            "gradedisciplina": gradedisciplina, "professor": professor,
            "periodoletivo": periodoletivo, "inativo": inativo, "aluno": aluno,
            "turma": pd.DataFrame(turmas), "diario": pd.DataFrame(diarios)}
