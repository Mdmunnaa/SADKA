/* ===== সহায়.bd — Main JS ===== */

document.addEventListener('DOMContentLoaded', () => {

  /* ── Navbar toggle (mobile) ── */
  const toggler = document.getElementById('navToggler');
  const navCollapse = document.getElementById('navCollapse');
  if (toggler && navCollapse) {
    toggler.addEventListener('click', () => navCollapse.classList.toggle('open'));
    document.addEventListener('click', e => {
      if (!toggler.contains(e.target) && !navCollapse.contains(e.target))
        navCollapse.classList.remove('open');
    });
  }

  /* ── Animate progress bars ── */
  const animateBars = () => {
    document.querySelectorAll('[data-pct]').forEach(bar => {
      const pct = parseFloat(bar.dataset.pct) || 0;
      setTimeout(() => { bar.style.width = Math.min(pct, 100) + '%'; }, 200);
    });
  };
  animateBars();

  /* ── DONATE MODAL (As-Sunnah style) ── */
  const overlay = document.getElementById('donateOverlay');
  const modalCampaignSlug  = document.getElementById('modalCampaignSlug');
  const modalCampaignTitle = document.getElementById('modalCampaignTitle');
  const modalBkash  = document.getElementById('modalBkash');
  const modalNagad  = document.getElementById('modalNagad');
  const modalRocket = document.getElementById('modalRocket');
  const modalForm   = document.getElementById('donateForm');

  const openModal = (btn) => {
    if (!overlay) return;
    const slug   = btn.dataset.slug;
    const title  = btn.dataset.title;
    const bkash  = btn.dataset.bkash  || '';
    const nagad  = btn.dataset.nagad  || '';
    const rocket = btn.dataset.rocket || '';

    if (modalCampaignSlug)  modalCampaignSlug.value  = slug;
    if (modalCampaignTitle) modalCampaignTitle.textContent = title;
    if (modalForm) modalForm.action = '/donate/' + slug + '/';

    // Payment numbers
    updatePayNumbers(bkash, nagad, rocket);
    selectFirstPay(bkash, nagad, rocket);

    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  };

  const closeModal = () => {
    if (!overlay) return;
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  };

  // Open on "Donate Now" buttons
  document.querySelectorAll('[data-donate-trigger]').forEach(btn => {
    btn.addEventListener('click', () => openModal(btn));
  });

  // Close buttons
  document.querySelectorAll('[data-close-modal]').forEach(el => {
    el.addEventListener('click', closeModal);
  });
  if (overlay) {
    overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(); });
  }
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

  /* ── Amount pills ── */
  document.querySelectorAll('.pill[data-amount]').forEach(pill => {
    pill.addEventListener('click', () => {
      const container = pill.closest('.amount-pills');
      container?.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const input = pill.closest('.modal-body, form')?.querySelector('input[name="amount"]');
      if (input) input.value = pill.dataset.amount;
    });
  });

  // Clear pill active if typed
  document.querySelectorAll('input[name="amount"]').forEach(inp => {
    inp.addEventListener('input', () => {
      inp.closest('.modal-body, form')?.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
    });
  });

  /* ── Payment method tabs inside modal ── */
  function updatePayNumbers(bkash, nagad, rocket) {
    const display = document.getElementById('payNumberDisplay');
    if (!display) return;
    const tabs = document.querySelectorAll('.pay-tab[data-method]');
    tabs.forEach(t => {
      const m = t.dataset.method;
      t.style.display = (m === 'bkash' && bkash) || (m === 'nagad' && nagad) || (m === 'rocket' && rocket) ? '' : 'none';
    });
    // data on tabs
    if (bkash) document.querySelector('.pay-tab[data-method="bkash"]')?.setAttribute('data-num', bkash);
    if (nagad) document.querySelector('.pay-tab[data-method="nagad"]')?.setAttribute('data-num', nagad);
    if (rocket) document.querySelector('.pay-tab[data-method="rocket"]')?.setAttribute('data-num', rocket);
  }

  function selectFirstPay(bkash, nagad, rocket) {
    const first = bkash || nagad || rocket;
    const method = bkash ? 'bkash' : nagad ? 'nagad' : 'rocket';
    document.querySelectorAll('.pay-tab').forEach(t => t.classList.remove('active'));
    const tab = document.querySelector(`.pay-tab[data-method="${method}"]`);
    if (tab) {
      tab.classList.add('active');
      const display = document.getElementById('payNumberDisplay');
      if (display) display.textContent = first;
      const inp = document.getElementById('modalPaymentMethod');
      if (inp) inp.value = method;
    }
  }

  document.querySelectorAll('.pay-tab[data-method]').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.pay-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const num = tab.dataset.num || '';
      const display = document.getElementById('payNumberDisplay');
      if (display) display.textContent = num || '—';
      const inp = document.getElementById('modalPaymentMethod');
      if (inp) inp.value = tab.dataset.method;
    });
  });

  /* ── Detail page tabs ── */
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.tab;
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(target)?.classList.add('active');
    });
  });

  /* ── Share buttons ── */
  document.querySelectorAll('[data-share="facebook"]').forEach(btn => {
    btn.addEventListener('click', e => {
      e.preventDefault();
      const url = btn.dataset.url || location.href;
      window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`, '_blank', 'width=620,height=420');
    });
  });

  document.querySelectorAll('[data-share="whatsapp"]').forEach(btn => {
    btn.addEventListener('click', e => {
      e.preventDefault();
      const url   = btn.dataset.url   || location.href;
      const title = btn.dataset.title || document.title;
      window.open(`https://wa.me/?text=${encodeURIComponent(title + '\n\n' + url)}`, '_blank');
    });
  });

  document.querySelectorAll('[data-share="copy"]').forEach(btn => {
    btn.addEventListener('click', () => {
      navigator.clipboard.writeText(btn.dataset.url || location.href).then(() => {
        const orig = btn.innerHTML;
        btn.innerHTML = '<i class="bi bi-check2"></i> কপি হয়েছে!';
        btn.style.color = 'var(--green-700)';
        setTimeout(() => { btn.innerHTML = orig; btn.style.color = ''; }, 2500);
      });
    });
  });

});
