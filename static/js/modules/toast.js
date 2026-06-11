/**
 * toast.js — Ari Pratas
 * Sistema de notificações toast global.
 * Uso: Toast.show('Produto adicionado!', 'sucesso')
 * Tipos: 'sucesso' | 'erro' | 'info'
 */

const Toast = (() => {
  'use strict';

  let container = null;

  function getContainer() {
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    return container;
  }

  const icones = {
    sucesso: '✓',
    erro: '✕',
    info: 'ℹ',
  };

  /**
   * Exibe um toast.
   * @param {string} mensagem
   * @param {'sucesso'|'erro'|'info'} tipo
   * @param {number} duracao - ms (padrão 3500)
   */
  function show(mensagem, tipo = 'sucesso', duracao = 3500) {
    const c = getContainer();

    const toast = document.createElement('div');
    toast.className = `toast toast--${tipo}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'polite');

    toast.innerHTML = `
      <span class="toast-icone">${icones[tipo] || icones.info}</span>
      <span class="toast-msg">${mensagem}</span>
      <button class="toast-fechar" aria-label="Fechar">✕</button>
    `;

    // Fechar manualmente
    toast.querySelector('.toast-fechar').addEventListener('click', () => fechar(toast));

    c.appendChild(toast);

    // Animação de entrada
    requestAnimationFrame(() => toast.classList.add('toast--visivel'));

    // Auto-fechar
    setTimeout(() => fechar(toast), duracao);

    return toast;
  }

  function fechar(toast) {
    toast.classList.remove('toast--visivel');
    toast.classList.add('toast--saindo');
    toast.addEventListener('transitionend', () => toast.remove(), { once: true });
  }

  return { show };
})();

window.Toast = Toast;
