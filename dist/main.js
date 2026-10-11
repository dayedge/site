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
  const modes = document.querySelector('.install-modes');
  if (!modes) return;
  const button = document.querySelector('.copy-install');
  const command = document.getElementById('brew-command');
  const status = document.getElementById('install-status');
  const guidance = document.getElementById('install-guidance');
  const installGuidance = guidance.innerHTML;
  let mode = 'install';
  modes.hidden = false;
  modes.addEventListener('change', (event) => {
    mode = event.target.value;
    const updating = mode === 'update';
    command.textContent = updating
      ? 'brew update && brew upgrade --cask dayedge'
      : 'brew install --cask dayedge/tap/dayedge';
    guidance.innerHTML = updating ? 'Installed with Homebrew? Run this in Terminal.' : installGuidance;
    document.querySelector('.install-update-heading').hidden = !updating;
    document.querySelector('.install-note').hidden = updating;
    button.textContent = 'Copy';
    button.setAttribute('aria-label', `Copy Homebrew ${mode} command`);
    status.textContent = '';
  });
  if (!navigator.clipboard) return;
  button.hidden = false;
  button.addEventListener('click', async () => {
    const copiedCommand = command.textContent;
    const copiedMode = mode;
    try {
      await navigator.clipboard.writeText(copiedCommand);
      if (command.textContent !== copiedCommand) return;
      status.textContent = `${copiedMode === 'install' ? 'Install' : 'Update'} command copied.`;
      button.textContent = 'Copied';
    } catch {
      if (command.textContent === copiedCommand) status.textContent = 'Select the command and copy it manually.';
    }
  });
})();

(() => {
  const install = document.querySelector('.nav-install');
  const heroInstall = document.querySelector('.hero .actions .primary');
  if (!install || !heroInstall || !('IntersectionObserver' in window)) return;
  const headerHeight = document.querySelector('.navigation').offsetHeight;
  const setHeroVisible = (visible) => {
    install.classList.toggle('is-hero-visible', visible);
    install.inert = visible;
    if (visible) install.setAttribute('aria-hidden', 'true');
    else install.removeAttribute('aria-hidden');
  };
  const rect = heroInstall.getBoundingClientRect();
  const visibleHeight = Math.max(0, Math.min(rect.bottom, window.innerHeight) - Math.max(rect.top, headerHeight));
  setHeroVisible(visibleHeight >= rect.height * 0.25);
  new IntersectionObserver(([entry]) => {
    setHeroVisible(entry.isIntersecting && entry.intersectionRatio >= 0.25);
  }, {rootMargin: `-${headerHeight}px 0px 0px 0px`, threshold: [0, 0.25]}).observe(heroInstall);
})();
