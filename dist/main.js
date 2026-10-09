'use strict';

// Enhance a fully readable static gallery. No timers, network calls, or storage.
(() => {
  const showcase = document.querySelector('.theme-showcase');
  if (!showcase) return;
  const figures = [...showcase.querySelectorAll('[data-theme]')];
  const controls = showcase.querySelector('.theme-controls');
  const buttons = [...controls.querySelectorAll('[data-pick]')];
  const positions = new Map([[0, 'current'], [-1, 'previous'], [1, 'next'], [-2, 'far-previous'], [2, 'far-next']]);
  const select = (index, announce = true) => {
    figures.forEach((figure, i) => {
      let offset = (i - index + figures.length) % figures.length;
      if (offset > figures.length / 2) offset -= figures.length;
      figure.className = positions.get(offset) || '';
      figure.setAttribute('aria-hidden', String(i !== index));
    });
    buttons.forEach((button, i) => button.setAttribute('aria-pressed', String(i === index)));
    const {name, mode, note} = figures[index].dataset;
    document.getElementById('theme-counter').textContent = `${String(index + 1).padStart(2, '0')} / ${String(figures.length).padStart(2, '0')} · ${mode.toUpperCase()}`;
    document.getElementById('theme-name').textContent = name;
    document.getElementById('theme-note').textContent = note;
    if (announce) document.getElementById('theme-announcement').textContent = `${name} theme. ${note}`;
  };
  buttons.forEach((button, index) => {
    button.addEventListener('click', () => select(index));
    button.addEventListener('keydown', (event) => {
      let next;
      if (event.key === 'ArrowRight') next = (index + 1) % buttons.length;
      if (event.key === 'ArrowLeft') next = (index - 1 + buttons.length) % buttons.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = buttons.length - 1;
      if (next === undefined) return;
      event.preventDefault();
      buttons[next].focus();
      select(next);
    });
  });
  select(0, false);
  showcase.classList.add('theme-enhanced');
  showcase.closest('.theme-layout').classList.add('theme-ready');
  controls.hidden = false;
})();

// Escape dismisses the hover card without interrupting its direct link.
(() => {
  const link = document.querySelector('.support-link');
  if (!link) return;
  const reset = () => link.classList.remove('sheet-dismissed');
  link.addEventListener('pointerleave', reset);
  link.addEventListener('focusout', reset);
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && link.matches(':hover, :focus-visible')) {
      link.classList.add('sheet-dismissed');
    }
  });
})();

(() => {
  const button = document.querySelector('.copy-install');
  if (!button || !navigator.clipboard) return;
  button.hidden = false;
  button.addEventListener('click', async () => {
    const status = document.getElementById('install-status');
    try {
      await navigator.clipboard.writeText(document.getElementById('brew-command').textContent);
      status.textContent = 'Install command copied.';
      button.textContent = 'Copied';
    } catch {
      status.textContent = 'Select the command and copy it manually.';
    }
  });
})();
