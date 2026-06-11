from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.text import slugify
from loja.models import Produto, Categoria, Pedido, ImagemProduto, Cupom, Feedback
from django.db import models
import uuid
from decimal import Decimal, InvalidOperation


def _parse_preco(valor):  # ← também no topo, fora de qualquer view
    try:
        v = Decimal(valor.replace(',', '.').strip())
        return v if v > 0 else None
    except (InvalidOperation, AttributeError):
        return None



@staff_member_required(login_url='/login/')
def dashboard(request):
    total_produtos = Produto.objects.count()
    total_categorias = Categoria.objects.count()
    total_pedidos = Pedido.objects.count()
    pedidos_recentes = Pedido.objects.order_by('-criado_em')[:5]
    return render(request, 'painel/dashboard.html', {
        'total_produtos': total_produtos,
        'total_categorias': total_categorias,
        'total_pedidos': total_pedidos,
        'pedidos_recentes': pedidos_recentes,
    })


@staff_member_required(login_url='/login/')
def produtos_lista(request):
    produtos = Produto.objects.all().order_by('-id')
    return render(request, 'painel/produtos_lista.html', {'produtos': produtos})


@staff_member_required(login_url='/login/')
def produto_criar(request):
    categorias = Categoria.objects.all()
    if request.method == 'POST':
        nome = request.POST.get('nome')
        preco_original = _parse_preco(request.POST.get('preco_original', ''))
        preco_promo    = _parse_preco(request.POST.get('preco', ''))

        if preco_promo and preco_original and preco_promo < preco_original:
            promocao_ativa = True
        else:
            preco_promo    = None
            promocao_ativa = False

        descricao    = request.POST.get('descricao', '')
        material     = request.POST.get('material', '')
        medidas      = request.POST.get('medidas', '')
        cuidados     = request.POST.get('cuidados', '')
        categoria_id = request.POST.get('categoria') or None
        destaque     = request.POST.get('destaque') == 'on'
        novo         = request.POST.get('novo') == 'on'
        fora_estoque = request.POST.get('fora_estoque') == 'on'
        acao         = request.POST.get('acao', 'postar')
        disponivel   = acao == 'postar'

        slug = slugify(nome)
        if Produto.objects.filter(slug=slug).exists():
            slug = f"{slug}-{uuid.uuid4().hex[:6]}"

        produto = Produto.objects.create(
            nome=nome,
            slug=slug,
            preco=preco_promo,          # ← era preco=preco (variável inexistente)
            preco_original=preco_original,
            promocao_ativa=promocao_ativa,
            descricao=descricao,
            material=material,
            medidas=medidas,
            cuidados=cuidados,
            categoria_id=categoria_id,
            destaque=destaque,
            novo=novo,
            disponivel=disponivel,
            fora_estoque=fora_estoque,
        )

        imagens = request.FILES.getlist('imagens')
        for i, img in enumerate(imagens):
            ImagemProduto.objects.create(produto=produto, imagem=img, principal=(i == 0), ordem=i)

        return redirect('painel:produtos_lista')

    return render(request, 'painel/produto_form.html', {'categorias': categorias, 'produto': None})

@staff_member_required(login_url='/login/')
def produto_editar(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    categorias = Categoria.objects.all()
    if request.method == 'POST':
        produto.nome = request.POST.get('nome')

        preco_original = _parse_preco(request.POST.get('preco_original', ''))
        preco_promo    = _parse_preco(request.POST.get('preco', ''))

        produto.preco_original = preco_original

        if preco_promo and preco_original and preco_promo < preco_original:
            produto.preco          = preco_promo
            produto.promocao_ativa = True
        else:
            produto.preco          = None
            produto.promocao_ativa = False

        produto.descricao    = request.POST.get('descricao', '')
        produto.material     = request.POST.get('material', '')
        produto.medidas      = request.POST.get('medidas', '')
        produto.cuidados     = request.POST.get('cuidados', '')
        produto.categoria_id = request.POST.get('categoria') or None
        produto.destaque     = request.POST.get('destaque') == 'on'
        produto.novo         = request.POST.get('novo') == 'on'
        produto.fora_estoque = request.POST.get('fora_estoque') == 'on'
        acao                 = request.POST.get('acao', 'postar')
        produto.disponivel   = acao == 'postar'
        produto.save()

        # Deletar imagens marcadas
        deletar_ids = request.POST.getlist('deletar_imagem')
        if deletar_ids:
            ImagemProduto.objects.filter(id__in=deletar_ids, produto=produto).delete()

        # Definir imagem principal
        principal_id = request.POST.get('imagem_principal')
        if principal_id:
            ImagemProduto.objects.filter(produto=produto).update(principal=False)
            ImagemProduto.objects.filter(id=principal_id, produto=produto).update(principal=True)

        # Adicionar novas imagens
        imagens = request.FILES.getlist('imagens')
        tem_principal = ImagemProduto.objects.filter(produto=produto, principal=True).exists()
        for i, img in enumerate(imagens):
            principal = not tem_principal and i == 0
            ImagemProduto.objects.create(produto=produto, imagem=img, principal=principal, ordem=i)

        return redirect('painel:produtos_lista')

    return render(request, 'painel/produto_form.html', {'produto': produto, 'categorias': categorias})

@staff_member_required(login_url='/login/')
def produto_deletar(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    if request.method == 'POST':
        produto.delete()
        return redirect('painel:produtos_lista')
    return render(request, 'painel/produto_confirmar_delete.html', {'produto': produto})
    
@staff_member_required(login_url='/login/')
def categorias_lista(request):
    categorias = Categoria.objects.all().order_by('nome')
    return render(request, 'painel/categorias_lista.html', {'categorias': categorias})


@staff_member_required(login_url='/login/')
def categoria_criar(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        icone = request.POST.get('icone', '')
        slug = slugify(nome)
        if Categoria.objects.filter(slug=slug).exists():
            slug = f"{slug}-{uuid.uuid4().hex[:6]}"
        Categoria.objects.create(nome=nome, icone=icone, slug=slug)
        return redirect('painel:categorias_lista')
    return render(request, 'painel/categoria_form.html', {'categoria': None})


@staff_member_required(login_url='/login/')
def categoria_editar(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    if request.method == 'POST':
        categoria.nome = request.POST.get('nome')
        categoria.icone = request.POST.get('icone', '')
        categoria.save()
        return redirect('painel:categorias_lista')
    return render(request, 'painel/categoria_form.html', {'categoria': categoria})


@staff_member_required(login_url='/login/')
def categoria_deletar(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    if request.method == 'POST':
        categoria.delete()
        return redirect('painel:categorias_lista')
    return render(request, 'painel/categoria_confirmar_delete.html', {'categoria': categoria})
    
@staff_member_required(login_url='/login/')
def pedidos_lista(request):
    pedidos = Pedido.objects.all().order_by('-criado_em')
    return render(request, 'painel/pedidos_lista.html', {'pedidos': pedidos})


@staff_member_required(login_url='/login/')
@staff_member_required(login_url='/login/')
def pedido_detalhe(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    return render(request, 'painel/pedido_detalhe.html', {'pedido': pedido})


@staff_member_required(login_url='/login/')
def salvar_rastreio(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    if request.method == 'POST':
        codigo = request.POST.get('codigo_rastreio', '').strip()
        acao = request.POST.get('acao', 'salvar')
        
        if codigo:
            pedido.codigo_rastreio = codigo
            
            if acao == 'salvar_e_enviar':
                from django.core.mail import send_mail
                from django.conf import settings
                send_mail(
                    subject=f'Seu pedido #{pedido.id} foi enviado! — Ari Pratas',
                    message=f'''Olá, {pedido.nome}!

Seu pedido foi enviado e já está a caminho!

Código de rastreio: {codigo}

Você pode rastrear seu pedido nos Correios:
https://www.correios.com.br/

Qualquer dúvida, entre em contato conosco.

Equipe Ari Pratas ✨''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[pedido.email],
                )
                pedido.rastreio_enviado = True
            
            pedido.save()
    
    return redirect('painel:pedido_detalhe', pedido_id=pedido_id)
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST

@staff_member_required(login_url='/login/')
def produto_imagens(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    imagens = produto.imagens.all().order_by('ordem')
    return render(request, 'painel/produto_imagens.html', {
        'produto': produto,
        'imagens': imagens,
    })

@staff_member_required(login_url='/login/')
@require_POST
def salvar_ordem_imagens(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    dados = json.loads(request.body)
    ids_ordenados = dados.get('ordem', [])
    
    ImagemProduto.objects.filter(produto=produto).update(principal=False)
    for i, img_id in enumerate(ids_ordenados):
        ImagemProduto.objects.filter(id=img_id, produto=produto).update(
            ordem=i,
            principal=(i == 0)
        )
    return JsonResponse({'ok': True})

@staff_member_required(login_url='/login/')
def cupons_lista(request):
    cupons = Cupom.objects.all()
    return render(request, 'painel/cupons_lista.html', {'cupons': cupons})


@staff_member_required(login_url='/login/')
def cupom_criar(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip().upper()
        desconto = request.POST.get('desconto')
        ativo = request.POST.get('ativo') == 'on'
        Cupom.objects.create(codigo=codigo, desconto=desconto, ativo=ativo)
        return redirect('painel:cupons_lista')
    return render(request, 'painel/cupom_form.html', {'cupom': None})


@staff_member_required(login_url='/login/')
def cupom_editar(request, cupom_id):
    cupom = get_object_or_404(Cupom, id=cupom_id)
    if request.method == 'POST':
        cupom.codigo = request.POST.get('codigo', '').strip().upper()
        cupom.desconto = request.POST.get('desconto')
        cupom.ativo = request.POST.get('ativo') == 'on'
        cupom.save()
        return redirect('painel:cupons_lista')
    return render(request, 'painel/cupom_form.html', {'cupom': cupom})


@staff_member_required(login_url='/login/')
def cupom_deletar(request, cupom_id):
    cupom = get_object_or_404(Cupom, id=cupom_id)
    if request.method == 'POST':
        cupom.delete()
        return redirect('painel:cupons_lista')
    return render(request, 'painel/cupom_confirmar_delete.html', {'cupom': cupom})


@staff_member_required(login_url='/login/')
def cupom_toggle(request, cupom_id):
    cupom = get_object_or_404(Cupom, id=cupom_id)
    cupom.ativo = not cupom.ativo
    cupom.save()
    return redirect('painel:cupons_lista')


@staff_member_required(login_url='/login/')
def feedbacks_lista(request):
    feedbacks = Feedback.objects.all()
    total = feedbacks.count()
    media = feedbacks.aggregate(media=models.Avg('estrelas'))['media']
    return render(request, 'painel/feedbacks_lista.html', {
        'feedbacks': feedbacks,
        'total': total,
        'media': media,
    })