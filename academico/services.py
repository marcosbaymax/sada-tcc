"""Camada de serviços: visibilidade dos dados (RN07) e carga dos dados para análise."""
from .models import Diario, Turma


def eh_coordenador(usuario) -> bool:
    return usuario.groups.filter(name="Coordenador").exists()


def turmas_visiveis(usuario):
    """RN07: o coordenador enxerga todas as turmas; o professor, apenas as próprias."""
    base = Turma.objects.select_related("disciplina", "periodo", "professor")
    if eh_coordenador(usuario):
        return base
    return base.filter(professor__perfil__usuario=usuario)


def diarios_visiveis(usuario):
    """Registros de diário das turmas que o usuário pode ver."""
    return Diario.objects.filter(turma__in=turmas_visiveis(usuario).values("pk"))
