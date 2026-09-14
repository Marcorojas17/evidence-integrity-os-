/* ============================================================
   Verificación local de paquetes .evidence
   El archivo NUNCA se sube al servidor.
   ============================================================ */

(function () {
  'use strict';

  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('file');
  const fileInfo = document.getElementById('file-info');
  const verifyBtn = document.getElementById('verify-btn');
  const result = document.getElementById('result');

  if (!dropzone || !fileInput) return;

  let selectedFile = null;

  dropzone.addEventListener('click', () => fileInput.click());

  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  });

  function handleFile(file) {
    selectedFile = file;
    if (fileInfo) {
      fileInfo.style.display = 'block';
      fileInfo.innerHTML = `
        <dl>
          <dt>nombre</dt><dd>${escapeHtml(file.name)}</dd>
          <dt>tamaño</dt><dd>${formatBytes(file.size)}</dd>
          <dt>tipo</dt><dd>${escapeHtml(file.type || 'desconocido')}</dd>
        </dl>
      `;
    }
    if (verifyBtn) verifyBtn.disabled = false;
  }

  function formatBytes(n) {
    if (n < 1024) return n + ' B';
    if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' KiB';
    if (n < 1024 * 1024 * 1024) return (n / 1024 / 1024).toFixed(1) + ' MiB';
    return (n / 1024 / 1024 / 1024).toFixed(1) + ' GiB';
  }

  function escapeHtml(s) {
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }

  if (verifyBtn) {
    verifyBtn.addEventListener('click', async () => {
      if (!selectedFile) return;

      verifyBtn.disabled = true;
      result.style.display = 'block';
      result.className = 'result';
      result.innerHTML = '<div class="result-title">Procesando…</div>';

      try {
        const formData = new FormData();
        formData.append('file', selectedFile);

        const response = await fetch('/evidence/verify', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        renderResult(data);
      } catch (err) {
        result.className = 'result invalid';
        result.innerHTML = `
          <div class="result-title">ERROR</div>
          <p>No se pudo verificar el paquete: ${escapeHtml(err.message)}</p>
        `;
      } finally {
        verifyBtn.disabled = false;
      }
    });
  }

  function renderResult(data) {
    const cls = data.valid ? 'valid' : 'invalid';
    const title = data.valid ? 'PAQUETE VÁLIDO' : 'PAQUETE INVÁLIDO';

    const stepsHtml = (data.steps || [])
      .map(
        (s) =>
          `<li class="${s.passed ? '' : 'fail'}">${escapeHtml(s.name)} — ${
            s.passed ? 'ok' : 'fail'
          }${s.detail ? ` (${escapeHtml(s.detail)})` : ''}</li>`
      )
      .join('');

    result.className = 'result ' + cls;
    result.innerHTML = `
      <div class="result-title">${title}</div>
      ${data.evidence_id ? `<p><strong>evidence_id:</strong> <code>${escapeHtml(data.evidence_id)}</code></p>` : ''}
      ${data.manifest_digest ? `<p><strong>manifest_digest:</strong> <code>${escapeHtml(data.manifest_digest)}</code></p>` : ''}
      ${data.tsa_gen_time ? `<p><strong>tsa_gen_time:</strong> <code>${escapeHtml(data.tsa_gen_time)}</code></p>` : ''}
      <h3 style="font-family: var(--mono); font-size: 13px; color: var(--text-dim); margin: 16px 0 8px;">pasos</h3>
      <ul class="steps">${stepsHtml}</ul>
    `;
  }
})();
