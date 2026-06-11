/**
 * produto.js — Ari Pratas
 * Comportamentos da página de detalhe do produto:
 * - Galeria de imagens (troca com fade)
 * - Seletor de tamanhos
 * - Botão de copiar link
 */

;(function () {
  'use strict';

  // ─── GALERIA ──────────────────────────────────────────────────
  function initGaleria() {
    const principal = document.getElementById('imagem-principal');
    if (!principal) return;

    document.querySelectorAll('.miniatura').forEach(thumb => {
      thumb.addEventListener('click', () => {
        const url = thumb.dataset.url;
        if (!url) return;

        principal.style.opacity = '0';
        setTimeout(() => {
          principal.src = url;
          principal.style.opacity = '1';
        }, 200);

        document.querySelectorAll('.miniatura').forEach(m => m.classList.remove('ativa'));
        thumb.classList.add('ativa');
      });
    });
  }

  // ─── TAMANHOS ─────────────────────────────────────────────────
  function initTamanhos() {
    const inputTamanho = document.getElementById('tamanho-selecionado');
    if (!inputTamanho) return;

    document.querySelectorAll('.btn-tamanho').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.btn-tamanho').forEach(b => b.classList.remove('selecionado'));
        btn.classList.add('selecionado');
        inputTamanho.value = btn.dataset.tamanho;
      });
    });
  }

  // ─── COPIAR LINK ──────────────────────────────────────────────
  function initCopiarLink() {
    const btnCopiar = document.getElementById('btn-copiar');
    if (!btnCopiar) return;

    btnCopiar.addEventListener('click', () => {
      navigator.clipboard.writeText(window.location.href).then(() => {
        const span = document.getElementById('texto-copiar');
        if (span) {
          span.textContent = 'Copiado!';
          setTimeout(() => { span.textContent = 'Copiar link'; }, 2000);
        }
      });
    });
  }

  // ─── INIT ─────────────────────────────────────────────────────
  function init() {
    initGaleria();
    initTamanhos();
    initCopiarLink();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();