/**
 * checkout.js — Ari Pratas
 * Loading visual ao submeter o formulário de checkout.
 * - Spinner no botão "Confirmar Pedido"
 * - Overlay de página durante o processamento
 * - Previne duplo clique
 */

;(function () {
  'use strict';

  function criarOverlay() {
    const overlay = document.createElement('div');
    overlay.id = 'checkout-overlay';
    overlay.className = 'checkout-overlay';
    overlay.innerHTML = `
      <div class="checkout-overlay__box">
        <div class="checkout-overlay__spinner"></div>
        <p class="checkout-overlay__texto">Confirmando seu pedido…</p>
      </div>
    `;
    document.body.appendChild(overlay);
    return overlay;
  }

  function ativarLoading(btn, overlay) {
    // Botão
    btn.disabled = true;
    btn.dataset.textoOriginal = btn.textContent.trim();
    btn.textContent = 'Processando…';
    btn.classList.add('btn--loading');

    // Overlay
    overlay.classList.add('checkout-overlay--visivel');
  }

  function init() {
    const form = document.querySelector('form[method="post"]');
    if (!form) return;

    const btn = form.querySelector('button[type="submit"]');
    if (!btn) return;

    const overlay = criarOverlay();

    form.addEventListener('submit', function (e) {
      // Deixa a validação nativa do browser rodar primeiro
      if (!form.checkValidity()) return;

      // Previne duplo submit
      if (btn.disabled) {
        e.preventDefault();
        return;
      }

      ativarLoading(btn, overlay);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();