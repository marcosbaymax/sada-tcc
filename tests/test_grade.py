import unittest

from academico import grade_si


class TesteGradeSI(unittest.TestCase):
    def test_totais_conferem_com_a_grade_oficial(self):
        t = grade_si.totais()
        self.assertEqual(t["disciplinas"], 49)
        self.assertEqual(t["estagios"], 2)
        self.assertEqual(t["creditos"], 196)
        self.assertEqual(t["horas"], 2940)
        self.assertEqual(t["horas_estagio"], 300)
        self.assertEqual(t["periodos"], 8)

    def test_carga_total_com_atividades_complementares(self):
        t = grade_si.totais()
        self.assertEqual(t["horas"] + t["horas_estagio"] + 100, 3340)

    def test_nomes_e_codigos_unicos(self):
        d = grade_si.disciplinas()
        self.assertEqual(len({x["nomedisciplina"] for x in d}), len(d))
        self.assertEqual(len({x["codigodisciplina"] for x in d}), len(d))

    def test_disciplinas_por_periodo(self):
        p = grade_si.por_periodo()
        self.assertEqual([len(p[i]) for i in range(1, 9)], [6, 6, 6, 6, 6, 6, 7, 8])

    def test_estagios_ficam_no_setimo_e_no_oitavo_periodo(self):
        est = [x["periodo"] for x in grade_si.disciplinas() if x["estagio"]]
        self.assertEqual(est, [7, 8])

    def test_codigos_de_compartilhamento_documentados(self):
        for x in grade_si.disciplinas():
            self.assertIn(x["compartilhamento"], grade_si.COMPARTILHAMENTO)


if __name__ == "__main__":
    unittest.main()
