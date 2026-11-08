"""Visões do SADA: painel, consulta, histórico, divergências e exportações."""
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView

from painel import graficos, indicadores
from painel.consultas import carregar_tabelas, filtrar_diarios, registros

from . import exportacao, services
from .forms import FiltroDesempenhoForm


def _filtros(request):
    form = FiltroDesempenhoForm(request.GET or None)
    return form, (form.cleaned_data if form.is_valid() else {})


def _base_analitica(request, filtros):
    """Carrega os dados visíveis ao usuário (RN07) e aplica os filtros (RF06)."""
    qs = filtrar_diarios(services.diarios_visiveis(request.user), filtros)
    t = carregar_tabelas(qs)
    if t["diario"].empty:
        return t, None
    df = indicadores.filtrar_situacao(indicadores.preparar(t), filtros.get("situacao"))
    return t, df


class CoordenadorRequerido(UserPassesTestMixin):
    def test_func(self):
        return services.eh_coordenador(self.request.user)


class PainelView(LoginRequiredMixin, TemplateView):
    """RF07: cartões de indicadores e gráficos interativos."""
    template_name = "painel/painel.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        form, filtros = _filtros(self.request)
        t, df = _base_analitica(self.request, filtros)
        vazio = df is None or df.empty
        ctx.update(form=form, vazio=vazio)
        if not vazio:
            ctx.update(kpis=indicadores.kpis(df),
                       g_aprovacao=graficos.grafico_aprovacao(df),
                       g_evolucao=graficos.grafico_evolucao(df),
                       g_distribuicao=graficos.grafico_distribuicao(df))
            if services.eh_coordenador(self.request.user):
                ctx["g_coortes"] = graficos.grafico_coortes(t)
        return ctx


@login_required
def consulta(request):
    """RF06 e RF08: consulta paginada com filtros e destaque do nível de risco."""
    form, filtros = _filtros(request)
    t, df = _base_analitica(request, filtros)
    linhas = []
    if df is not None and not df.empty:
        df = df.sort_values(["ano", "semestre", "matricula", "codigodisciplina"],
                            ascending=[False, False, True, True])
        linhas = registros(df, ["matricula", "nomealuno", "nomedisciplina", "periodo", "media",
                                "frequencia", "resultado", "risco"])
    pagina = Paginator(linhas, 50).get_page(request.GET.get("pagina"))
    return render(request, "painel/consulta.html", {"form": form, "pagina": pagina})


@login_required
def historico(request, matricula):
    """RF05: histórico do estudante e coeficiente de rendimento (RN05)."""
    qs = services.diarios_visiveis(request.user).filter(aluno__matricula=matricula)
    t = carregar_tabelas(qs)
    if t["diario"].empty:
        raise Http404("Estudante inexistente ou fora do seu escopo.")
    df = indicadores.preparar(t)
    cr = indicadores.cr_por_aluno(df)
    ctx = {"matricula": matricula, "nome": df["nomealuno"].iloc[0],
           "historico": registros(indicadores.historico_aluno(df, matricula)),
           "cr": None if cr.empty else cr["cr"].iloc[0]}
    return render(request, "painel/historico.html", ctx)


class DivergenciasView(LoginRequiredMixin, CoordenadorRequerido, TemplateView):
    """Controle de qualidade: diários cujo resultado armazenado difere do recalculado."""
    template_name = "painel/divergencias.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        t = carregar_tabelas(services.diarios_visiveis(self.request.user))
        d = indicadores.divergencias_resultado(indicadores.preparar(t))
        ctx.update(total=len(d), divergencias=registros(d.head(200)))
        return ctx


class ExportarView(LoginRequiredMixin, View):
    """RF09: exportação do resultado filtrado em CSV ou PDF."""
    CABECALHO = ["Matrícula", "Estudante", "Disciplina", "Período", "Média",
                 "Frequência (%)", "Resultado", "Risco"]

    def get(self, request, formato):
        if formato not in ("csv", "pdf"):
            raise Http404("Formato de exportação inexistente.")
        _, filtros = _filtros(request)
        _, df = _base_analitica(request, filtros)
        colunas = ["matricula", "nomealuno", "nomedisciplina", "periodo", "media",
                   "frequencia", "resultado", "risco"]
        linhas = [] if df is None else [
            ["" if r[c] is None else r[c] for c in colunas]
            for r in registros(df.head(2000), colunas)]
        if formato == "csv":
            resp = HttpResponse(exportacao.gerar_csv(self.CABECALHO, linhas),
                                content_type="text/csv; charset=utf-8")
        else:
            resp = HttpResponse(exportacao.gerar_pdf("Relatório de desempenho",
                                                     self.CABECALHO, linhas),
                                content_type="application/pdf")
        resp["Content-Disposition"] = f'attachment; filename="desempenho.{formato}"'
        return resp
