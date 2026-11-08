"""Gráficos interativos do painel (Plotly)."""
import plotly.graph_objects as go

from painel import indicadores

AZUL, VERMELHO, CINZA, VERDE = "#1F4E79", "#C0504D", "#7F7F7F", "#4F7F52"


def _html(fig, altura: int = 340, incluir_js: bool = False) -> str:
    """Serializa a figura como fragmento HTML; a biblioteca JS é incluída uma só vez."""
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=altura,
                      template="plotly_white")
    return fig.to_html(full_html=False, include_plotlyjs="cdn" if incluir_js else False)


def grafico_aprovacao(df) -> str:
    d = indicadores.aprovacao_por_disciplina(df)
    # destaque: disciplinas com aprovação 5 pontos percentuais abaixo da taxa global
    limiar = (indicadores.kpis(df)["taxa_aprovacao"] or 0) - 5
    cores = [VERMELHO if v < limiar else AZUL for v in d["taxa_aprovacao"]]
    fig = go.Figure(go.Bar(x=d["taxa_aprovacao"], y=d["nomedisciplina"], orientation="h",
                           marker_color=cores, customdata=d["periodocurricular"],
                           hovertemplate="%{y}<br>%{x:.1f}% (%{customdata}º período)"
                                         "<extra></extra>"))
    fig.update_layout(title="Taxa de aprovação por disciplina (%)",
                      yaxis=dict(autorange="reversed"))
    return _html(fig, altura=max(340, 18 * len(d) + 80), incluir_js=True)


def grafico_evolucao(df) -> str:
    e = indicadores.evolucao_por_periodo(df)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=e["periodo"], y=e["taxa_aprovacao"], mode="lines+markers",
                             name="Aprovação (%)", line=dict(color=AZUL)))
    fig.add_trace(go.Scatter(x=e["periodo"], y=e["frequencia"], mode="lines+markers",
                             name="Frequência (%)", line=dict(color=VERMELHO)))
    fig.update_layout(title="Evolução por período letivo")
    return _html(fig)


def grafico_distribuicao(df) -> str:
    d = indicadores.distribuicao_notas(df)
    fig = go.Figure(go.Bar(x=d["faixa"], y=d["quantidade"], marker_color=AZUL))
    fig.update_layout(title="Distribuição das médias do semestre")
    return _html(fig)


def grafico_coortes(t) -> str:
    c = indicadores.situacao_por_coorte(t)
    fig = go.Figure()
    for coluna, cor in (("Concluído", VERDE), ("Ativo", AZUL), ("Trancado", CINZA),
                        ("Evadido", VERMELHO)):
        fig.add_trace(go.Bar(x=c["coorte"], y=c[coluna], name=coluna, marker_color=cor))
    fig.update_layout(barmode="stack", title="Situação atual por coorte de ingresso")
    return _html(fig)
