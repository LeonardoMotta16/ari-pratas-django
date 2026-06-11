/**
 * ui.js — Ari Pratas
 * Comportamentos globais de UI presentes em todas as páginas:
 * - Scroll Reveal
 * - Menu hamburguer (mobile)
 * - WhatsApp flutuante
 * - Popup de feedback
 */

;(function () {
  'use strict';

  function init() {
    initScrollReveal();
    initMenuHamburguer();
    initWhatsappFlutuante();
    initPopupFeedback();
  }

  // ─── SCROLL REVEAL ────────────────────────────────────────────
  function initScrollReveal() {
    const reveals = document.querySelectorAll('.reveal');
    if (!reveals.length) return;

    const observer = new IntersectionObserver(
      entries => entries.forEach(entry => {
        if (entry.isIntersecting) entry.target.classList.add('visivel');
      }),
      { threshold: 0.1 }
    );

    reveals.forEach(el => observer.observe(el));
  }

  // ─── MENU HAMBURGUER ──────────────────────────────────────────
  function initMenuHamburguer() {
    const btnMenu = document.querySelector('.navbar-menu');
    const navLinks = document.querySelector('.navbar-links');
    if (!btnMenu || !navLinks) return;

    btnMenu.addEventListener('click', () => {
      navLinks.classList.toggle('aberto');
      btnMenu.setAttribute('aria-expanded', navLinks.classList.contains('aberto'));
    });

    // Fecha ao clicar fora
    document.addEventListener('click', e => {
      if (!btnMenu.contains(e.target) && !navLinks.contains(e.target)) {
        navLinks.classList.remove('aberto');
        btnMenu.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // ─── WHATSAPP FLUTUANTE ───────────────────────────────────────
  function initWhatsappFlutuante() {
    const wpp = document.querySelector('.whatsapp-flutuante');
    if (!wpp) return;

    window.addEventListener('scroll', () => {
      wpp.classList.toggle('visivel', window.scrollY > 300);
    }, { passive: true });
  }

  // ─── POPUP FEEDBACK ───────────────────────────────────────────
  function initPopupFeedback() {
    const popup = document.getElementById('popup-feedback');
    if (!popup) return;

    // Expõe funções globais usadas nos botões do template
    window.abrirPopup = () => popup.classList.add('aberto');
    window.fecharPopup = () => popup.classList.remove('aberto');

    // Fecha ao clicar no overlay
    popup.addEventListener('click', e => {
      if (e.target === popup) window.fecharPopup();
    });

    // Exibe automaticamente 1x por mês
    if (deveExibirPopup()) {
      setTimeout(() => {
        window.abrirPopup();
        marcarExibido();
      }, 30000);
    }

    // AJAX do formulário
    const form = document.getElementById('form-feedback-popup');
    if (!form) return;

    form.addEventListener('submit', async function (e) {
      e.preventDefault();

      const btn = form.querySelector('button[type="submit"]');
      if (btn) {
        btn.disabled = true;
        btn.textContent = 'Enviando...';
      }

      try {
        const res = await fetch(form.action, {
          method: 'POST',
          body: new FormData(form),
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        const data = await res.json();
        if (data.ok) {
          document.getElementById('popup-conteudo').style.display = 'none';
          document.getElementById('popup-sucesso').style.display = 'block';
        }
      } catch {
        if (btn) {
          btn.disabled = false;
          btn.textContent = 'Enviar Feedback';
        }
      }
    });
  }

  function deveExibirPopup() {
    const salvo = localStorage.getItem('feedback_mes');
    const agora = new Date();
    return salvo !== `${agora.getFullYear()}-${agora.getMonth() + 1}`;
  }

  function marcarExibido() {
    const agora = new Date();
    localStorage.setItem('feedback_mes', `${agora.getFullYear()}-${agora.getMonth() + 1}`);
  }

  // ─── INIT ─────────────────────────────────────────────────────
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();