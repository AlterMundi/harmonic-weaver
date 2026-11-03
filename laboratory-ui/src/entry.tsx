// Load only the selected instrument. The facial mirror never starts the host runtime.
if (new URLSearchParams(location.search).get('mode') === 'face') {
  import('./face/App').then(({mount}) => mount()).catch(() => {
    document.getElementById('root')!.textContent = 'No se pudo abrir el espejo. Recargá la página.';
  });
} else {
  import('./main');
}
