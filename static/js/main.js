// ===== SAHAY PLATFORM - MAIN JS =====

// Quick amount buttons
document.addEventListener('DOMContentLoaded', function() {

  // Amount quick select
  const amountBtns = document.querySelectorAll('.amount-btn');
  const amountInput = document.getElementById('amount');

  if (amountBtns.length && amountInput) {
    amountBtns.forEach(btn => {
      btn.addEventListener('click', function() {
        amountBtns.forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        amountInput.value = this.dataset.amount;
      });
    });

    amountInput.addEventListener('input', function() {
      amountBtns.forEach(b => b.classList.remove('active'));
    });
  }

  // Progress bar animation
  const progressBars = document.querySelectorAll('.progress-bar[data-width]');
  progressBars.forEach(bar => {
    const width = bar.dataset.width;
    setTimeout(() => {
      bar.style.width = width + '%';
    }, 300);
  });

  // Payment method selection
  const paymentCards = document.querySelectorAll('.payment-method-card');
  const paymentInput = document.getElementById('payment_method');

  if (paymentCards.length) {
    paymentCards.forEach(card => {
      card.addEventListener('click', function() {
        paymentCards.forEach(c => c.classList.remove('selected'));
        this.classList.add('selected');
        if (paymentInput) {
          paymentInput.value = this.dataset.method;
        }
      });
    });
  }

  // Share buttons
  const currentUrl = window.location.href;
  const pageTitle = document.title;

  const fbShare = document.querySelectorAll('.share-facebook');
  fbShare.forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      const url = this.dataset.url || currentUrl;
      window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`, '_blank', 'width=600,height=400');
    });
  });

  const waShare = document.querySelectorAll('.share-whatsapp');
  waShare.forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      const url = this.dataset.url || currentUrl;
      const title = this.dataset.title || pageTitle;
      const text = `${title}\n\nএখানে ডোনেট করুন: ${url}`;
      window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank');
    });
  });

  // Copy link
  const copyBtns = document.querySelectorAll('.copy-link');
  copyBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      const url = this.dataset.url || currentUrl;
      navigator.clipboard.writeText(url).then(() => {
        const original = this.innerHTML;
        this.innerHTML = '<i class="bi bi-check2"></i> কপি হয়েছে!';
        setTimeout(() => { this.innerHTML = original; }, 2000);
      });
    });
  });

  // Number counter animation
  const counters = document.querySelectorAll('.counter-animate');
  counters.forEach(counter => {
    const target = parseFloat(counter.dataset.target);
    const prefix = counter.dataset.prefix || '';
    const suffix = counter.dataset.suffix || '';
    const isFloat = counter.dataset.float === 'true';
    let start = 0;
    const duration = 2000;
    const step = target / (duration / 16);

    const timer = setInterval(() => {
      start += step;
      if (start >= target) {
        start = target;
        clearInterval(timer);
      }
      const val = isFloat ? start.toFixed(1) : Math.floor(start).toLocaleString('bn-BD');
      counter.textContent = prefix + val + suffix;
    }, 16);
  });

});

// Format taka
function formatTaka(amount) {
  return '৳' + parseFloat(amount).toLocaleString('bn-BD');
}
