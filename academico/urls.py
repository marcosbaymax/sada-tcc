from django.urls import path

from . import views

urlpatterns = [
    path("", views.PainelView.as_view(), name="painel"),
    path("consulta/", views.consulta, name="consulta"),
    path("estudantes/<str:matricula>/", views.historico, name="historico"),
    path("divergencias/", views.DivergenciasView.as_view(), name="divergencias"),
    path("exportar/<str:formato>/", views.ExportarView.as_view(), name="exportar"),
]
