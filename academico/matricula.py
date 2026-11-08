"""Estrutura do número de matrícula da instituição (10 dígitos): AA CC S T NNNN.

    2 1 | 0 1 | 2 | 3 | 0 0 2 0
    AA    CC    S   T   NNNN

AA   dois últimos dígitos do ano de ingresso;
CC   código do curso (dois dígitos);
S    semestre de ingresso (1 ou 2);
T    turno (3 = noturno, único turno dos cursos de graduação);
NNNN sequencial, de quatro dígitos, sem significado para a análise.

A estrutura foi informada pelo autor a partir do sistema acadêmico da instituição.
O século do ano de ingresso é assumido como 2000 (válido para 2000 a 2099).
"""
import re
from dataclasses import dataclass
from typing import Optional

TAMANHO = 10
TURNO_NOTURNO = 3
PADRAO = re.compile(r"^\d{10}$")


@dataclass(frozen=True)
class PartesMatricula:
    ano: int
    curso: int
    semestre: int
    turno: int
    sequencial: int

    @property
    def coorte(self) -> str:
        """Coorte de ingresso no formato 'AAAA.S'."""
        return f"{self.ano}.{self.semestre}"


def montar(ano: int, curso: int, semestre: int, sequencial: int,
           turno: int = TURNO_NOTURNO) -> str:
    """Compõe o número de matrícula a partir de suas partes."""
    if not 2000 <= ano <= 2099:
        raise ValueError("O ano de ingresso deve estar entre 2000 e 2099.")
    if not 0 <= curso <= 99:
        raise ValueError("O código do curso deve ter até dois dígitos.")
    if semestre not in (1, 2):
        raise ValueError("O semestre de ingresso deve ser 1 ou 2.")
    if not 0 <= turno <= 9:
        raise ValueError("O turno deve ter um dígito.")
    if not 0 <= sequencial <= 9999:
        raise ValueError("O sequencial deve ter até quatro dígitos.")
    return f"{ano % 100:02d}{curso:02d}{semestre}{turno}{sequencial:04d}"


def eh_valida(numero: str) -> bool:
    """Verifica apenas o formato (dez dígitos) e o semestre (1 ou 2)."""
    return bool(PADRAO.match(str(numero))) and str(numero)[4] in "12"


def interpretar(numero: str) -> PartesMatricula:
    """Decompõe um número de matrícula; lança ValueError se o formato é inválido."""
    numero = str(numero)
    if not eh_valida(numero):
        raise ValueError("Matrícula inválida: esperados 10 dígitos e semestre 1 ou 2.")
    return PartesMatricula(ano=2000 + int(numero[0:2]), curso=int(numero[2:4]),
                           semestre=int(numero[4]), turno=int(numero[5]),
                           sequencial=int(numero[6:10]))


def coerente(numero: str, ano: Optional[int] = None, curso: Optional[int] = None,
             semestre: Optional[int] = None, turno: Optional[int] = None) -> bool:
    """Confere se os atributos do cadastro concordam com o número de matrícula."""
    try:
        p = interpretar(numero)
    except ValueError:
        return False
    return ((ano is None or p.ano == ano) and (curso is None or p.curso == curso)
            and (semestre is None or p.semestre == semestre)
            and (turno is None or p.turno == turno))
