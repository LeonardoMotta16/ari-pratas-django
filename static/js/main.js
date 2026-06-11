/**
 * main.js — Ari Pratas
 * Ponto de entrada do JS da loja.
 * Importa todos os módulos na ordem correta.
 *
 * Incluir no base.html antes do </body>:
 *   <script src="{% static 'js/modules/toast.js' %}"></script>
 *   <script src="{% static 'js/modules/estrelas.js' %}"></script>
 *   <script src="{% static 'js/modules/carrinho.js' %}"></script>
 *   <script src="{% static 'js/modules/ui.js' %}"></script>
 *   <script src="{% static 'js/validacao.js' %}"></script>
 */

// Este arquivo serve como documentação da ordem de carregamento.
// Como o Django serve estáticos sem bundler, os scripts são carregados
// individualmente via <script> tags no base.html (ver comentário acima).
//
// Ordem importa:
// 1. toast.js       — sem dependências
// 2. estrelas.js    — sem dependências
// 3. carrinho.js    — depende de toast.js
// 4. ui.js          — depende de toast.js
// 5. validacao.js   — já existia, sem dependências
