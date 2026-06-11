from django.urls import path
from . import views

app_name = 'painel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('produtos/', views.produtos_lista, name='produtos_lista'),
    path('produtos/novo/', views.produto_criar, name='produto_criar'),
    path('produtos/<int:produto_id>/editar/', views.produto_editar, name='produto_editar'),
    path('produtos/<int:produto_id>/deletar/', views.produto_deletar, name='produto_deletar'),

    path('categorias/', views.categorias_lista, name='categorias_lista'),
    path('categorias/nova/', views.categoria_criar, name='categoria_criar'),
    path('categorias/<int:categoria_id>/editar/', views.categoria_editar, name='categoria_editar'),
    path('categorias/<int:categoria_id>/deletar/', views.categoria_deletar, name='categoria_deletar'),

    path('pedidos/', views.pedidos_lista, name='pedidos_lista'),
    path('pedidos/<int:pedido_id>/', views.pedido_detalhe, name='pedido_detalhe'),
    path('pedidos/<int:pedido_id>/rastreio/', views.salvar_rastreio, name='salvar_rastreio'),
    path('produtos/<int:produto_id>/imagens/', views.produto_imagens, name='produto_imagens'),
    path('produtos/<int:produto_id>/imagens/ordem/', views.salvar_ordem_imagens, name='salvar_ordem_imagens'),

    path('cupons/', views.cupons_lista, name='cupons_lista'),
    path('cupons/criar/', views.cupom_criar, name='cupom_criar'),
    path('cupons/<int:cupom_id>/editar/', views.cupom_editar, name='cupom_editar'),
    path('cupons/<int:cupom_id>/deletar/', views.cupom_deletar, name='cupom_deletar'),
    path('cupons/<int:cupom_id>/toggle/', views.cupom_toggle, name='cupom_toggle'),

    path('feedbacks/', views.feedbacks_lista, name='feedbacks_lista'),
]