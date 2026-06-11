/**
 * validacao.js — Ari Pratas
 * Validação inline de formulários com feedback visual em tempo real.
 *
 * PRINCÍPIO: validar no blur (quando o usuário sai do campo),
 * não no keyup (muito agressivo) e não só no submit (tarde demais).
 */

;(function () {
  'use strict';

  // ============================================================
  // UTILITÁRIOS
  // ============================================================

  /**
   * Marca um campo como ERRO.
   * Adiciona classe visual, ícone e mensagem embaixo.
   */
  function marcarErro(input, mensagem) {
    const wrapper = input.closest('.form-field');
    if (!wrapper) return;

    // Remove estado anterior
    wrapper.classList.remove('tem-ok');
    wrapper.classList.add('tem-erro');
    input.classList.add('form-input--erro');
    input.classList.remove('form-input--ok');

    // Mensagem embaixo
    let msg = wrapper.querySelector('.form-campo-msg');
    if (!msg) {
      msg = document.createElement('span');
      msg.className = 'form-campo-msg';
      wrapper.appendChild(msg);
    }
    msg.textContent = mensagem;
    msg.className = 'form-campo-msg form-campo-msg--erro';

    // Acessibilidade: anuncia o erro para leitores de tela
    input.setAttribute('aria-invalid', 'true');
    input.setAttribute('aria-describedby', msg.id || (msg.id = 'msg-' + Math.random().toString(36).slice(2)));
  }

  /**
   * Marca um campo como OK.
   */
  function marcarOk(input) {
    const wrapper = input.closest('.form-field');
    if (!wrapper) return;

    wrapper.classList.remove('tem-erro');
    wrapper.classList.add('tem-ok');
    input.classList.remove('form-input--erro');
    input.classList.add('form-input--ok');

    let msg = wrapper.querySelector('.form-campo-msg');
    if (msg) msg.className = 'form-campo-msg'; // esconde

    input.removeAttribute('aria-invalid');
  }

  /**
   * Limpa o estado de um campo (volta ao neutro).
   */
  function limparEstado(input) {
    const wrapper = input.closest('.form-field');
    if (!wrapper) return;
    wrapper.classList.remove('tem-erro', 'tem-ok');
    input.classList.remove('form-input--erro', 'form-input--ok');
    const msg = wrapper.querySelector('.form-campo-msg');
    if (msg) msg.className = 'form-campo-msg';
    input.removeAttribute('aria-invalid');
  }

  // ============================================================
  // REGRAS DE VALIDAÇÃO
  // ============================================================

  const regras = {
    obrigatorio(input) {
      if (!input.value.trim()) {
        marcarErro(input, 'Este campo é obrigatório.');
        return false;
      }
      return true;
    },

    email(input) {
      const ok = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.value.trim());
      if (!ok) {
        marcarErro(input, 'Digite um e-mail válido.');
        return false;
      }
      return true;
    },

    telefone(input) {
      const digits = input.value.replace(/\D/g, '');
      if (digits.length < 12 || digits.length > 13) {
        marcarErro(input, 'Digite um telefone válido com DDD.');
        return false;
      }
      return true;
    },

    cep(input) {
      const digits = input.value.replace(/\D/g, '');
      if (digits.length !== 8) {
        marcarErro(input, 'CEP deve ter 8 dígitos.');
        return false;
      }
      return true;
    },

    senha(input) {
      if (input.value.length < 6) {
        marcarErro(input, 'A senha deve ter pelo menos 6 caracteres.');
        return false;
      }
      return true;
    },

    confirmarSenha(input, referencia) {
      if (input.value !== referencia.value) {
        marcarErro(input, 'As senhas não coincidem.');
        return false;
      }
      return true;
    },

    uf(input) {
      if (!/^[A-Za-z]{2}$/.test(input.value.trim())) {
        marcarErro(input, 'Digite a sigla do estado (ex: SP).');
        return false;
      }
      return true;
    },
  };

  /**
   * Valida um campo e retorna true/false.
   * Chama marcarOk se passou em tudo.
   */
  function validarCampo(input) {
    const tipo = input.dataset.validar;
    if (!tipo) return true;

    const tipos = tipo.split(' ');
    let valido = true;

    for (const t of tipos) {
      if (t === 'confirmar-senha') {
        const ref = document.querySelector('[data-validar~="senha"]');
        if (ref && !regras.confirmarSenha(input, ref)) { valido = false; break; }
      } else if (regras[t]) {
        if (!regras[t](input)) { valido = false; break; }
      }
    }

    if (valido) marcarOk(input);
    return valido;
  }

  // ============================================================
  // INICIALIZAÇÃO — pega todos os forms com data-validar
  // ============================================================

  function inicializar() {
    const forms = document.querySelectorAll('form[data-form-validar]');

    forms.forEach(form => {
      const campos = form.querySelectorAll('[data-validar]');

      // Valida no blur (quando sai do campo)
      campos.forEach(input => {
        input.addEventListener('blur', () => {
          // Só valida se o usuário digitou algo OU se é obrigatório
          if (input.value.trim() || input.dataset.validar.includes('obrigatorio')) {
            validarCampo(input);
          }
        });

        // Se estava com erro e o usuário começa a digitar: limpa imediatamente
        input.addEventListener('input', () => {
          if (input.classList.contains('form-input--erro')) {
            limparEstado(input);
          }
        });
      });

      // No submit: valida TUDO e bloqueia se inválido
      form.addEventListener('submit', (e) => {
        let formValido = true;
        campos.forEach(input => {
          if (!validarCampo(input)) formValido = false;
        });

        if (!formValido) {
          e.preventDefault();
          // Foca no primeiro campo com erro
          const primeiro = form.querySelector('.form-input--erro');
          if (primeiro) {
            primeiro.focus();
            primeiro.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        }
      });
    });
  }

  // Roda quando o DOM estiver pronto
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inicializar);
  } else {
    inicializar();
  }

  // Expõe ao escopo global para que buscarCep() (fora da IIFE) possa usá-las
  window.marcarErro = marcarErro;
  window.marcarOk = marcarOk;

})();

// ============================================================
// MÁSCARAS
// ============================================================

/**
 * Aplica máscara de CEP: 00000-000
 */
function mascaraCep(input) {
  let v = input.value.replace(/\D/g, '').slice(0, 8);
  if (v.length > 5) v = v.slice(0, 5) + '-' + v.slice(5);
  input.value = v;
}

/**
 * Aplica máscara de telefone: +55 11 93535-4994
 */
function mascaraTelefone(input) {
  // Remove o prefixo de exibição "+55 " antes de ler os dígitos,
  // senão o "55" do prefixo é relido a cada tecla e se acumula
  const semPrefixo = input.value.replace(/^\+55\s*/, '');
  let d = semPrefixo.replace(/\D/g, '');

  // Se mesmo assim colaram um 55 de país num número longo, remove
  if (d.length > 11 && d.startsWith('55')) {
    d = d.slice(2);
  }
  d = d.slice(0, 11); // DDD (2) + número (até 9 dígitos)

  if (d.length === 0) {
    input.value = '';
    return;
  }

  let out = '+55 ' + d.slice(0, 2); // +55 DDD
  const resto = d.slice(2);
  if (resto.length > 8) {
    out += ' ' + resto.slice(0, 5) + '-' + resto.slice(5); // celular: 5-4
  } else if (resto.length > 4) {
    out += ' ' + resto.slice(0, 4) + '-' + resto.slice(4); // fixo: 4-4
  } else if (resto.length > 0) {
    out += ' ' + resto;
  }
  input.value = out;
}

// ============================================================
// BUSCA DE CEP (ViaCEP)
// ============================================================

async function buscarCep() {
  const inputCep = document.getElementById('cep');
  const status   = document.getElementById('cep-status');
  if (!inputCep || !status) return;

  const cep = inputCep.value.replace(/\D/g, '');
  if (cep.length !== 8) return;

  status.textContent = 'Buscando…';
  status.className   = 'cep-status';

  try {
    const res  = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
    const data = await res.json();

    if (data.erro) {
      status.textContent = '✗ CEP não encontrado.';
      status.className   = 'cep-status cep-status--erro';
      marcarErro(inputCep, 'CEP não encontrado.');
      return;
    }

    document.getElementById('rua').value    = data.logradouro || '';
    document.getElementById('bairro').value = data.bairro     || '';
    document.getElementById('cidade').value = data.localidade || '';
    document.getElementById('estado').value = data.uf         || '';
    document.getElementById('numero').focus();

    status.textContent = '✓ Endereço encontrado!';
    status.className   = 'cep-status cep-status--ok';
    marcarOk(inputCep);
  } catch {
    status.textContent = '✗ Erro ao buscar CEP.';
    status.className   = 'cep-status cep-status--erro';
    marcarErro(inputCep, 'Erro ao buscar CEP. Tente novamente.');
  }
}

// ============================================================
// TOGGLE SENHA (criar conta no checkout)
// ============================================================

function toggleSenha() {
  const check = document.getElementById('criar_conta');
  const campo = document.getElementById('campo-senha');
  if (!check || !campo) return;
  campo.style.display = check.checked ? 'block' : 'none';
} 