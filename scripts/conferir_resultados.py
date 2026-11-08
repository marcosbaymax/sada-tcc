"""Confere os números de referência do TCC sobre a base simulada (semente 42).

Uso, a partir da raiz do projeto:  python scripts/conferir_resultados.py
Não exige Django nem banco de dados: usa apenas Python, NumPy e pandas.
Cada linha mostra o valor obtido, o valor esperado e o veredito (OK ou DIVERGE).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from academico import simulacao                     # noqa: E402
from painel import indicadores as ind               # noqa: E402

ESPERADO = {
    "estudantes": 456, "professores": 22, "disciplinas": 51, "turmas": 426,
    "periodos letivos": 12, "diarios": 14184,
    "diarios encerrados": 12400, "diarios em andamento": 1784,
    "estudantes ativos": 298, "turmas em andamento": 52,
    "taxa de aprovacao (%)": 84.4, "reprovacao por nota (%)": 9.8,
    "reprovacao por falta (%)": 5.8, "media geral": 7.47,
    "frequencia media (%)": 88.9, "CR medio": 7.09,
    "alunos em risco critico": 35, "alunos em risco de atencao": 180,
    "diarios em risco critico": 53, "diarios em risco de atencao": 589,
    "divergencias de resultado": 0,
}


def obter():
    t = simulacao.gerar_base()
    df = ind.preparar(t)
    k = ind.kpis(df)
    res = ind.distribuicao_resultados(df).set_index("resultado")["percentual"]
    cur = df[~df.concluida]
    critico = set(cur.loc[cur.risco == "CRITICO", "codigoaluno"])
    com_risco = set(cur.loc[cur.risco.notna(), "codigoaluno"])
    return {
        "estudantes": len(t["aluno"]), "professores": len(t["professor"]),
        "disciplinas": len(t["disciplina"]), "turmas": len(t["turma"]),
        "periodos letivos": len(t["periodoletivo"]), "diarios": len(t["diario"]),
        "diarios encerrados": int(df.concluida.sum()), "diarios em andamento": len(cur),
        "estudantes ativos": int(cur.codigoaluno.nunique()),
        "turmas em andamento": int((~t["turma"]["diarioencerrado"]).sum()),
        "taxa de aprovacao (%)": round(float(res["APROVADO"]), 1),
        "reprovacao por nota (%)": round(float(res["REPROVADO_NOTA"]), 1),
        "reprovacao por falta (%)": round(float(res["REPROVADO_FALTA"]), 1),
        "media geral": k["media_geral"], "frequencia media (%)": k["frequencia_media"],
        "CR medio": round(float(ind.cr_por_aluno(df).cr.mean()), 2),
        "alunos em risco critico": len(critico),
        "alunos em risco de atencao": len(com_risco - critico),
        "diarios em risco critico": int((cur.risco == "CRITICO").sum()),
        "diarios em risco de atencao": int((cur.risco == "ATENCAO").sum()),
        "divergencias de resultado": len(ind.divergencias_resultado(df)),
    }


def main() -> int:
    obtido, falhas = obter(), 0
    for nome, esperado in ESPERADO.items():
        v = obtido[nome]
        ok = abs(v - esperado) < 1e-9
        falhas += not ok
        print(f"{nome:32s} obtido={v!s:>8}  esperado={esperado!s:>8}  {'OK' if ok else 'DIVERGE'}")
    print("\nTodos os valores conferem." if not falhas else f"\n{falhas} valor(es) divergente(s).")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
