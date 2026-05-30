(function () {
  // No mostrar si ya está instalada como PWA
  if (window.matchMedia('(display-mode: standalone)').matches) return;

  let deferredPrompt = null;

  const banner = document.getElementById('pwa-install-banner');
  const btnInstall = document.getElementById('pwa-install-btn');
  const btnDismiss = document.getElementById('pwa-install-dismiss');

  window.addEventListener('beforeinstallprompt', function (e) {
    e.preventDefault();
    deferredPrompt = e;
    if (banner) banner.classList.remove('hidden');
  });

  if (btnInstall) {
    btnInstall.addEventListener('click', function () {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      deferredPrompt.userChoice.then(function (result) {
        deferredPrompt = null;
        if (banner) banner.classList.add('hidden');
      });
    });
  }

  if (btnDismiss) {
    btnDismiss.addEventListener('click', function () {
      if (banner) banner.classList.add('hidden');
    });
  }

  // Ocultar una vez instalada
  window.addEventListener('appinstalled', function () {
    if (banner) banner.classList.add('hidden');
    deferredPrompt = null;
  });
})();
