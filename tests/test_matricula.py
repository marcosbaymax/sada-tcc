import unittest

from academico import matricula as m


class TesteMatricula(unittest.TestCase):
    def test_exemplo_da_instituicao(self):
        """2101230020: 21 (ano), 01 (curso), 2 (semestre), 3 (noturno), 0020 (sequencial)."""
        self.assertEqual(m.montar(2021, 1, 2, 20), "2101230020")
        p = m.interpretar("2101230020")
        self.assertEqual((p.ano, p.curso, p.semestre, p.turno, p.sequencial),
                         (2021, 1, 2, 3, 20))
        self.assertEqual(p.coorte, "2021.2")

    def test_tem_sempre_dez_digitos(self):
        for seq in (0, 7, 9999):
            self.assertEqual(len(m.montar(2026, 1, 1, seq)), 10)

    def test_ida_e_volta(self):
        numero = m.montar(2024, 4, 1, 345)
        p = m.interpretar(numero)
        self.assertEqual(m.montar(p.ano, p.curso, p.semestre, p.sequencial, p.turno), numero)

    def test_formato_invalido(self):
        for ruim in ("123456789", "21012300201", "21A1230020", "2101330020", ""):
            self.assertFalse(m.eh_valida(ruim), ruim)
            with self.assertRaises(ValueError):
                m.interpretar(ruim)

    def test_partes_invalidas_na_montagem(self):
        for args in ((1999, 1, 1, 1), (2021, 100, 1, 1), (2021, 1, 3, 1), (2021, 1, 1, 10000)):
            with self.assertRaises(ValueError):
                m.montar(*args)

    def test_coerencia_com_o_cadastro(self):
        numero = "2101230020"
        self.assertTrue(m.coerente(numero, ano=2021, curso=1, semestre=2, turno=3))
        self.assertFalse(m.coerente(numero, ano=2022))
        self.assertFalse(m.coerente(numero, semestre=1))
        self.assertFalse(m.coerente("abc"))


if __name__ == "__main__":
    unittest.main()
