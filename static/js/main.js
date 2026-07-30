// ---- Menu mobile ----
const burger = document.getElementById('burger');
const menu = document.getElementById('menu');
if (burger && menu) {
  burger.addEventListener('click', () => menu.classList.toggle('open'));
  menu.querySelectorAll('a').forEach(a => a.addEventListener('click', () => menu.classList.remove('open')));
}

// ---- Apparition au défilement ----
const io = new IntersectionObserver(
  entries => entries.forEach(x => { if (x.isIntersecting) x.target.classList.add('in'); }),
  { threshold: 0.12 }
);
document.querySelectorAll('.reveal').forEach(el => io.observe(el));

// ---- Compteurs animés ----
function animateCount(el) {
  const target = +el.dataset.count;
  const decimal = el.dataset.count === '149'; // cas 14,9 %
  let cur = 0;
  const step = Math.max(1, Math.ceil(target / 55));
  const timer = setInterval(() => {
    cur += step;
    if (cur >= target) { cur = target; clearInterval(timer); }
    el.textContent = decimal ? (cur / 10).toFixed(1).replace('.', ',') : cur.toLocaleString('fr-FR');
  }, 24);
}
const cio = new IntersectionObserver(entries => entries.forEach(en => {
  if (en.isIntersecting) { animateCount(en.target); cio.unobserve(en.target); }
}), { threshold: 0.6 });
document.querySelectorAll('[data-count]').forEach(el => cio.observe(el));

// ---- Montants de don ----
document.querySelectorAll('.amount').forEach(a => {
  a.addEventListener('click', () => {
    document.querySelectorAll('.amount').forEach(x => x.classList.remove('sel'));
    a.classList.add('sel');
    const custom = document.getElementById('montant-custom');
    if (custom) custom.value = a.dataset.val;
  });
});

// ---- Envoi des formulaires (AJAX vers l'API Node) ----
document.querySelectorAll('form[data-endpoint]').forEach(form => {
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const msg = form.querySelector('.form-msg');
    const btn = form.querySelector('button[type=submit]');
    const original = btn ? btn.textContent : '';
    if (btn) { btn.disabled = true; btn.textContent = 'Envoi…'; }
    try {
      const formData = new FormData(form);
      const contientFichier = [...formData.values()].some(v => v instanceof File && v.size > 0);
      let res;
      if (contientFichier) {
        // Laisser le navigateur fixer le Content-Type (multipart + boundary)
        res = await fetch(form.dataset.endpoint, { method: 'POST', body: formData });
      } else {
        const data = Object.fromEntries(formData.entries());
        res = await fetch(form.dataset.endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
      }
      const out = await res.json();
      if (msg) {
        msg.className = 'form-msg ' + (out.ok ? 'ok' : 'err');
        msg.textContent = out.message || (out.ok ? 'Message envoyé, merci !' : 'Une erreur est survenue.');
      }
      if (out.ok) form.reset();
    } catch (err) {
      if (msg) { msg.className = 'form-msg err'; msg.textContent = 'Impossible d’envoyer pour le moment. Réessayez plus tard.'; }
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = original; }
      if (msg) msg.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  });
});
