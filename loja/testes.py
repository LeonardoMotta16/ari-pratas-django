"""
Suite de Testes — Pratas da Ari
================================
Cobre: models, carrinho (sessão), checkout, cupons, favoritos,
autenticação, avaliações, feedback, segurança (IDOR, abuso de cupom).

Como rodar:
    python manage.py test loja --verbosity=2

Requisito: o arquivo deve ficar em  loja/tests.py
"""

import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from loja.models import (
    Avaliacao,
    Categoria,
    Cupom,
    CupomUsado,
    Favorito,
    Feedback,
    ImagemProduto,
    ItemPedido,
    Pedido,
    Produto,
)


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def make_categoria(nome="Anéis"):
    return Categoria.objects.create(nome=nome)


def make_produto(nome="Anel de Prata", preco=150, preco_original=200,
                 disponivel=True, destaque=False, novo=False,
                 fora_estoque=False, categoria=None):
    return Produto.objects.create(
        nome=nome,
        preco=Decimal(str(preco)),
        preco_original=Decimal(str(preco_original)),
        disponivel=disponivel,
        destaque=destaque,
        novo=novo,
        fora_estoque=fora_estoque,
        categoria=categoria,
    )


def make_user(email="cliente@example.com", password="senha123"):
    return User.objects.create_user(
        username=email, email=email, password=password
    )


def make_pedido(nome="Maria", email="maria@example.com",
                total=150, usuario=None):
    return Pedido.objects.create(
        nome=nome,
        email=email,
        endereco="Rua X, 1",
        total=Decimal(str(total)),
        usuario=usuario,
    )


# ──────────────────────────────────────────────
# 1. MODELS
# ──────────────────────────────────────────────

class CategoriaModelTest(TestCase):
    def test_slug_gerado_automaticamente(self):
        c = Categoria.objects.create(nome="Colares de Prata")
        self.assertEqual(c.slug, "colares-de-prata")

    def test_str(self):
        c = make_categoria("Brincos")
        self.assertEqual(str(c), "Brincos")


class ProdutoModelTest(TestCase):
    def test_slug_gerado_automaticamente(self):
        p = make_produto("Pulseira Fina")
        self.assertEqual(p.slug, "pulseira-fina")

    def test_preco_final_sem_promocao(self):
        p = make_produto(preco=100, preco_original=200)
        p.promocao_ativa = False
        self.assertEqual(p.preco_final, Decimal("200"))

    def test_preco_final_com_promocao(self):
        p = make_produto(preco=100, preco_original=200)
        p.promocao_ativa = True
        self.assertEqual(p.preco_final, Decimal("100"))

    def test_desconto_calculado(self):
        p = make_produto(preco=150, preco_original=200)
        self.assertEqual(p.desconto(), 25)

    def test_desconto_sem_preco_original(self):
        p = make_produto()
        p.preco_original = None
        self.assertIsNone(p.desconto())

    def test_str(self):
        p = make_produto("Colar Star")
        self.assertEqual(str(p), "Colar Star")

    def test_imagem_principal_retorna_none_sem_imagens(self):
        p = make_produto()
        self.assertIsNone(p.imagem_principal())


class PedidoModelTest(TestCase):
    def test_str(self):
        pedido = make_pedido(nome="Ana")
        self.assertIn("Ana", str(pedido))
        self.assertIn(str(pedido.id), str(pedido))

    def test_total_correto(self):
        pedido = make_pedido(total=299.90)
        self.assertEqual(pedido.total, Decimal("299.90"))


class ItemPedidoModelTest(TestCase):
    def test_preco_total(self):
        p = make_produto()
        pedido = make_pedido()
        item = ItemPedido.objects.create(
            pedido=pedido,
            produto=p,
            quantidade=3,
            preco_unitario=Decimal("50.00"),
        )
        self.assertEqual(item.preco_total, Decimal("150.00"))


class CupomModelTest(TestCase):
    def test_str(self):
        c = Cupom.objects.create(codigo="PROMO10", desconto=10)
        self.assertIn("PROMO10", str(c))
        self.assertIn("10", str(c))

    def test_criado_como_ativo(self):
        c = Cupom.objects.create(codigo="ATIVO", desconto=5)
        self.assertTrue(c.ativo)


class FavoritoModelTest(TestCase):
    def test_str(self):
        u = make_user()
        p = make_produto()
        f = Favorito.objects.create(usuario=u, produto=p)
        self.assertIn(p.nome, str(f))

    def test_unique_together(self):
        u = make_user()
        p = make_produto()
        Favorito.objects.create(usuario=u, produto=p)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Favorito.objects.create(usuario=u, produto=p)


class AvaliacaoModelTest(TestCase):
    def test_str(self):
        u = make_user()
        p = make_produto()
        a = Avaliacao.objects.create(produto=p, usuario=u, estrelas=5)
        self.assertIn("5", str(a))


# ──────────────────────────────────────────────
# 2. VIEWS — HOME E LISTAGEM
# ──────────────────────────────────────────────

class HomeViewTest(TestCase):
    def test_home_retorna_200(self):
        r = self.client.get(reverse("loja:home"))
        self.assertEqual(r.status_code, 200)

    def test_destaques_aparecem_na_home(self):
        p = make_produto("Destaque", destaque=True)
        r = self.client.get(reverse("loja:home"))
        self.assertContains(r, "Destaque")

    def test_produto_indisponivel_nao_aparece_em_destaques(self):
        make_produto("Invisível", destaque=True, disponivel=False)
        r = self.client.get(reverse("loja:home"))
        self.assertNotContains(r, "Invisível")


class ListaProdutosViewTest(TestCase):
    def setUp(self):
        self.cat = make_categoria("Anéis")
        self.p1 = make_produto("Anel A", categoria=self.cat)
        self.p2 = make_produto("Pulseira B", preco=80, preco_original=80)

    def test_lista_retorna_200(self):
        r = self.client.get(reverse("loja:lista_produtos"))
        self.assertEqual(r.status_code, 200)

    def test_busca_por_nome(self):
        r = self.client.get(reverse("loja:lista_produtos"), {"busca": "Anel"})
        self.assertContains(r, "Anel A")
        self.assertNotContains(r, "Pulseira B")

    def test_filtro_por_categoria(self):
        r = self.client.get(
            reverse("loja:lista_produtos"), {"categoria": self.cat.slug}
        )
        self.assertContains(r, "Anel A")
        self.assertNotContains(r, "Pulseira B")

    def test_produto_indisponivel_nao_aparece(self):
        make_produto("Fora de Linha", disponivel=False)
        r = self.client.get(reverse("loja:lista_produtos"))
        self.assertNotContains(r, "Fora de Linha")


class DetalheProdutoViewTest(TestCase):
    def test_detalhe_produto_retorna_200(self):
        p = make_produto()
        r = self.client.get(
            reverse("loja:detalhe_produto", kwargs={"slug": p.slug})
        )
        self.assertEqual(r.status_code, 200)

    def test_produto_indisponivel_retorna_404(self):
        p = make_produto(disponivel=False)
        r = self.client.get(
            reverse("loja:detalhe_produto", kwargs={"slug": p.slug})
        )
        self.assertEqual(r.status_code, 404)


# ──────────────────────────────────────────────
# 3. CARRINHO (sessão)
# ──────────────────────────────────────────────

class CarrinhoViewTest(TestCase):
    def setUp(self):
        self.produto = make_produto(preco=100, preco_original=100)

    def test_carrinho_vazio_retorna_200(self):
        r = self.client.get(reverse("loja:carrinho"))
        self.assertEqual(r.status_code, 200)

    def test_adicionar_produto_ao_carrinho(self):
        r = self.client.post(
            reverse("loja:adicionar_carrinho",
                    kwargs={"produto_id": self.produto.id})
        )
        self.assertEqual(r.status_code, 302)
        self.assertIn(str(self.produto.id), self.client.session["carrinho"])

    def test_adicionar_via_ajax_retorna_json(self):
        r = self.client.post(
            reverse("loja:adicionar_carrinho",
                    kwargs={"produto_id": self.produto.id}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.content)
        self.assertTrue(data["ok"])
        self.assertEqual(data["total"], 1)

    def test_adicionar_mesmo_produto_incrementa_quantidade(self):
        url = reverse("loja:adicionar_carrinho",
                      kwargs={"produto_id": self.produto.id})
        self.client.post(url)
        self.client.post(url)
        carrinho = self.client.session["carrinho"]
        chave = str(self.produto.id)
        self.assertEqual(carrinho[chave]["quantidade"], 2)

    def test_remover_produto_do_carrinho(self):
        self.client.post(
            reverse("loja:adicionar_carrinho",
                    kwargs={"produto_id": self.produto.id})
        )
        chave = str(self.produto.id)
        self.client.get(
            reverse("loja:remover_carrinho", kwargs={"chave": chave})
        )
        self.assertNotIn(chave, self.client.session.get("carrinho", {}))

    def test_remover_um_decrementa_quantidade(self):
        url = reverse("loja:adicionar_carrinho",
                      kwargs={"produto_id": self.produto.id})
        self.client.post(url)
        self.client.post(url)
        chave = str(self.produto.id)
        self.client.get(
            reverse("loja:remover_um_carrinho", kwargs={"chave": chave})
        )
        self.assertEqual(
            self.client.session["carrinho"][chave]["quantidade"], 1
        )

    def test_remover_um_quando_quantidade_1_remove_item(self):
        self.client.post(
            reverse("loja:adicionar_carrinho",
                    kwargs={"produto_id": self.produto.id})
        )
        chave = str(self.produto.id)
        self.client.get(
            reverse("loja:remover_um_carrinho", kwargs={"chave": chave})
        )
        self.assertNotIn(chave, self.client.session.get("carrinho", {}))

    def test_produto_fora_estoque_nao_adiciona_ajax(self):
        p = make_produto("Anel Fora de Estoque", fora_estoque=True, preco=100, preco_original=100)
        r = self.client.post(
            reverse("loja:adicionar_carrinho",
                    kwargs={"produto_id": p.id}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(r.status_code, 400)
        data = json.loads(r.content)
        self.assertFalse(data["ok"])

    def test_adicionar_com_tamanho_cria_chave_diferente(self):
        url = reverse("loja:adicionar_carrinho",
                      kwargs={"produto_id": self.produto.id})
        self.client.post(url, {"tamanho": "P"})
        self.client.post(url, {"tamanho": "G"})
        carrinho = self.client.session["carrinho"]
        self.assertIn(f"{self.produto.id}_P", carrinho)
        self.assertIn(f"{self.produto.id}_G", carrinho)


# ──────────────────────────────────────────────
# 4. CUPONS
# ──────────────────────────────────────────────

class CupomTest(TestCase):
    def setUp(self):
        self.produto = make_produto(preco=100, preco_original=100)
        self.url_adicionar = reverse(
            "loja:adicionar_carrinho",
            kwargs={"produto_id": self.produto.id}
        )
        self.url_carrinho = reverse("loja:carrinho")

    def _adicionar_produto(self):
        self.client.post(self.url_adicionar)

    def test_cupom_valido_aplica_desconto(self):
        Cupom.objects.create(codigo="DESC10", desconto=10)
        self._adicionar_produto()
        r = self.client.post(self.url_carrinho, {"cupom": "DESC10"})
        self.assertContains(r, "DESC10")

    def test_cupom_invalido_exibe_erro(self):
        self._adicionar_produto()
        r = self.client.post(self.url_carrinho, {"cupom": "INEXISTENTE"})
        self.assertContains(r, "inválido")

    def test_cupom_inativo_rejeitado(self):
        Cupom.objects.create(codigo="INATIVO", desconto=20, ativo=False)
        self._adicionar_produto()
        r = self.client.post(self.url_carrinho, {"cupom": "INATIVO"})
        self.assertContains(r, "inválido")

    def test_cupom_ja_usado_pelo_usuario_rejeitado(self):
        user = make_user()
        cupom = Cupom.objects.create(codigo="USADO", desconto=15)
        CupomUsado.objects.create(cupom=cupom, usuario=user)
        self.client.force_login(user)
        self._adicionar_produto()
        r = self.client.post(self.url_carrinho, {"cupom": "USADO"})
        self.assertContains(r, "já utilizou")

    def test_cupom_pode_ser_usado_por_outro_usuario(self):
        """Cupom não-global não impede outro usuário de usar."""
        user1 = make_user("u1@x.com")
        user2 = make_user("u2@x.com")
        cupom = Cupom.objects.create(codigo="COMP10", desconto=10)
        CupomUsado.objects.create(cupom=cupom, usuario=user1)
        self.client.force_login(user2)
        self._adicionar_produto()
        r = self.client.post(self.url_carrinho, {"cupom": "COMP10"})
        self.assertContains(r, "COMP10")


# ──────────────────────────────────────────────
# 5. CHECKOUT
# ──────────────────────────────────────────────

class CheckoutViewTest(TestCase):
    def setUp(self):
        self.produto = make_produto(preco=120, preco_original=120)
        self.client.post(
            reverse("loja:adicionar_carrinho",
                    kwargs={"produto_id": self.produto.id})
        )
        self.url = reverse("loja:checkout")
        self.dados_validos = {
            "nome": "João",
            "sobrenome": "Silva",
            "email": "joao@example.com",
            "Telefone": "11999999999",
            "cep": "01310-100",
            "rua": "Av. Paulista",
            "numero": "1000",
            "complemento": "",
            "bairro": "Bela Vista",
            "cidade": "São Paulo",
            "estado": "SP",
        }

    def test_checkout_get_retorna_200(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)

    def test_checkout_carrinho_vazio_redireciona(self):
        session = self.client.session
        session['carrinho'] = {}
        session.save()
        r = self.client.get(self.url)
        self.assertRedirects(r, reverse("loja:carrinho"))

    def test_checkout_valido_cria_pedido(self):
        antes = Pedido.objects.count()
        self.client.post(self.url, self.dados_validos)
        self.assertEqual(Pedido.objects.count(), antes + 1)

    def test_checkout_valido_redireciona_para_confirmado(self):
        r = self.client.post(self.url, self.dados_validos)
        self.assertRedirects(r, reverse("loja:pedido_confirmado"))

    def test_checkout_valido_limpa_carrinho(self):
        self.client.post(self.url, self.dados_validos)
        self.assertEqual(self.client.session.get("carrinho", {}), {})

    def test_checkout_campos_obrigatorios(self):
        r = self.client.post(self.url, {
            "nome": "", "sobrenome": "", "email": "",
            "Telefone": "", "cep": "", "rua": "",
            "numero": "", "bairro": "", "cidade": "", "estado": "",
        })
        self.assertContains(r, "obrigatório")

    def test_checkout_sem_nome_exibe_erro(self):
        dados = {**self.dados_validos, "nome": ""}
        r = self.client.post(self.url, dados)
        self.assertContains(r, "Nome")

    def test_checkout_cria_itens_pedido(self):
        self.client.post(self.url, self.dados_validos)
        pedido = Pedido.objects.last()
        self.assertEqual(pedido.itens.count(), 1)
        self.assertEqual(pedido.itens.first().produto, self.produto)

    def test_checkout_total_correto(self):
        self.client.post(self.url, self.dados_validos)
        pedido = Pedido.objects.last()
        self.assertEqual(pedido.total, Decimal("120"))

    def test_checkout_com_criar_conta_cria_usuario(self):
        dados = {**self.dados_validos,
                 "criar_conta": "on", "senha": "minhasenha123"}
        self.client.post(self.url, dados)
        self.assertTrue(
            User.objects.filter(username="joao@example.com").exists()
        )

    def test_checkout_usuario_logado_vincula_pedido(self):
        user = make_user("comprador@x.com")
        self.client.force_login(user)
        dados = {**self.dados_validos, "email": "comprador@x.com"}
        self.client.post(self.url, dados)
        pedido = Pedido.objects.last()
        self.assertEqual(pedido.usuario, user)

    def test_checkout_com_cupom_aplica_desconto_no_total(self):
        Cupom.objects.create(codigo="DESC20", desconto=20)
        # aplica cupom na sessão
        self.client.post(reverse("loja:carrinho"), {"cupom": "DESC20"})
        self.client.post(self.url, self.dados_validos)
        pedido = Pedido.objects.last()
        # 120 - 20% = 96
        self.assertEqual(pedido.total, Decimal("96.00"))

    def test_checkout_com_cupom_marca_como_usado(self):
        user = make_user("fiel@x.com")
        self.client.force_login(user)
        cupom = Cupom.objects.create(codigo="CUPOMFIEL", desconto=10)
        self.client.post(reverse("loja:carrinho"), {"cupom": "CUPOMFIEL"})
        dados = {**self.dados_validos, "email": "fiel@x.com"}
        self.client.post(self.url, dados)
        self.assertTrue(
            CupomUsado.objects.filter(cupom=cupom, usuario=user).exists()
        )


# ──────────────────────────────────────────────
# 6. AUTENTICAÇÃO — CADASTRO E LOGIN
# ──────────────────────────────────────────────

class CadastroViewTest(TestCase):
    url = "/cadastro/"

    def test_get_retorna_200(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)

    def test_cadastro_valido_cria_usuario(self):
        self.client.post(self.url, {
            "email": "novo@x.com",
            "first_name": "Novo",
            "last_name": "User",
            "password1": "senha12345",
            "password2": "senha12345",
        })
        self.assertTrue(User.objects.filter(email="novo@x.com").exists())

    def test_cadastro_email_duplicado_exibe_erro(self):
        make_user("dup@x.com")
        r = self.client.post(self.url, {
            "email": "dup@x.com",
            "first_name": "A",
            "last_name": "B",
            "password1": "senha12345",
            "password2": "senha12345",
        })
        self.assertContains(r, "cadastrado")

    def test_cadastro_senhas_diferentes_exibe_erro(self):
        r = self.client.post(self.url, {
            "email": "x@x.com",
            "first_name": "A",
            "last_name": "B",
            "password1": "abc",
            "password2": "xyz",
        })
        self.assertContains(r, "coincidem")

    def test_cadastro_vincula_pedidos_anteriores(self):
        make_pedido(email="novo2@x.com")
        self.client.post(self.url, {
            "email": "novo2@x.com",
            "first_name": "N",
            "last_name": "U",
            "password1": "senha12345",
            "password2": "senha12345",
        })
        user = User.objects.get(email="novo2@x.com")
        self.assertTrue(Pedido.objects.filter(usuario=user).exists())


# ──────────────────────────────────────────────
# 7. FAVORITOS
# ──────────────────────────────────────────────

class FavoritosViewTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.produto = make_produto()

    def test_toggle_adiciona_favorito(self):
        self.client.force_login(self.user)
        self.client.get(
            reverse("loja:toggle_favorito",
                    kwargs={"produto_id": self.produto.id}),
            {"next": "/"},
        )
        self.assertTrue(
            Favorito.objects.filter(
                usuario=self.user, produto=self.produto
            ).exists()
        )

    def test_toggle_remove_favorito_existente(self):
        Favorito.objects.create(usuario=self.user, produto=self.produto)
        self.client.force_login(self.user)
        self.client.get(
            reverse("loja:toggle_favorito",
                    kwargs={"produto_id": self.produto.id}),
            {"next": "/"},
        )
        self.assertFalse(
            Favorito.objects.filter(
                usuario=self.user, produto=self.produto
            ).exists()
        )

    def test_favorito_requer_login(self):
        r = self.client.get(
            reverse("loja:toggle_favorito",
                    kwargs={"produto_id": self.produto.id})
        )
        self.assertRedirects(r, f"/login/?next=/favorito/{self.produto.id}/",
                             fetch_redirect_response=False)

    def test_lista_favoritos_retorna_200(self):
        self.client.force_login(self.user)
        r = self.client.get(reverse("loja:meus_favoritos"))
        self.assertEqual(r.status_code, 200)

    def test_lista_favoritos_requer_login(self):
        r = self.client.get(reverse("loja:meus_favoritos"))
        self.assertEqual(r.status_code, 302)


# ──────────────────────────────────────────────
# 8. AVALIAÇÕES
# ──────────────────────────────────────────────

class AvaliacaoViewTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.produto = make_produto()

    def _comprar(self):
        pedido = make_pedido(email=self.user.email, usuario=self.user)
        ItemPedido.objects.create(
            pedido=pedido,
            produto=self.produto,
            quantidade=1,
            preco_unitario=Decimal("100"),
        )

    def test_avaliar_requer_login(self):
        r = self.client.post(
            reverse("loja:avaliar_produto",
                    kwargs={"produto_id": self.produto.id}),
            {"estrelas": 5},
        )
        self.assertRedirects(
            r,
            f"/login/?next=/avaliar/{self.produto.id}/",
            fetch_redirect_response=False,
        )

    def test_avaliar_sem_compra_redireciona(self):
        self.client.force_login(self.user)
        r = self.client.post(
            reverse("loja:avaliar_produto",
                    kwargs={"produto_id": self.produto.id}),
            {"estrelas": 5},
        )
        self.assertRedirects(
            r,
            reverse("loja:detalhe_produto", kwargs={"slug": self.produto.slug}),
        )
        self.assertFalse(Avaliacao.objects.exists())

    def test_avaliar_apos_compra_cria_avaliacao(self):
        self._comprar()
        self.client.force_login(self.user)
        self.client.post(
            reverse("loja:avaliar_produto",
                    kwargs={"produto_id": self.produto.id}),
            {"estrelas": 4, "comentario": "Ótimo produto!"},
        )
        av = Avaliacao.objects.filter(produto=self.produto, usuario=self.user)
        self.assertTrue(av.exists())
        self.assertEqual(av.first().estrelas, 4)

    def test_avaliar_duas_vezes_atualiza(self):
        self._comprar()
        self.client.force_login(self.user)
        url = reverse("loja:avaliar_produto",
                      kwargs={"produto_id": self.produto.id})
        self.client.post(url, {"estrelas": 3})
        self.client.post(url, {"estrelas": 5, "comentario": "Mudei de ideia"})
        av = Avaliacao.objects.get(produto=self.produto, usuario=self.user)
        self.assertEqual(av.estrelas, 5)
        self.assertEqual(Avaliacao.objects.filter(produto=self.produto).count(), 1)


# ──────────────────────────────────────────────
# 9. FEEDBACK
# ──────────────────────────────────────────────

class FeedbackViewTest(TestCase):
    url = "/feedback/"

    def test_get_retorna_200(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)

    def test_post_valido_cria_feedback(self):
        self.client.post(self.url, {
            "nome": "Maria",
            "email": "maria@x.com",
            "estrelas": "5",
            "mensagem": "Adorei!",
        })
        self.assertEqual(Feedback.objects.count(), 1)

    def test_post_via_ajax_retorna_json_ok(self):
        r = self.client.post(self.url, {
            "nome": "João",
            "email": "joao@x.com",
            "estrelas": "4",
            "mensagem": "Bom!",
        }, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(json.loads(r.content)["ok"])

    def test_post_incompleto_nao_cria_feedback(self):
        self.client.post(self.url, {"nome": "X"})
        self.assertEqual(Feedback.objects.count(), 0)

    def test_post_incompleto_ajax_retorna_erro(self):
        r = self.client.post(self.url, {"nome": "X"},
                             HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        data = json.loads(r.content)
        self.assertFalse(data["ok"])


# ──────────────────────────────────────────────
# 10. HISTÓRICO DE PEDIDOS
# ──────────────────────────────────────────────

class HistoricoPedidosViewTest(TestCase):
    def test_usuario_autenticado_ve_seus_pedidos(self):
        user = make_user()
        pedido = make_pedido(email=user.email, usuario=user)
        self.client.force_login(user)
        r = self.client.get(reverse("loja:historico_pedidos"))
        self.assertContains(r, str(pedido.id))

    def test_busca_por_email_retorna_pedidos(self):
        pedido = make_pedido(nome="Carol", email="carol@x.com")
        r = self.client.get(
            reverse("loja:historico_pedidos"), {"email": "carol@x.com"}
        )
        self.assertContains(r, f"Pedido #{pedido.id}")

    def test_usuario_nao_ve_pedidos_de_outro(self):
        u1 = make_user("a@x.com")
        u2 = make_user("b@x.com")
        make_pedido(email="a@x.com", usuario=u1)
        self.client.force_login(u2)
        r = self.client.get(reverse("loja:historico_pedidos"))
        # b@x.com não tem pedidos; lista deve estar vazia
        self.assertNotContains(r, "a@x.com")


# ──────────────────────────────────────────────
# 11. SEGURANÇA
# ──────────────────────────────────────────────

class SegurancaTest(TestCase):
    """Testa vulnerabilidades identificadas na auditoria."""

    # ── 11.1  IDOR em /meus-pedidos/ ──
    def test_historico_por_email_nao_exige_autenticacao_mas_expoe_dados(self):
        """
        Documenta o problema IDOR existente: qualquer pessoa pode ver pedidos
        de terceiros passando ?email=. Esse teste *confirma* o comportamento
        atual para que uma futura correção quebre o teste intencionalmente.
        """
        pedido = make_pedido(nome="Vítima", email="vitima@x.com")
        r = self.client.get(
            reverse("loja:historico_pedidos"),
            {"email": "vitima@x.com"},
        )
        # Atualmente o sistema RETORNA os dados — teste registra isso.
        self.assertContains(r, f"Pedido #{pedido.id}")

    # ── 11.2  Cupom não pode ser reutilizado ──
    def test_cupom_nao_pode_ser_usado_duas_vezes_mesmo_usuario(self):
        user = make_user()
        cupom = Cupom.objects.create(codigo="UNICO", desconto=10)
        CupomUsado.objects.create(cupom=cupom, usuario=user)
        self.client.force_login(user)
        produto = make_produto(preco=100, preco_original=100)
        self.client.post(
            reverse("loja:adicionar_carrinho",
                    kwargs={"produto_id": produto.id})
        )
        r = self.client.post(reverse("loja:carrinho"), {"cupom": "UNICO"})
        # cupom não deve aparecer aplicado
        session_cupom = self.client.session.get("cupom", "")
        self.assertEqual(session_cupom, "")

    # ── 11.3  Rastreio protegido para staff ──
    def test_enviar_rastreio_requer_staff(self):
        pedido = make_pedido()
        user = make_user()  # usuário comum
        self.client.force_login(user)
        r = self.client.get(
            reverse("loja:enviar_rastreio", kwargs={"pedido_id": pedido.id})
        )
        self.assertRedirects(r, reverse("loja:home"),
                             fetch_redirect_response=False)

    def test_enviar_rastreio_funciona_para_staff(self):
        pedido = make_pedido()
        pedido.codigo_rastreio = "BR123456789"
        pedido.save()
        staff = User.objects.create_user(
            username="staff@x.com", password="x", is_staff=True
        )
        self.client.force_login(staff)
        r = self.client.get(
            reverse("loja:enviar_rastreio", kwargs={"pedido_id": pedido.id})
        )
        self.assertEqual(r.status_code, 302)
        pedido.refresh_from_db()
        self.assertTrue(pedido.rastreio_enviado)

    # ── 11.4  Avaliar produto de outro usuário não é possível ──
    def test_usuario_nao_pode_avaliar_produto_que_nao_comprou(self):
        u1 = make_user("comprador@x.com")
        u2 = make_user("invasor@x.com")
        produto = make_produto()
        pedido = make_pedido(email=u1.email, usuario=u1)
        ItemPedido.objects.create(
            pedido=pedido, produto=produto,
            quantidade=1, preco_unitario=Decimal("100")
        )
        self.client.force_login(u2)
        self.client.post(
            reverse("loja:avaliar_produto",
                    kwargs={"produto_id": produto.id}),
            {"estrelas": 1, "comentario": "Ataque"},
        )
        self.assertFalse(
            Avaliacao.objects.filter(produto=produto, usuario=u2).exists()
        )

    # ── 11.5  CSRF habilitado ──
    def test_checkout_sem_csrf_retorna_403(self):
        produto = make_produto(preco=100, preco_original=100)
        self.client.post(
            reverse("loja:adicionar_carrinho",
                    kwargs={"produto_id": produto.id})
        )
        # cliente sem enforce_csrf_checks usa o client padrão (csrf ignorado)
        # Para testar de verdade, usamos o client com enforce_csrf_checks=True
        client_csrf = Client(enforce_csrf_checks=True)
        r = client_csrf.post(reverse("loja:checkout"), {
            "nome": "X", "sobrenome": "Y", "email": "x@x.com",
            "Telefone": "11999", "cep": "01000", "rua": "Rua",
            "numero": "1", "bairro": "B", "cidade": "C", "estado": "SP",
        })
        self.assertEqual(r.status_code, 403)


# ──────────────────────────────────────────────
# 12. PÁGINAS ESTÁTICAS
# ──────────────────────────────────────────────

class PaginasEstaticasTest(TestCase):
    def test_sobre_retorna_200(self):
        r = self.client.get(reverse("loja:sobre"))
        self.assertEqual(r.status_code, 200)

    def test_contato_retorna_200(self):
        r = self.client.get(reverse("loja:contato"))
        self.assertEqual(r.status_code, 200)

    def test_pedido_confirmado_retorna_200(self):
        r = self.client.get(reverse("loja:pedido_confirmado"))
        self.assertEqual(r.status_code, 200)