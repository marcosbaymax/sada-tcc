from django import forms

from .models import Disciplina, PeriodoLetivo


class FiltroDesempenhoForm(forms.Form):
    """Filtros da consulta (RF06): período, disciplina, situação e busca por estudante."""
    SITUACOES = [("", "Todas"), ("APROVADO", "Aprovado"),
                 ("REPROVADO_NOTA", "Reprovado por nota"),
                 ("REPROVADO_FALTA", "Reprovado por falta"), ("EM_CURSO", "Em curso"),
                 ("RISCO", "Em risco (qualquer nível)"), ("CRITICO", "Risco crítico"),
                 ("ATENCAO", "Risco de atenção")]
    periodo = forms.ModelChoiceField(PeriodoLetivo.objects.all(), required=False,
                                     empty_label="Todos os períodos")
    disciplina = forms.ModelChoiceField(Disciplina.objects.all(), required=False,
                                        empty_label="Todas as disciplinas")
    situacao = forms.ChoiceField(choices=SITUACOES, required=False)
    busca = forms.CharField(required=False, label="Estudante ou matrícula")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():   # classes do Bootstrap
            selecao = isinstance(campo.widget, forms.Select)
            campo.widget.attrs["class"] = "form-select" if selecao else "form-control"
        self.fields["busca"].widget.attrs["placeholder"] = "Estudante ou matrícula"
