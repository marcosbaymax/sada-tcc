import unittest

import pandas as pd

from academico import exportacao, grade_si, matricula, regras, simulacao
from painel import indicadores


class TesteExportacao(unittest.TestCase):
    def test_csv_com_bom_e_separador(self):
        dados = exportacao.gerar_csv(["a", "b"], [[1, "x"]])
        self.assertTrue(dados.startswith(b"\xef\xbb\xbf"))
        self.assertIn(b"a;b", dados)

    def test_pdf_valido(self):
        pdf = exportacao.gerar_pdf("Teste", ["a", "b"], [[1, 2], [3, 4]])
        self.assertTrue(pdf.startswith(b"%PDF"))


class TesteSimulacao(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = simulacao.gerar_base()
        cls.df = indicadores.preparar(cls.t)

    def test_tabelas_do_esquema(self):
        self.assertEqual(set(self.t), {"curso", "gradecurricular", "disciplina",
                                       "gradedisciplina", "professor", "periodoletivo",
                                       "inativo", "aluno", "turma", "diario"})

    def test_reprodutibilidade_da_semente(self):
        outra = simulacao.gerar_base()
        self.assertTrue(outra["diario"].equals(self.t["diario"]))
        self.assertTrue(outra["aluno"].equals(self.t["aluno"]))

    def test_sementes_diferentes_geram_bases_diferentes(self):
        outra = simulacao.gerar_base(semente=7)
        self.assertFalse(outra["diario"].equals(self.t["diario"]))

    def test_matriz_curricular_completa(self):
        self.assertEqual(len(self.t["disciplina"]), 51)
        self.assertEqual(len(self.t["gradedisciplina"]), 51)
        self.assertEqual(len(self.t["professor"]), simulacao.N_PROFESSORES)
        self.assertEqual(len(self.t["periodoletivo"]), 12)

    def test_ingressantes_por_coorte(self):
        n = self.t["aluno"].groupby(["anoingresso", "semestreingresso"]).size().tolist()
        self.assertEqual(n, simulacao.INGRESSANTES)

    def test_matriculas_seguem_a_estrutura_da_instituicao(self):
        for r in self.t["aluno"].itertuples():
            self.assertTrue(matricula.eh_valida(r.matricula))
            self.assertTrue(matricula.coerente(r.matricula, ano=r.anoingresso,
                                               curso=r.codigocurso,
                                               semestre=r.semestreingresso,
                                               turno=r.codigoturno))
            self.assertEqual(len(r.matricula), 10)
            self.assertEqual(r.codigoturno, 3)

    def test_matriculas_unicas(self):
        self.assertFalse(self.t["aluno"]["matricula"].duplicated().any())

    def test_cpf_nao_e_gerado(self):
        self.assertTrue(self.t["aluno"]["cpf"].isna().all())
        self.assertTrue(self.t["professor"]["cpf"].isna().all())

    def test_integridade_referencial(self):
        d, t, a = self.t["diario"], self.t["turma"], self.t["aluno"]
        self.assertTrue(d["codigoturma"].isin(t["codigoturma"]).all())
        self.assertTrue(d["codigoaluno"].isin(a["codigoaluno"]).all())
        self.assertTrue(t["codigodisciplina"].isin(self.t["disciplina"]["codigodisciplina"]).all())
        self.assertTrue(t["codigoprofessor"].isin(self.t["professor"]["codigoprofessor"]).all())

    def test_unicidade_aluno_turma(self):
        self.assertFalse(self.t["diario"].duplicated(["codigoaluno", "codigoturma"]).any())

    def test_faixas_de_valores(self):
        d = self.t["diario"]
        for col in ("nota1", "nota2", "nota", "notafinal"):
            self.assertTrue(d[col].dropna().between(0, 10).all(), col)
        self.assertTrue((d["faltas"] >= 0).all())

    def test_faltas_nao_excedem_as_aulas(self):
        self.assertTrue((self.df["faltas"] <= self.df["aulas"]).all())

    def test_periodo_em_curso_tem_apenas_a_primeira_nota(self):
        cur = self.df[~self.df["concluida"]]
        self.assertGreater(len(cur), 0)
        self.assertTrue(cur["nota2"].isna().all())
        self.assertTrue(cur["resultado_armazenado"].isna().all())
        self.assertEqual(set(cur["periodo"]), {"2026.2"})

    def test_periodos_encerrados_tem_resultado(self):
        enc = self.df[self.df["concluida"]]
        self.assertTrue(enc["resultado_armazenado"].notna().all())
        self.assertTrue(enc["nota_armazenada"].notna().all())

    def test_ninguem_cursa_depois_de_aprovado(self):
        ordem = self.df.sort_values(["ano", "semestre"])
        aprov = ordem[ordem["resultado"] == regras.APROVADO]
        dup = aprov.duplicated(["codigoaluno", "codigodisciplina"])
        self.assertFalse(dup.any())

    def test_nao_cursa_antes_do_ingresso(self):
        ing = self.t["aluno"].set_index("codigoaluno")
        chave = self.df["ano"] * 10 + self.df["semestre"]
        ingresso = (self.df["codigoaluno"].map(ing["anoingresso"]) * 10
                    + self.df["codigoaluno"].map(ing["semestreingresso"]))
        self.assertTrue((chave >= ingresso).all())

    def test_concluintes_cursaram_toda_a_matriz(self):
        concl = self.t["aluno"][self.t["aluno"]["concluinte"]]
        self.assertGreater(len(concl), 0)
        aprov = self.df[self.df["resultado"] == regras.APROVADO]
        por_aluno = aprov.groupby("codigoaluno")["codigodisciplina"].nunique()
        self.assertTrue((por_aluno.loc[concl["codigoaluno"]] == 51).all())
        self.assertTrue((concl["codigoinativo"] == 3).all())

    def test_codigos_de_inativacao_existem(self):
        cod = self.t["aluno"]["codigoinativo"].dropna().astype(int)
        self.assertTrue(cod.isin(self.t["inativo"]["codigoinativo"]).all())

    def test_resultado_armazenado_coincide_com_o_recalculado(self):
        self.assertEqual(len(indicadores.divergencias_resultado(self.df)), 0)

    def test_divergencia_e_detectada(self):
        alterado = self.t["diario"].copy()
        i = alterado.index[alterado["resultado"] == regras.APROVADO][0]
        alterado.loc[i, "resultado"] = regras.REPROVADO_NOTA
        t2 = dict(self.t, diario=alterado)
        self.assertEqual(len(indicadores.divergencias_resultado(indicadores.preparar(t2))), 1)

    def test_taxa_de_aprovacao_proxima_do_alvo(self):
        taxa = indicadores.kpis(self.df)["taxa_aprovacao"]
        self.assertTrue(75 <= taxa <= 90, taxa)


class TesteIndicadores(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = simulacao.gerar_base()
        cls.df = indicadores.preparar(cls.t)

    def test_kpis_coerentes(self):
        k = indicadores.kpis(self.df)
        self.assertTrue(0 < k["taxa_aprovacao"] < 100)
        self.assertEqual(k["total_alunos"], self.df["codigoaluno"].nunique())
        self.assertLessEqual(k["alunos_em_risco_critico"], k["alunos_em_risco"])

    def test_distribuicao_cobre_todos_os_encerrados(self):
        d = indicadores.distribuicao_notas(self.df)
        self.assertEqual(int(d["quantidade"].sum()), len(indicadores.concluidas(self.df)))

    def test_distribuicao_de_resultados_soma_cem(self):
        d = indicadores.distribuicao_resultados(self.df)
        self.assertAlmostEqual(d["percentual"].sum(), 100.0, delta=0.2)

    def test_exame_final_aprova_parte_dos_elegiveis(self):
        e = indicadores.exame_final(self.df)
        self.assertGreater(e["elegiveis"], 0)
        self.assertLessEqual(e["realizados"], e["elegiveis"])
        self.assertLessEqual(e["aprovados_no_exame"], e["realizados"])

    def test_estudantes_em_risco_respeitam_a_regra(self):
        r = indicadores.alunos_em_risco(self.df, "2026.2")
        self.assertGreater(len(r), 0)
        for x in r.itertuples():
            self.assertEqual(x.risco, regras.nivel_risco(x.media, x.frequencia))
        self.assertTrue(r["risco"].isin([regras.ATENCAO, regras.CRITICO]).all())

    def test_risco_critico_vem_antes_de_atencao(self):
        r = indicadores.alunos_em_risco(self.df, "2026.2")
        primeiros = list(r["risco"])
        self.assertEqual(primeiros, sorted(primeiros, key=lambda x: x != regras.CRITICO))

    def test_encerrados_nao_tem_risco(self):
        self.assertTrue(self.df.loc[self.df["concluida"], "risco"].isna().all())

    def test_filtro_de_situacao(self):
        self.assertTrue(indicadores.filtrar_situacao(self.df, "CRITICO")["risco"].eq("CRITICO").all())
        self.assertTrue(indicadores.filtrar_situacao(self.df, "EM_CURSO")["concluida"].eq(False).all())
        self.assertTrue(indicadores.filtrar_situacao(self.df, "APROVADO")["resultado"].eq("APROVADO").all())
        self.assertEqual(len(indicadores.filtrar_situacao(self.df, "")), len(self.df))

    def test_cr_dentro_da_faixa_e_sem_estagios(self):
        cr = indicadores.cr_por_aluno(self.df)
        self.assertTrue(cr["cr"].between(0, 10).all())
        conc = self.df[self.df["concluida"]]
        so_estagio = conc.groupby("codigoaluno")["estagio"].all()
        self.assertFalse(cr["codigoaluno"].isin(so_estagio[so_estagio].index).any())

    def test_historico_ordenado_por_periodo(self):
        mat = self.t["aluno"]["matricula"].iloc[0]
        h = indicadores.historico_aluno(self.df, mat)
        self.assertTrue(h["periodo"].is_monotonic_increasing)

    def test_coortes_somam_os_ingressantes(self):
        c = indicadores.situacao_por_coorte(self.t)
        self.assertEqual(c["ingressantes"].tolist(), simulacao.INGRESSANTES)
        soma = c[["Ativo", "Trancado", "Evadido", "Concluído"]].sum(axis=1)
        self.assertTrue((soma == c["ingressantes"]).all())
        self.assertEqual(c["coorte"].tolist()[0], "2021.1")

    def test_coorte_derivada_da_matricula_coincide_com_o_ingresso(self):
        a = self.t["aluno"]
        derivada = [matricula.interpretar(m).coorte for m in a["matricula"]]
        informada = (a["anoingresso"].astype(str) + "." + a["semestreingresso"].astype(str))
        self.assertEqual(derivada, informada.tolist())

    def test_progressao_por_periodo_curricular(self):
        p = indicadores.aprovacao_por_periodo_curricular(self.df)
        self.assertEqual(p["periodocurricular"].tolist(), list(range(1, 9)))
        self.assertTrue(p["taxa_aprovacao"].between(0, 100).all())

    def test_aprovacao_por_disciplina_cobre_a_matriz(self):
        d = indicadores.aprovacao_por_disciplina(self.df)
        self.assertEqual(len(d), 51)
        self.assertTrue(d["taxa_aprovacao"].is_monotonic_increasing)

    def test_media_arredondada_meio_para_cima(self):
        self.assertEqual(indicadores._media(pd.Series([7.57, 7.58]), 2), 7.58)
        self.assertEqual(indicadores._percentual(1, 8), 12.5)


if __name__ == "__main__":
    unittest.main()
