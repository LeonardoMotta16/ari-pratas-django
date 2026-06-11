# pyright: reportMissingModuleSource=false
# Register your models here.
from django.contrib import admin
from .models import Categoria, Produto, ImagemProduto
from .models import Feedback

class ImagemInline(admin.TabularInline):
    model = ImagemProduto
    extra = 3

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'slug', 'icone']
    prepopulated_fields = {'slug': ('nome',)}

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'categoria', 'preco', 'destaque', 'novo', 'disponivel']
    list_filter = ['categoria', 'destaque', 'novo', 'disponivel']
    list_editable = ['destaque', 'novo', 'disponivel']
    search_fields = ['nome']
    prepopulated_fields = {'slug': ('nome',)}
    inlines = [ImagemInline]

@admin.register(ImagemProduto)
class ImagemAdmin(admin.ModelAdmin):
    list_display = ['produto', 'principal', 'ordem']


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'estrelas', 'criado_em')
    list_filter = ('estrelas',)
    ordering = ('-criado_em',)