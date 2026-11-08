"""Matriz curricular do curso de Sistemas de Informação da instituição estudada (a partir de 2020/1).

Os nomes, os períodos e os códigos de compartilhamento foram transcritos da grade
curricular do curso. Cada disciplina obrigatória tem 4 créditos e 60 horas, o que
é compatível com os totais da grade (49 disciplinas = 196 créditos = 2.940 horas);
os dois estágios supervisionados (300 horas) são contabilizados à parte.

Os índices de dificuldade (0 a 1) NÃO provêm da instituição: são parâmetros do
modelo de simulação, atribuídos pelo autor, e não devem ser lidos como dado real.
"""
from typing import Dict, List

CARGA_HORARIA_DISCIPLINA = 60
CREDITOS_DISCIPLINA = 4
CARGA_HORARIA_ESTAGIO = 150

# Legenda dos códigos de compartilhamento da grade:
# 0 = comum a todos os cursos; 3 = exclusiva de SI; 6 = SI e Engenharia de Produção;
# 8 = SI e Licenciatura em Matemática; 9 = SI, EP e Matemática; 12 = SI, EP e Administração.
COMPARTILHAMENTO = {
    0: "Todos os cursos",
    3: "Somente Sistemas de Informação",
    6: "SI e Engenharia de Produção",
    8: "SI e Licenciatura em Matemática",
    9: "SI, Engenharia de Produção e Matemática",
    12: "SI, Engenharia de Produção e Administração",
}

# (período, nome, categoria B/P, código de compartilhamento, dificuldade, estágio)
_LINHAS = [
    (1, "Estruturas Organizacionais", "B", 3, 0.05, False),
    (1, "Filosofia e Ética", "B", 12, 0.00, False),
    (1, "Noções de Engenharia de Software", "B", 3, 0.15, False),
    (1, "Introdução à Lógica", "B", 8, 0.55, False),
    (1, "Noções Básicas de Programação", "B", 6, 0.60, False),
    (1, "Português Instrumental", "B", 0, 0.05, False),
    (2, "Estatística e Probabilidade", "B", 0, 0.60, False),
    (2, "Cálculo Diferencial e Integral A", "B", 3, 0.90, False),
    (2, "Análise de Sistemas I", "P", 3, 0.30, False),
    (2, "Organização de Computadores I", "P", 3, 0.50, False),
    (2, "Programação de Computadores I", "B", 6, 0.65, False),
    (2, "Fundamentos da Contabilidade", "B", 12, 0.35, False),
    (3, "Inferência Estatística", "B", 0, 0.60, False),
    (3, "Cálculo Diferencial e Integral B", "B", 3, 0.90, False),
    (3, "Análise de Sistemas II", "P", 3, 0.30, False),
    (3, "Organização de Computadores II", "P", 3, 0.50, False),
    (3, "Programação de Computadores II", "B", 3, 0.55, False),
    (3, "Metodologia da Pesquisa", "B", 0, 0.10, False),
    (4, "Cálculo Numérico (S.I.)", "B", 3, 0.70, False),
    (4, "Matemática Discreta", "B", 8, 0.80, False),
    (4, "Projeto de Sistemas I", "P", 3, 0.25, False),
    (4, "Gerência de Projetos", "P", 12, 0.10, False),
    (4, "Estrutura de Dados I", "P", 3, 0.70, False),
    (4, "Álgebra Linear", "B", 9, 0.80, False),
    (5, "Banco de Dados I", "P", 3, 0.35, False),
    (5, "Projeto de Sistemas II", "P", 3, 0.25, False),
    (5, "Programação de Computadores III", "P", 3, 0.45, False),
    (5, "Qualidade de Software", "P", 3, 0.20, False),
    (5, "Estrutura de Dados II", "P", 3, 0.65, False),
    (5, "Pesquisa Operacional I", "B", 6, 0.60, False),
    (6, "Banco de Dados II", "P", 3, 0.40, False),
    (6, "UX e Desenvolvimento Web", "P", 3, 0.20, False),
    (6, "Sistemas de Informações Gerenciais", "P", 12, 0.10, False),
    (6, "Optativa I", "P", 3, 0.05, False),
    (6, "Sistemas Operacionais I", "P", 3, 0.50, False),
    (6, "Gerência de Sistemas e Projetos", "P", 3, 0.20, False),
    (7, "Desenvolvimento de Sistemas I", "P", 3, 0.30, False),
    (7, "Desenvolvimento para Dispositivos Móveis", "P", 3, 0.30, False),
    (7, "Introdução a Redes de Computadores", "P", 3, 0.40, False),
    (7, "Optativa II", "P", 3, 0.05, False),
    (7, "Sistemas Operacionais II", "P", 3, 0.45, False),
    (7, "Trabalho de Conclusão de Curso I", "P", 3, 0.10, False),
    (7, "Estágio Supervisionado I", "P", 3, -0.60, True),
    (8, "Desenvolvimento de Sistemas II", "P", 3, 0.25, False),
    (8, "Banco de Dados III", "P", 3, 0.40, False),
    (8, "Gestão de Redes", "P", 3, 0.25, False),
    (8, "Optativa III", "P", 3, 0.05, False),
    (8, "Empreendedorismo e Gestão Estratégica", "P", 3, 0.00, False),
    (8, "Gerência em Informação", "P", 3, 0.10, False),
    (8, "Trabalho de Conclusão de Curso II", "P", 3, 0.00, False),
    (8, "Estágio Supervisionado II", "P", 3, -0.60, True),
]

# Estrutura de Dados II aparece na grade com o código P0 (comum a todos os cursos), mas
# com a cor das disciplinas exclusivas de SI; tratou-se como exclusiva (código 3).


def disciplinas() -> List[Dict]:
    """Lista de disciplinas na ordem da grade, com identificador sequencial."""
    saida = []
    for i, (per, nome, cat, comp, dif, estagio) in enumerate(_LINHAS, start=1):
        saida.append({
            "codigodisciplina": i, "nomedisciplina": nome, "periodo": per,
            "categoria": cat, "compartilhamento": comp, "dificuldade": dif,
            "estagio": estagio,
            "cargahoraria": CARGA_HORARIA_ESTAGIO if estagio else CARGA_HORARIA_DISCIPLINA,
            "credito": 0 if estagio else CREDITOS_DISCIPLINA,
        })
    return saida


def por_periodo() -> Dict[int, List[str]]:
    """Nomes das disciplinas por período curricular."""
    saida: Dict[int, List[str]] = {}
    for d in disciplinas():
        saida.setdefault(d["periodo"], []).append(d["nomedisciplina"])
    return saida


def totais() -> Dict[str, int]:
    """Totais conferíveis com o rodapé da grade (196 créditos; 2.940 h; 300 h de estágio)."""
    d = disciplinas()
    regulares = [x for x in d if not x["estagio"]]
    return {
        "disciplinas": len(regulares),
        "estagios": len(d) - len(regulares),
        "creditos": sum(x["credito"] for x in regulares),
        "horas": sum(x["cargahoraria"] for x in regulares),
        "horas_estagio": sum(x["cargahoraria"] for x in d if x["estagio"]),
        "periodos": max(x["periodo"] for x in d),
    }
