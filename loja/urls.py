from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'loja'

urlpatterns = [
    
    path('', views.home, name='home'),
    path('produtos/', views.lista_produtos, name='lista_produtos'),
    path('produto/<slug:slug>/', views.detalhe_produto, name='detalhe_produto'),
    path('carrinho/', views.carrinho, name='carrinho'),
    path('carrinho/adicionar/<int:produto_id>/', views.adicionar_carrinho, name='adicionar_carrinho'),
    path('checkout/', views.checkout, name='checkout'),
    path('pedido-confirmado/', views.pedido_confirmado, name='pedido_confirmado'),
    path('sobre/', views.sobre, name='sobre'),
    path('contato/', views.contato, name='contato'),
    path('meus-pedidos/', views.historico_pedidos, name='historico_pedidos'),
    path('login/', auth_views.LoginView.as_view(template_name='loja/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='loja:home'), name='logout'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('favorito/<int:produto_id>/', views.toggle_favorito, name='toggle_favorito'),
    path('favoritos/', views.meus_favoritos, name='meus_favoritos'),
    path('enviar-rastreio/<int:pedido_id>/', views.enviar_rastreio, name='enviar_rastreio'),
    path('avaliar/<int:produto_id>/', views.avaliar_produto, name='avaliar_produto'),
    path('carrinho/remover/<str:chave>/', views.remover_carrinho, name='remover_carrinho'),
    path('carrinho/remover-um/<str:chave>/', views.remover_um_carrinho, name='remover_um_carrinho'),
    path('feedback/', views.feedback, name='feedback'),
    path('aviso-estoque/<int:produto_id>/', views.aviso_estoque, name='aviso_estoque'),
    path('pedido/sucesso/', views.pagamento_sucesso, name='pagamento_sucesso'),
    path('pedido/falha/', views.pagamento_falha, name='pagamento_falha'),
    path('pedido/pendente/', views.pagamento_pendente, name='pagamento_pendente'),
]