func = '''def remover_um_carrinho(request, produto_id):
    carrinho = request.session.get('carrinho', {})
    chave = str(produto_id)
    if chave in carrinho:
        if carrinho[chave]['quantidade'] > 1:
            carrinho[chave]['quantidade'] -= 1
        else:
            del carrinho[chave]
    request.session['carrinho'] = carrinho
    return redirect('loja:carrinho')
'''

with open('loja/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Acha onde começa a função
inicio = None
for i, line in enumerate(lines):
    if 'def remover_um_carrinho' in line:
        inicio = i
        break

if inicio is not None:
    lines = lines[:inicio]
    lines.append('\n' + func)
    with open('loja/views.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print('Corrigido!')
else:
    print('Funcao nao encontrada')