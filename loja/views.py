from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Categoria, Produto, ImagemProduto, Pedido, ItemPedido, Favorito, Avaliacao, Cupom, CupomUsado, Feedback
from django.db import models
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
import uuid
from django.db.models import Case, When, F, DecimalField
import mercadopago


def preco_float(preco):
    try:
        return float(preco)
    except (TypeError, ValueError):
        return 0.0


def home(request):
    categorias = Categoria.objects.all()
    destaques = Produto.objects.filter(destaque=True, disponivel=True)[:8]
    novidades = Produto.objects.filter(novo=True, disponivel=True)[:4]
    return render(request, 'loja/home.html', {
        'categorias': categorias,
        'destaques': destaques,
        'novidades': novidades,
    })


def lista_produtos(request):
    produtos = Produto.objects.filter(disponivel=True)
    categorias = Categoria.objects.all()

    busca = request.GET.get('busca', '')
    if busca:
        produtos = produtos.filter(nome__icontains=busca)

    categoria_atual = request.GET.get('categoria', '')
    if categoria_atual:
        produtos = produtos.filter(categoria__slug=categoria_atual)

    ordem_atual = request.GET.get('ordem', 'novidade')
    if ordem_atual in ('menor_preco', 'maior_preco'):
        produtos = produtos.annotate(
            preco_efetivo=Case(
                When(promocao_ativa=True, preco__isnull=False, then=F('preco')),
                default=F('preco_original'),
                output_field=DecimalField(),
            )
        )
        if ordem_atual == 'menor_preco':
            produtos = produtos.order_by('preco_efetivo')
        else:
            produtos = produtos.order_by('-preco_efetivo')
    elif ordem_atual == 'nome':
        produtos = produtos.order_by('nome')
    else:
        produtos = produtos.order_by('-novo', '-id')

    favoritos_ids = []
    if request.user.is_authenticated:
        favoritos_ids = list(
            Favorito.objects.filter(usuario=request.user).values_list('produto_id', flat=True)
        )

    return render(request, 'loja/lista_produtos.html', {
        'produtos': produtos,
        'categorias': categorias,
        'busca': busca,
        'categoria_atual': categoria_atual,
        'ordem_atual': ordem_atual,
        'favoritos_ids': favoritos_ids,
    })


def detalhe_produto(request, slug):
    produto = get_object_or_404(Produto, slug=slug, disponivel=True)
    relacionados = Produto.objects.filter(
        categoria=produto.categoria, disponivel=True
    ).exclude(id=produto.id)[:4]

    avaliacoes = Avaliacao.objects.filter(produto=produto).select_related('usuario')
    media_estrelas = avaliacoes.aggregate(media=models.Avg('estrelas'))['media']

    comprou = False
    ja_avaliou = False
    minha_avaliacao = None
    if request.user.is_authenticated:
        comprou = ItemPedido.objects.filter(
            pedido__email=request.user.email,
            produto=produto
        ).exists()
        minha_avaliacao = avaliacoes.filter(usuario=request.user).first()
        ja_avaliou = minha_avaliacao is not None

    tamanhos = [t.strip() for t in produto.medidas.split(',')] if produto.medidas else []

    return render(request, 'loja/detalhe_produto.html', {
        'produto': produto,
        'relacionados': relacionados,
        'avaliacoes': avaliacoes,
        'media_estrelas': media_estrelas,
        'comprou': comprou,
        'ja_avaliou': ja_avaliou,
        'minha_avaliacao': minha_avaliacao,
        'tamanhos': tamanhos,
    })


def carrinho(request):
    carrinho = request.session.get('carrinho', {})
    total = sum(preco_float(item['preco']) * item['quantidade'] for item in carrinho.values())

    desconto = 0
    cupom_aplicado = request.session.get('cupom', '')
    cupom_erro = ''

    if request.method == 'POST':
        codigo = request.POST.get('cupom', '').strip().upper()
        try:
            cupom_obj = Cupom.objects.get(codigo=codigo, ativo=True)
            ja_usado = (
                request.user.is_authenticated and
                CupomUsado.objects.filter(cupom=cupom_obj, usuario=request.user).exists()
            )
            if ja_usado:
                request.session['cupom'] = ''
                cupom_aplicado = ''
                cupom_erro = 'Você já utilizou este cupom.'
            else:
                request.session['cupom'] = codigo
                cupom_aplicado = codigo
        except Cupom.DoesNotExist:
            request.session['cupom'] = ''
            cupom_aplicado = ''
            cupom_erro = 'Cupom inválido ou inativo.'

    # FIX: Identação e correção de sintaxe (faltava o `:` após o try)
    if cupom_aplicado:
        try:
            cupom_obj = Cupom.objects.get(codigo=cupom_aplicado, ativo=True)
            ja_usado = (
                request.user.is_authenticated and
                CupomUsado.objects.filter(cupom=cupom_obj, usuario=request.user).exists()
            )
            if ja_usado:
                request.session['cupom'] = ''
                cupom_aplicado = ''
            else:
                desconto = total * cupom_obj.desconto / 100
        except Cupom.DoesNotExist:
            request.session['cupom'] = ''
            cupom_aplicado = ''

    total_final = total - desconto

    return render(request, 'loja/carrinho.html', {
        'carrinho': carrinho,
        'total_final': total_final,
        'desconto': desconto,
        'cupom_aplicado': cupom_aplicado,
        'cupom_erro': cupom_erro,
    })


def sobre(request):
    return render(request, 'loja/sobre.html')


def contato(request):
    return render(request, 'loja/contato.html')


def adicionar_carrinho(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)

    if produto.fora_estoque:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'mensagem': 'Produto fora de estoque.'}, status=400)
        return redirect('loja:detalhe_produto', slug=produto.slug)

    carrinho = request.session.get('carrinho', {})
    tamanho = request.POST.get('tamanho', '')

    chave = f"{produto_id}_{tamanho}" if tamanho else str(produto_id)

    if chave in carrinho:
        carrinho[chave]['quantidade'] += 1
    else:
        carrinho[chave] = {
            'nome': produto.nome,
            'preco': str(produto.preco_final),
            'quantidade': 1,
            'tamanho': tamanho,
            'produto_id': produto_id,
        }
    request.session['carrinho'] = carrinho

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        total_itens = sum(item['quantidade'] for item in carrinho.values())
        return JsonResponse({
            'ok': True,
            'mensagem': f'{produto.nome} adicionado ao carrinho! 🛍️',
            'total': total_itens,
        })

    return redirect('loja:carrinho')


def remover_carrinho(request, chave):
    carrinho = request.session.get('carrinho', {})
    if chave in carrinho:
        del carrinho[chave]
    request.session['carrinho'] = carrinho
    return redirect('loja:carrinho')


def remover_um_carrinho(request, chave):
    carrinho = request.session.get('carrinho', {})
    if chave in carrinho:
        if carrinho[chave]['quantidade'] > 1:
            carrinho[chave]['quantidade'] -= 1
        else:
            del carrinho[chave]
    request.session['carrinho'] = carrinho
    return redirect('loja:carrinho')



def checkout(request):
    carrinho = request.session.get('carrinho', {})
    if not carrinho:
        return redirect('loja:carrinho')

    total = sum(preco_float(item['preco']) * item['quantidade'] for item in carrinho.values())
    desconto = 0
    cupom_aplicado = request.session.get('cupom', '')
    if cupom_aplicado:
        try:
            cupom_obj = Cupom.objects.get(codigo=cupom_aplicado, ativo=True)
            desconto = total * cupom_obj.desconto / 100
        except Cupom.DoesNotExist:
            request.session['cupom'] = ''
            cupom_aplicado = ''
    total_final = total - desconto
    erros = []

    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        sobrenome = request.POST.get('sobrenome', '').strip()
        email = request.POST.get('email', '').strip()
        telefone = request.POST.get('Telefone', '').strip()
        cep = request.POST.get('cep', '').strip()
        rua = request.POST.get('rua', '').strip()
        numero = request.POST.get('numero', '').strip()
        complemento = request.POST.get('complemento', '').strip()
        bairro = request.POST.get('bairro', '').strip()
        cidade = request.POST.get('cidade', '').strip()
        estado = request.POST.get('estado', '').strip()
        criar_conta = request.POST.get('criar_conta')
        senha = request.POST.get('senha', '').strip()

        if not nome:
            erros.append('Nome é obrigatório.')
        if not sobrenome:
            erros.append('Sobrenome é obrigatório.')
        if not email:
            erros.append('E-mail é obrigatório.')
        if not telefone:
            erros.append('Telefone é obrigatório.')
        if not cep:
            erros.append('CEP é obrigatório.')
        if not rua:
            erros.append('Rua é obrigatória.')
        if not numero:
            erros.append('Número é obrigatório.')
        if not bairro:
            erros.append('Bairro é obrigatório.')
        if not cidade:
            erros.append('Cidade é obrigatória.')
        if not estado:
            erros.append('Estado é obrigatório.')
        if criar_conta and not senha:
            erros.append('Escolha uma senha para criar sua conta.')

        if erros:
            return render(request, 'loja/checkout.html', {
                'carrinho': carrinho,
                'total': total_final,
                'desconto': desconto,
                'erros': erros,
                'post': request.POST,
            })

        nome_completo = f"{nome} {sobrenome}".strip()
        endereco = f"{rua}, {numero}{' - ' + complemento if complemento else ''} - {bairro} - {cidade}/{estado} - CEP: {cep}"

        if criar_conta and senha:
            from django.contrib.auth.models import User
            if not User.objects.filter(username=email).exists():
                user = User.objects.create_user(username=email, email=email, password=senha, first_name=nome_completo)
                login(request, user)
                Pedido.objects.filter(email=email, usuario=None).update(usuario=user)

        pedido = Pedido.objects.create(
            nome=nome_completo,
            email=email,
            telefone=telefone,
            endereco=endereco,
            total=total_final,
            usuario=request.user if request.user.is_authenticated else None,
        )

        for chave, item in carrinho.items():
            try:
                produto = Produto.objects.get(id=item['produto_id'])
                preco = preco_float(item['preco'])
                if preco <= 0:
                    continue
                ItemPedido.objects.create(
                    pedido=pedido,
                    produto=produto,
                    quantidade=item['quantidade'],
                    preco_unitario=preco,
                    tamanho=item.get('tamanho', ''),
                )
            except Produto.DoesNotExist:
                pass

        if request.user.is_authenticated:
            total_pedidos = Pedido.objects.filter(usuario=request.user).count()
            if total_pedidos > 0 and total_pedidos % 3 == 0:
                codigo = f"FIDELIDADE-{request.user.id}-{total_pedidos}-{uuid.uuid4().hex[:6].upper()}"
                Cupom.objects.create(
                    codigo=codigo,
                    desconto=20,
                    ativo=True,
                    fidelidade=True,
                    usuario=request.user,
                )
                try:
                    send_mail(
                        subject='🎉 Você ganhou um cupom de fidelidade! — Ari Pratas',
                        message=f'Olá! Seu cupom de fidelidade é: {codigo} — 20% de desconto.',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        fail_silently=True,
                    )
                except Exception:
                    pass

        cupom_usado = request.session.get('cupom', '')
        if cupom_usado:
            try:
                cupom_obj = Cupom.objects.get(codigo=cupom_usado, ativo=True)
                if request.user.is_authenticated:
                    CupomUsado.objects.get_or_create(cupom=cupom_obj, usuario=request.user)
                else:
                    cupom_obj.ativo = False
                    cupom_obj.save()
            except Cupom.DoesNotExist:
                pass
            request.session['cupom'] = ''

        request.session['carrinho'] = {}
        request.session['pedido_id'] = pedido.id

        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

        preference_data = {
            "items": [{
                "title": f"Pedido #{pedido.id} - Pratas da Ari",
                "quantity": 1,
                "unit_price": float(total_final),
                "currency_id": "BRL",
            }],
            "payer": {
                "name": nome_completo,
                "email": email,
            },
            "back_urls": {
                "success": "https://www.google.com",
                "failure": "https://www.google.com",
                "pending": "https://www.google.com",
            },
            "external_reference": str(pedido.id),
        }

        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]

        pedido.mp_preference_id = preference["id"]
        pedido.save()

        return redirect(preference["sandbox_init_point"])

    return render(request, 'loja/checkout.html', {
        'carrinho': carrinho,
        'total': total_final,
        'desconto': desconto,
        'erros': erros,
        'post': {},
    })


def cadastro(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        erros = []
        if not first_name:
            erros.append('Nome é obrigatório.')
        if not last_name:
            erros.append('Sobrenome é obrigatório.')
        if not email:
            erros.append('Email é obrigatório.')
        if not password1:
            erros.append('Senha é obrigatória.')
        if password1 != password2:
            erros.append('As senhas não coincidem.')

        from django.contrib.auth.models import User
        if User.objects.filter(username=email).exists():
            erros.append('Este email já está cadastrado.')

        if erros:
            return render(request, 'loja/cadastro.html', {'erros': erros, 'post': request.POST})

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
        )
        login(request, user)
        Pedido.objects.filter(email=email, usuario=None).update(usuario=user)
        return redirect('loja:home')

    return render(request, 'loja/cadastro.html', {'erros': [], 'post': {}})


@login_required(login_url='/login/')
def toggle_favorito(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    favorito, criado = Favorito.objects.get_or_create(usuario=request.user, produto=produto)
    if not criado:
        favorito.delete()
    next_url = request.GET.get('next', 'loja:lista_produtos')
    return redirect(next_url)


@login_required(login_url='/login/')
def meus_favoritos(request):
    favoritos = Favorito.objects.filter(usuario=request.user).select_related('produto')
    return render(request, 'loja/favoritos.html', {'favoritos': favoritos})


def enviar_rastreio(request, pedido_id):
    if not request.user.is_staff:
        return redirect('loja:home')

    pedido = get_object_or_404(Pedido, id=pedido_id)

    if pedido.codigo_rastreio and not pedido.rastreio_enviado:
        try:
            send_mail(
                subject=f'Seu pedido #{pedido.id} foi enviado! — Ari Pratas',
                message=f'''Olá, {pedido.nome}!

Seu pedido foi enviado e já está a caminho!

Código de rastreio: {pedido.codigo_rastreio}

Você pode rastrear seu pedido nos Correios:
https://www.correios.com.br/

Qualquer dúvida, entre em contato conosco.

Equipe Ari Pratas ✨''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[pedido.email],
                fail_silently=True,
            )
        except Exception:
            pass
        pedido.rastreio_enviado = True
        pedido.save()

    return redirect('/painel/pedidos/')


@login_required(login_url='/login/')
def avaliar_produto(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)

    comprou = ItemPedido.objects.filter(
        pedido__email=request.user.email,
        produto=produto
    ).exists()

    if not comprou:
        return redirect('loja:detalhe_produto', slug=produto.slug)

    if request.method == 'POST':
        estrelas = request.POST.get('estrelas')
        comentario = request.POST.get('comentario', '')

        if estrelas:
            foto = request.FILES.get('foto')
            defaults = {'estrelas': estrelas, 'comentario': comentario}
            if foto:
                defaults['foto'] = foto
            Avaliacao.objects.update_or_create(
                produto=produto,
                usuario=request.user,
                defaults=defaults
            )

    return redirect('loja:detalhe_produto', slug=produto.slug)


def feedback(request):
    enviado = False
    erro = ''

    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        email = request.POST.get('email', '').strip()
        estrelas = request.POST.get('estrelas', '')
        mensagem = request.POST.get('mensagem', '').strip()

        if not nome or not email or not estrelas or not mensagem:
            erro = 'Por favor, preencha todos os campos.'
        else:
            Feedback.objects.create(
                nome=nome,
                email=email,
                estrelas=estrelas,
                mensagem=mensagem,
            )
            enviado = True

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if enviado:
                return JsonResponse({'ok': True})
            else:
                return JsonResponse({'ok': False, 'erro': erro})

    return render(request, 'loja/feedback.html', {
        'enviado': enviado,
        'erro': erro,
    })


def pedido_confirmado(request):
    return render(request, 'loja/pedido_confirmado.html')


@login_required(login_url='/login/')
def historico_pedidos(request):
    # Só o próprio usuário logado vê seus pedidos.
    # Busca por email solto removida: expunha pedidos de qualquer pessoa (IDOR).
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-criado_em')
    return render(request, 'loja/historico.html', {
        'pedidos': pedidos,
        'buscou': True,
    })

def aviso_estoque(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if email:
            try:
                send_mail(
                    subject=f'[Ari Pratas] Produto de volta ao estoque: {produto.nome}',
                    message=f'Olá! Você pediu para ser avisado quando "{produto.nome}" voltasse ao estoque. Assim que disponível, entraremos em contato.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.DEFAULT_FROM_EMAIL],
                    fail_silently=True,
                )
            except Exception:
                pass
    return redirect('loja:detalhe_produto', slug=produto.slug)




def pagamento_sucesso(request):
    pedido_id = request.GET.get('external_reference')
    payment_id = request.GET.get('payment_id')
    if pedido_id:
        try:
            pedido = Pedido.objects.get(id=pedido_id)
            pedido.status = 'pago'
            pedido.mp_payment_id = payment_id or ''
            pedido.save()
        except Pedido.DoesNotExist:
            pass
    return render(request, 'loja/pedido_confirmado.html')

def pagamento_falha(request):
    return render(request, 'loja/pagamento_falha.html')

def pagamento_pendente(request):
    return render(request, 'loja/pedido_confirmado.html')