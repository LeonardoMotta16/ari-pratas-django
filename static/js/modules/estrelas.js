/**
 * estrelas.js — Ari Pratas
 * Inicializa interatividade das estrelas de avaliação.
 * Funciona para qualquer container com `.estrela` dentro.
 *
 * Uso automático: qualquer .estrelas-container na página é inicializado.
 * Uso manual: Estrelas.init(containerElement)
 */

const Estrelas = (() => {
  'use strict';

  /**
   * Inicializa um container de estrelas.
   * @param {Element} container - elemento pai com as .estrela
   * @param {string} nomeInput - name do radio input (padrão: 'estrelas')
   */
  function init(container, nomeInput = 'estrelas') {
    if (!container) return;

    const estrelas = container.querySelectorAll('.estrela');
    if (!estrelas.length) return;

    function pintar(ate) {
      estrelas.forEach(e =>
        e.style.color = parseInt(e.dataset.valor) <= ate ? '#f0a500' : '#ddd'
      );
    }

    function valorSelecionado() {
      const sel = container.querySelector(`input[name="${nomeInput}"]:checked`);
      return sel ? parseInt(sel.value) : 0;
    }

    estrelas.forEach(estrela => {
      const valor = parseInt(estrela.dataset.valor);

      estrela.addEventListener('mouseover', () => pintar(valor));
      estrela.addEventListener('mouseout', () => pintar(valorSelecionado()));
      estrela.addEventListener('click', () => {
        const radio = container.querySelector(
          `input[name="${nomeInput}"][value="${valor}"]`
        );
        if (radio) radio.checked = true;
        pintar(valor);
      });
    });

    // Pinta o valor já selecionado (ex: editar avaliação)
    pintar(valorSelecionado());
  }

  /**
   * Inicializa todos os .estrelas-container da página.
   */
  function initAll() {
    document.querySelectorAll('.estrelas-container').forEach(container => {
      // Detecta o name do radio dentro deste container
      const radio = container.querySelector('input[type="radio"]');
      const nome = radio ? radio.name : 'estrelas';
      init(container, nome);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }

  return { init, initAll };
})();

window.Estrelas = Estrelas;
