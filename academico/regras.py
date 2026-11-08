"""Regras de negócio do SADA (sem dependência de Django).

As constantes e funções deste módulo implementam as regras RN01 a RN05 e RN09, extraídas
do Regimento da instituição (2019, arts. 75 e 76) e da Deliberação nº 09/2011 do Conselho Superior (cálculo
do Coeficiente de Rendimento). São usadas pela leitura dos dados, pelos indicadores, pelos
testes unitários e pelo script de simulação.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Optional, Tuple

MEDIA_APROVACAO = Decimal("7.00")        # RN01: Regimento, art. 76
MEDIA_MINIMA_EXAME = Decimal("4.00")     # RN03: Regimento, art. 76, parágrafo único
NOTA_MINIMA_EXAME = Decimal("5.00")      # RN03: nota mínima no exame final
FREQUENCIA_MINIMA = Decimal("75.00")     # RN02: Regimento, art. 75, § 1º
AULAS_POR_DIA_LETIVO = 2                 # simplificação do modelo: 60 h = 30 dias x 2 aulas

EM_CURSO = "EM_CURSO"
APROVADO = "APROVADO"
REPROVADO_NOTA = "REPROVADO_NOTA"
REPROVADO_FALTA = "REPROVADO_FALTA"
RESULTADOS = (APROVADO, REPROVADO_NOTA, REPROVADO_FALTA)

ATENCAO = "ATENCAO"
CRITICO = "CRITICO"


def _dec(valor) -> Decimal:
    """Converte para Decimal sem herdar imprecisões de ponto flutuante."""
    return valor if isinstance(valor, Decimal) else Decimal(str(valor))


def _nulo(valor) -> bool:
    """Trata None e NaN (valor ausente vindo de DataFrames) como ausência."""
    return valor is None or (isinstance(valor, float) and valor != valor)


def arredondar(valor, casas: int = 2) -> Decimal:
    """Arredonda para `casas` decimais, com meio para cima."""
    return _dec(valor).quantize(Decimal(1).scaleb(-casas), rounding=ROUND_HALF_UP)


def validar_nota(valor) -> Decimal:
    """RN08: a nota deve estar no intervalo fechado de 0 a 10."""
    nota = _dec(valor)
    if nota < 0 or nota > 10:
        raise ValueError("A nota deve estar entre 0 e 10.")
    return nota


def media_semestral(nota1, nota2) -> Optional[Decimal]:
    """RN04: média aritmética das notas N1 e N2 já lançadas.

    Com apenas uma nota lançada, a média parcial é essa nota; sem nenhuma, não há média.
    """
    notas = [validar_nota(n) for n in (nota1, nota2) if not _nulo(n)]
    if not notas:
        return None
    return arredondar(sum(notas) / len(notas))


def percentual_frequencia(faltas: int, aulas_ministradas: int) -> Optional[Decimal]:
    """Percentual de presença sobre as aulas já ministradas."""
    if aulas_ministradas <= 0:
        return None
    if faltas < 0 or faltas > aulas_ministradas:
        raise ValueError("Número de faltas incompatível com as aulas ministradas.")
    return arredondar(Decimal(100) * (aulas_ministradas - faltas) / aulas_ministradas)


def aulas_ministradas(dias_letivos: int) -> int:
    """Aulas ministradas a partir do número de dias letivos realizados."""
    return int(dias_letivos) * AULAS_POR_DIA_LETIVO


def tem_direito_a_exame(media, frequencia) -> bool:
    """RN03: exame final facultado com frequência mínima e média de 4,0 a 6,99."""
    if _nulo(media) or _nulo(frequencia):
        return False
    return (_dec(frequencia) >= FREQUENCIA_MINIMA
            and MEDIA_MINIMA_EXAME <= _dec(media) < MEDIA_APROVACAO)


def classificar_resultado(media, frequencia, concluida: bool, nota_exame=None) -> str:
    """Resultado do estudante na disciplina (RN01 a RN03).

    A reprovação por falta precede qualquer outro resultado (Regimento, art. 75, § 1º).
    Com média entre 4,0 e 6,99, o exame final, quando realizado, decide: aprovação com
    nota igual ou superior a 5,0, desconsiderada a média do semestre (art. 76).
    """
    if not concluida:
        return EM_CURSO
    if _nulo(frequencia) or _nulo(media):
        raise ValueError("Turma concluída exige média e frequência.")
    if _dec(frequencia) < FREQUENCIA_MINIMA:
        return REPROVADO_FALTA
    if _dec(media) >= MEDIA_APROVACAO:
        return APROVADO
    if tem_direito_a_exame(media, frequencia) and not _nulo(nota_exame):
        return APROVADO if _dec(nota_exame) >= NOTA_MINIMA_EXAME else REPROVADO_NOTA
    return REPROVADO_NOTA


def nota_final(media, nota_exame=None) -> Optional[Decimal]:
    """Nota final da disciplina: a do exame, quando houve; senão, a média do semestre."""
    if not _nulo(nota_exame):
        return arredondar(nota_exame)
    return None if _nulo(media) else arredondar(media)


def nivel_risco(media_parcial, frequencia) -> Optional[str]:
    """RN09: nível de risco de uma matrícula em andamento.

    CRITICO: frequência abaixo de 75% (reprovação por falta) ou média parcial abaixo de
    4,0 (fora da faixa do exame final). ATENCAO: média parcial de 4,0 a 6,99, que exigirá
    exame final. Valores ausentes não geram alerta.
    """
    if not _nulo(frequencia) and _dec(frequencia) < FREQUENCIA_MINIMA:
        return CRITICO
    if _nulo(media_parcial):
        return None
    media = _dec(media_parcial)
    if media < MEDIA_MINIMA_EXAME:
        return CRITICO
    if media < MEDIA_APROVACAO:
        return ATENCAO
    return None


def em_risco(media_parcial, frequencia) -> bool:
    """RF08: verdadeiro quando há algum nível de risco."""
    return nivel_risco(media_parcial, frequencia) is not None


def coeficiente_rendimento(itens: Iterable[Tuple[object, int, bool]]) -> Optional[Decimal]:
    """RN05: CR ponderado pela carga horária (Deliberação nº 09/2011 do Conselho Superior).

    Cada item é (nota final, carga horária, estágio). Entram todas as disciplinas
    cursadas, inclusive as reprovadas por falta; os estágios supervisionados ficam fora.
    """
    lista = [(_dec(m), int(ch)) for m, ch, estagio in itens
             if not estagio and not _nulo(m)]
    if not lista:
        return None
    carga_total = sum(ch for _, ch in lista)
    if carga_total <= 0:
        raise ValueError("A carga horária total deve ser positiva.")
    return arredondar(sum(m * ch for m, ch in lista) / carga_total)
