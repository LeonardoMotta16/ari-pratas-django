/**
 * carrinho.js — Ari Pratas
 * Intercepta o formulário "Adicionar ao Carrinho".
 * - Valida se tamanho foi selecionado (quando necessário)
 * - Coloca o botão em estado de loading
 * - Envia via fetch (AJAX)
 * - Exibe toast de sucesso ou erro
 * - Atualiza o contador do carrinho na navbar
 */

;(function () {
  'use strict';

  function init() {
    const form = document.getElementById('form-carrinho');
    if (!form) return;

    const btn = form.querySelector('button[type="submit"]');
    const tamanhoInput = document.getElementById('tamanho-selecionado');
    const tamanhoContainer = document.getElementById('tamanhos-container');

    form.addEventListener('submit', async function (e) {
      e.preventDefault();

      // Valida tamanho se existir seletor
      if (tamanhoContainer && !tamanhoInput.value) {
        // Destaca os botões de tamanho
        tamanhoContainer.classList.add('tamanhos--erro');
        setTimeout(() => tamanhoContainer.classList.remove('tamanhos--erro'), 2000);
        Toast.show('Selecione um tamanho antes de continuar.', 'erro');
        return;
      }

      // Estado de loading
      setLoading(btn, true);

      try {
        const res = await fetch(form.action, {
          method: 'POST',
          body: new FormData(form),
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });

        const data = await res.json();

        if (data.ok) {
          Toast.show(data.mensagem || 'Produto adicionado ao carrinho! 🛍️', 'sucesso');
          atualizarContadorCarrinho(data.total);
        } else {
          Toast.show(data.mensagem || 'Não foi possível adicionar o produto.', 'erro');
        }
      } catch (err) {
        Toast.show('Erro de conexão. Tente novamente.', 'erro');
      } finally {
        setLoading(btn, false);
      }
    });
  }

  /**
   * Liga/desliga estado de loading no botão.
   */
  function setLoading(btn, loading) {
    if (!btn) return;
    if (loading) {
      btn.disabled = true;
      btn.dataset.textoOriginal = btn.textContent;
      btn.textContent = 'Adicionando...';
      btn.classList.add('btn--loading');
    } else {
      btn.disabled = false;
      btn.textContent = btn.dataset.textoOriginal || 'Adicionar ao Carrinho';
      btn.classList.remove('btn--loading');
    }
  }

  /**
   * Atualiza o número entre parênteses no ícone do carrinho na navbar.
   * Espera que o link tenha classe .btn-carrinho
   */
  function atualizarContadorCarrinho(total) {
    const btnCarrinho = document.querySelector('.btn-carrinho');
    if (!btnCarrinho) return;

    if (total > 0) {
      // Remove contador antigo se existir
      const velho = btnCarrinho.querySelector('.carrinho-count');
      if (velho) velho.remove();

      const span = document.createElement('span');
      span.className = 'carrinho-count';
      span.textContent = `(${total})`;
      btnCarrinho.appendChild(span);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
