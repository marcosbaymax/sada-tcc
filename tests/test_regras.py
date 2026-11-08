import unittest
from decimal import Decimal

from academico import regras as r


class TesteNotas(unittest.TestCase):
    def test_nota_valida_nos_limites(self):
        self.assertEqual(r.validar_nota(0), Decimal("0"))
        self.assertEqual(r.validar_nota("10"), Decimal("10"))

    def test_nota_fora_do_intervalo(self):
        for invalida in (-0.1, 10.1, 11):
            with self.assertRaises(ValueError):
                r.validar_nota(invalida)

    def test_media_aritmetica_de_n1_e_n2(self):
        self.assertEqual(r.media_semestral(8, 6), Decimal("7.00"))
        self.assertEqual(r.media_semestral("6.5", "7.0"), Decimal("6.75"))

    def test_media_parcial_com_uma_nota(self):
        self.assertEqual(r.media_semestral(8, None), Decimal("8.00"))
        self.assertEqual(r.media_semestral(float("nan"), 4.5), Decimal("4.50"))

    def test_media_sem_notas(self):
        self.assertIsNone(r.media_semestral(None, None))
        self.assertIsNone(r.media_semestral(float("nan"), float("nan")))

    def test_arredondamento_meio_para_cima(self):
        self.assertEqual(r.arredondar("5.995"), Decimal("6.00"))
        self.assertEqual(r.arredondar("5.994"), Decimal("5.99"))


class TesteFrequencia(unittest.TestCase):
    def test_frequencia_basica(self):
        self.assertEqual(r.percentual_frequencia(10, 40), Decimal("75.00"))

    def test_frequencia_sem_faltas(self):
        self.assertEqual(r.percentual_frequencia(0, 60), Decimal("100.00"))

    def test_faltas_acima_das_aulas(self):
        with self.assertRaises(ValueError):
            r.percentual_frequencia(61, 60)

    def test_sem_aulas_ministradas(self):
        self.assertIsNone(r.percentual_frequencia(0, 0))

    def test_aulas_ministradas_a_partir_dos_dias_letivos(self):
        self.assertEqual(r.aulas_ministradas(30), 60)
        self.assertEqual(r.aulas_ministradas(21), 42)


class TesteResultado(unittest.TestCase):
    def test_aprovado_com_media_sete(self):
        self.assertEqual(r.classificar_resultado("7.00", "75.00", True), r.APROVADO)

    def test_media_abaixo_de_sete_sem_exame_reprova(self):
        self.assertEqual(r.classificar_resultado("6.99", "90.00", True), r.REPROVADO_NOTA)

    def test_exame_final_aprova_com_cinco(self):
        self.assertEqual(r.classificar_resultado("6.00", "80.00", True, "5.00"), r.APROVADO)
        self.assertEqual(r.classificar_resultado("4.00", "80.00", True, "9.00"), r.APROVADO)

    def test_exame_final_abaixo_de_cinco_reprova(self):
        self.assertEqual(r.classificar_resultado("6.00", "80.00", True, "4.90"),
                         r.REPROVADO_NOTA)

    def test_media_abaixo_de_quatro_nao_tem_exame(self):
        self.assertFalse(r.tem_direito_a_exame("3.99", "90"))
        self.assertEqual(r.classificar_resultado("3.99", "90.00", True, "9.00"),
                         r.REPROVADO_NOTA)

    def test_limites_do_direito_a_exame(self):
        self.assertTrue(r.tem_direito_a_exame("4.00", "75.00"))
        self.assertTrue(r.tem_direito_a_exame("6.99", "75.00"))
        self.assertFalse(r.tem_direito_a_exame("7.00", "90"))
        self.assertFalse(r.tem_direito_a_exame("5.00", "74.99"))

    def test_reprovado_por_falta_precede_a_nota(self):
        self.assertEqual(r.classificar_resultado("9.00", "74.99", True), r.REPROVADO_FALTA)
        self.assertEqual(r.classificar_resultado("3.00", "50.00", True), r.REPROVADO_FALTA)

    def test_frequencia_minima_exata_nao_reprova(self):
        self.assertEqual(r.classificar_resultado("8.00", "75.00", True), r.APROVADO)

    def test_diario_em_andamento(self):
        self.assertEqual(r.classificar_resultado("5.00", "70.00", False), r.EM_CURSO)

    def test_diario_encerrado_exige_media_e_frequencia(self):
        with self.assertRaises(ValueError):
            r.classificar_resultado(None, "80", True)

    def test_nota_final_usa_o_exame_quando_houve(self):
        self.assertEqual(r.nota_final("6.00", "5.50"), Decimal("5.50"))
        self.assertEqual(r.nota_final("6.00"), Decimal("6.00"))
        self.assertIsNone(r.nota_final(None))


class TesteRisco(unittest.TestCase):
    def test_critico_por_frequencia(self):
        self.assertEqual(r.nivel_risco("9.00", "74.9"), r.CRITICO)

    def test_critico_por_media_abaixo_de_quatro(self):
        self.assertEqual(r.nivel_risco("3.90", "100"), r.CRITICO)

    def test_atencao_entre_quatro_e_sete(self):
        self.assertEqual(r.nivel_risco("4.00", "90"), r.ATENCAO)
        self.assertEqual(r.nivel_risco("6.99", "90"), r.ATENCAO)

    def test_sem_risco(self):
        self.assertIsNone(r.nivel_risco("7.00", "75.00"))
        self.assertFalse(r.em_risco("7.00", "75.00"))

    def test_valores_ausentes_nao_geram_risco(self):
        self.assertIsNone(r.nivel_risco(None, None))
        self.assertFalse(r.em_risco(float("nan"), float("nan")))

    def test_ausencia_de_media_com_frequencia_baixa_ainda_alerta(self):
        self.assertEqual(r.nivel_risco(None, "60"), r.CRITICO)


class TesteCoeficienteRendimento(unittest.TestCase):
    def test_cr_ponderado_por_carga_horaria(self):
        cr = r.coeficiente_rendimento([("8.00", 80, False), ("6.00", 40, False)])
        self.assertEqual(cr, Decimal("7.33"))

    def test_estagio_fica_fora_do_cr(self):
        cr = r.coeficiente_rendimento([("8.00", 60, False), ("10.00", 150, True)])
        self.assertEqual(cr, Decimal("8.00"))

    def test_reprovada_por_falta_entra_no_cr(self):
        cr = r.coeficiente_rendimento([("8.00", 60, False), ("2.00", 60, False)])
        self.assertEqual(cr, Decimal("5.00"))

    def test_cr_sem_disciplinas(self):
        self.assertIsNone(r.coeficiente_rendimento([]))
        self.assertIsNone(r.coeficiente_rendimento([("9.00", 150, True)]))


if __name__ == "__main__":
    unittest.main()
