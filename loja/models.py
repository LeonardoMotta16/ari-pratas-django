from django.db import models  # type: ignore[import]
from django.utils.text import slugify  # type: ignore[import]
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    icone = models.CharField(max_length=10, blank=True)  # ex: 💍

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name_plural = "Categorias"


class Produto(models.Model):
    nome = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preco_original = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    promocao_ativa = models.BooleanField(default=False)
    descricao = models.TextField(blank=True)
    material = models.CharField(max_length=200, blank=True)
    medidas = models.CharField(max_length=200, blank=True)
    cuidados = models.TextField(blank=True)
    destaque = models.BooleanField(default=False)
    novo = models.BooleanField(default=False)
    disponivel = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    fora_estoque = models.BooleanField(default=False)


    @property
    def preco_final(self):  # ← ADICIONAR ESSE PROPERTY
        if (
            self.promocao_ativa
            and self.preco is not None
            and self.preco > 0
            and self.preco < self.preco_original
        ):
            return self.preco
        return self.preco_original

    def desconto(self):
        if self.preco_original and self.preco and self.preco_original > self.preco:
            return int((1 - self.preco / self.preco_original) * 100)
        return None

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def imagem_principal(self):
        img = self.imagens.filter(principal=True).first()
        if not img:
            img = self.imagens.first()
        return img

    def desconto(self):
        if self.preco_original and self.preco and self.preco_original > self.preco:
            return int((1 - self.preco / self.preco_original) * 100)
        return None

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name_plural = "Produtos"


class ImagemProduto(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='imagens')
    imagem = models.ImageField(upload_to='produtos/')
    principal = models.BooleanField(default=False)
    ordem = models.IntegerField(default=0)

    def __str__(self):
        return f"Imagem de {self.produto.nome}"

    class Meta:
        ordering = ['ordem']
        
        
class Pedido(models.Model):
    nome = models.CharField(max_length=200)
    email = models.EmailField()
    usuario = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    endereco = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    codigo_rastreio = models.CharField(max_length=100, blank=True)
    rastreio_enviado = models.BooleanField(default=False)

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('cancelado', 'Cancelado'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    mp_preference_id = models.CharField(max_length=200, blank=True)
    mp_payment_id = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Pedido #{self.id} - {self.nome}"

    class Meta:
        verbose_name_plural = "Pedidos"
        ordering = ['-criado_em']


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True)
    quantidade = models.IntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    tamanho = models.CharField(max_length=20, blank=True)

    @property
    def preco_total(self):
        return self.preco_unitario * self.quantidade

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome}"


class Favorito(models.Model):
    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='favoritos')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='favoritos')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'produto')

    def __str__(self):
        return f"{self.usuario} favoritou {self.produto.nome}"

class Avaliacao(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='avaliacoes')
    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    estrelas = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comentario = models.TextField(blank=True)
    foto = models.ImageField(upload_to='avaliacoes/', blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('produto', 'usuario')
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.usuario} avaliou {self.produto.nome} com {self.estrelas}★"


class Cupom(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    desconto = models.PositiveIntegerField(help_text='Porcentagem de desconto (ex: 10 = 10%)')
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    fidelidade = models.BooleanField(default=False)
    usuario = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'{self.codigo} — {self.desconto}%'
    
    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Cupom'
        verbose_name_plural = 'Cupons'


class CupomUsado(models.Model):
    """Registra que um usuário já usou um cupom, sem desativá-lo globalmente."""
    cupom = models.ForeignKey(Cupom, on_delete=models.CASCADE, related_name='usos')
    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='cupons_usados')
    usado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cupom', 'usuario')
        verbose_name = 'Cupom Usado'
        verbose_name_plural = 'Cupons Usados'

    def __str__(self):
        return f'{self.usuario} usou {self.cupom.codigo}'


class Feedback(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    estrelas = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    mensagem = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Feedback'
        verbose_name_plural = 'Feedbacks'

    def __str__(self):
        return f"{self.nome} — {self.estrelas}★"

class Migration(migrations.Migration):
 
    dependencies = [
        ('loja', '0016_produto_promocao_ativa'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
 
    operations = [
        migrations.CreateModel(
            name='CupomUsado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usado_em', models.DateTimeField(auto_now_add=True)),
                ('cupom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usos', to='loja.cupom')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cupons_usados', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Cupom Usado',
                'verbose_name_plural': 'Cupons Usados',
                'unique_together': {('cupom', 'usuario')},
            },
        ),
    ]
