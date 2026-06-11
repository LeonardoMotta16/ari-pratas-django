# Resultados dos Testes — Pratas da Ari
**Data:** 30/05/2026  
**Total:** 84 testes | ✅ 79 passaram | ❌ 4 falharam | ⚠️ 1 erro

---

## ✅ Testes que passaram (79)

### Models
- `CategoriaModelTest` — slug gerado automaticamente, `__str__`
- `ProdutoModelTest` — slug, `preco_final` com/sem promoção, desconto calculado, desconto sem preço original, imagem principal sem imagens, `__str__`
- `PedidoModelTest` — `__str__`, total correto
- `ItemPedidoModelTest` — `preco_total`
- `CupomModelTest` — `__str__`, criado como ativo
- `FavoritoModelTest` — `__str__`, `unique_together`
- `AvaliacaoModelTest` — `__str__`

### Home e Listagem
- `HomeViewTest` — retorna 200, destaques aparecem, produto indisponível não aparece
- `ListaProdutosViewTest` — retorna 200, busca por nome, filtro por categoria, produto indisponível não aparece
- `DetalheProdutoViewTest` — retorna 200, produto indisponível retorna 404

### Carrinho
- Carrinho vazio retorna 200
- Adicionar produto ao carrinho
- Adicionar via AJAX retorna JSON
- Adicionar mesmo produto incrementa quantidade
- Remover produto do carrinho
- Remover um decrementa quantidade
- Remover um quando quantidade 1 remove item
- Adicionar com tamanho cria chave diferente

### Cupons
- Cupom válido aplica desconto
- Cupom inválido exibe erro
- Cupom inativo rejeitado
- Cupom já usado pelo mesmo usuário rejeitado
- Cupom pode ser usado por outro usuário

### Checkout
- GET retorna 200
- Sem nome exibe erro
- Cria pedido com dados válidos
- Redireciona para confirmado
- Limpa carrinho após finalizar
- Cria itens de pedido corretamente
- Total correto no pedido
- Com `criar_conta` cria usuário
- Usuário logado vincula pedido
- Com cupom aplica desconto no total
- Com cupom marca como usado (`CupomUsado`)

### Autenticação / Cadastro
- GET retorna 200
- Cadastro válido cria usuário
- Email duplicado exibe erro
- Senhas diferentes exibe erro
- Vincula pedidos anteriores ao cadastrar

### Favoritos
- Toggle adiciona favorito
- Toggle remove favorito existente
- Favorito requer login (redireciona para `/login/`)
- Lista favoritos retorna 200
- Lista favoritos requer login

### Avaliações
- Avaliar requer login
- Avaliar sem compra redireciona (sem criar avaliação)
- Avaliar após compra cria avaliação
- Avaliar duas vezes atualiza (não duplica)

### Feedback
- GET retorna 200
- POST válido cria feedback
- POST via AJAX retorna JSON `ok: true`
- POST incompleto não cria feedback
- POST incompleto via AJAX retorna erro

### Histórico de Pedidos
- Usuário autenticado vê seus pedidos
- Usuário não vê pedidos de outro

### Segurança
- Cupom não pode ser reutilizado pelo mesmo usuário
- Enviar rastreio requer staff (usuário comum é redirecionado)
- Enviar rastreio funciona para staff
- Usuário não pode avaliar produto que não comprou
- CSRF ativo no checkout (retorna 403 sem token)

### Páginas Estáticas
- `/sobre/` retorna 200
- `/contato/` retorna 200
- `/pedido-confirmado/` retorna 200

---

## ❌ Testes que falharam (4)

### 1. `test_checkout_campos_obrigatorios`
**Causa:** O template do checkout usa o atributo HTML `required` nos campos, o que impede o formulário de ser submetido vazio no browser. Mas nos testes o Django processa o POST diretamente, ignorando o `required` do HTML. Como o carrinho continua populado com 1 item (do `setUp`), a view renderiza o formulário normalmente **sem** exibir erros — porque a view só valida quando recebe dados e encontra campos vazios, mas o POST com `{}` chega com strings vazias, o que *deveria* acionar a validação. Investigar se a view realmente entra no bloco de erro com POST vazio.

**O que fazer:** Verificar a view `checkout` — o POST com campos todos vazios deve cair nos `erros.append(...)`. Provavelmente há uma condição que não está sendo satisfeita. Corrigir o teste para enviar ao menos `{}` com chaves presentes, ou corrigir a view para validar corretamente campos ausentes vs. vazios.

---

### 2. `test_checkout_carrinho_vazio_redireciona`
**Causa:** O teste força `request.session['carrinho'] = {}` mas a sessão do Django test client não está sendo sobrescrita corretamente dessa forma. O carrinho do `setUp` (que adicionou 1 produto) persiste.

**O que fazer:** Substituir a abordagem de limpeza por:
```python
session = self.client.session
session['carrinho'] = {}
session.save()
```

---

### 3. `test_busca_por_email_retorna_pedidos` (HistoricoPedidosViewTest)
**Causa:** O template do histórico exibe o **número do pedido** (`Pedido #13`) mas não exibe o **nome** do cliente (`Carol`). O teste procura por `"Carol"` no HTML, mas esse dado não aparece no template atual.

**O que fazer:** Ajustar o teste para buscar algo que realmente aparece, como o número do pedido ou o total:
```python
self.assertContains(r, "Pedido #")
```

---

### 4. `test_historico_por_email_nao_exige_autenticacao_mas_expoe_dados` (SegurancaTest)
**Causa:** Mesmo motivo do teste acima — o nome `"Vítima"` não aparece no HTML renderizado, logo o `assertContains` falha. O pedido é exibido (como `Pedido #21`) mas sem o nome do cliente.

**O que fazer:** Atualizar o teste para confirmar a vulnerabilidade verificando o que *realmente* aparece (número do pedido, total), ou exibir o nome no template e aí o teste passa como documentação do bug IDOR.

---

## ⚠️ Erro de execução (1)

### `test_produto_fora_estoque_nao_adiciona_ajax`
**Causa:** Dois produtos com o mesmo nome padrão `"Anel de Prata"` são criados no mesmo teste — um no `setUp` e outro dentro do teste. Como o slug é gerado a partir do nome e deve ser único, o segundo `Produto.objects.create(...)` estoura `UniqueViolation` no banco.

**O que fazer:** Usar um nome diferente para o produto fora de estoque:
```python
p = make_produto("Anel Fora de Estoque", fora_estoque=True, preco=100, preco_original=100)
```

---

## 🔧 Problema de infraestrutura

O banco de testes (`test_postgres` no Supabase) não foi destruído ao final porque havia outra sessão ativa. Isso não afeta os resultados, mas para evitar o aviso é recomendável usar um banco SQLite local para testes, adicionando ao `settings.py`:

```python
import sys
if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'test_db.sqlite3',
        }
    }
```

Isso deixa os testes mais rápidos (23s → ~2s) e não depende de conexão com o Supabase.
