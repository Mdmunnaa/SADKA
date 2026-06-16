/* ===== সহায়.bd — Islamic Charity Platform JS ===== */

document.addEventListener('DOMContentLoaded', () => {

  /* ── Progress bars (supports both data-width and data-pct) ── */
  document.querySelectorAll('[data-width], [data-pct]').forEach(bar => {
    const pct = parseFloat(bar.dataset.width || bar.dataset.pct) || 0;
    setTimeout(() => { bar.style.width = Math.min(pct, 100) + '%'; }, 300);
  });

  /* ── Donate Modal ── */
  const overlay  = document.getElementById('donateOverlay');
  const modalTitle = document.getElementById('modalCampaignTitle');
  const modalForm  = document.getElementById('donateForm');

  const openModal = btn => {
    if (!overlay) return;
    const { slug, title, bkash = '', nagad = '', rocket = '' } = btn.dataset;
    if (modalTitle) modalTitle.textContent = title;
    if (modalForm)  modalForm.action = '/donate/' + slug + '/';
    updatePayTabs(bkash, nagad, rocket);
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  };

  const closeModal = () => {
    if (!overlay) return;
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  };

  document.querySelectorAll('[data-donate-trigger]').forEach(btn =>
    btn.addEventListener('click', () => openModal(btn)));
  document.querySelectorAll('[data-close-modal]').forEach(el =>
    el.addEventListener('click', closeModal));
  if (overlay) overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

  function updatePayTabs(bkash, nagad, rocket) {
    const map = { bkash, nagad, rocket };
    const display = document.getElementById('payNumberDisplay');
    const inp     = document.getElementById('modalPaymentMethod');
    let first = null, firstMethod = null;

    document.querySelectorAll('.pay-tab[data-method]').forEach(tab => {
      const m = tab.dataset.method;
      const num = map[m] || '';
      tab.style.display = num ? '' : 'none';
      tab.dataset.num = num;
      tab.classList.remove('active');
      if (num && !first) { first = num; firstMethod = m; }
    });

    if (first) {
      const firstTab = document.querySelector(`.pay-tab[data-method="${firstMethod}"]`);
      if (firstTab) firstTab.classList.add('active');
      if (display) display.textContent = first;
      if (inp) inp.value = firstMethod;
    }
  }

  document.querySelectorAll('.pay-tab[data-method]').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.pay-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const display = document.getElementById('payNumberDisplay');
      if (display) display.textContent = tab.dataset.num || '—';
      const inp = document.getElementById('modalPaymentMethod');
      if (inp) inp.value = tab.dataset.method;
    });
  });

  /* ── Amount pills ── */
  document.querySelectorAll('.pill[data-amount]').forEach(pill => {
    pill.addEventListener('click', () => {
      pill.closest('.amount-pills')?.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const inp = pill.closest('.modal-body, form')?.querySelector('input[name="amount"]');
      if (inp) inp.value = pill.dataset.amount;
    });
  });
  document.querySelectorAll('input[name="amount"]').forEach(inp =>
    inp.addEventListener('input', () =>
      inp.closest('.modal-body, form')?.querySelectorAll('.pill').forEach(p => p.classList.remove('active'))));

  /* ── Detail page tabs ── */
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.tab)?.classList.add('active');
    });
  });

  /* ── Share buttons ── */
  document.querySelectorAll('[data-share="facebook"]').forEach(btn =>
    btn.addEventListener('click', e => {
      e.preventDefault();
      window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(btn.dataset.url || location.href)}`, '_blank', 'width=620,height=420');
    }));

  document.querySelectorAll('[data-share="whatsapp"]').forEach(btn =>
    btn.addEventListener('click', e => {
      e.preventDefault();
      const url   = btn.dataset.url   || location.href;
      const title = btn.dataset.title || document.title;
      window.open(`https://wa.me/?text=${encodeURIComponent(title + '\n\n' + url)}`, '_blank');
    }));

  document.querySelectorAll('[data-share="copy"]').forEach(btn =>
    btn.addEventListener('click', () => {
      navigator.clipboard.writeText(btn.dataset.url || location.href).then(() => {
        const orig = btn.innerHTML;
        btn.innerHTML = '<i class="bi bi-check2"></i> কপি হয়েছে!';
        btn.style.color = 'var(--teal-700)';
        setTimeout(() => { btn.innerHTML = orig; btn.style.color = ''; }, 2500);
      });
    }));

  /* ── Share buttons (old class-based) ── */
  document.querySelectorAll('.share-facebook').forEach(btn =>
    btn.addEventListener('click', e => {
      e.preventDefault();
      const url = btn.dataset.url || location.href;
      window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`, '_blank', 'width=620,height=420');
    }));

  document.querySelectorAll('.share-whatsapp').forEach(btn =>
    btn.addEventListener('click', e => {
      e.preventDefault();
      const url   = btn.dataset.url   || location.href;
      const title = btn.dataset.title || document.title;
      window.open(`https://wa.me/?text=${encodeURIComponent(title + '\n\n' + url)}`, '_blank');
    }));

});
