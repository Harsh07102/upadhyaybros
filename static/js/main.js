// ═══════════════════════════════════
// UBC - Main JavaScript
// ═══════════════════════════════════

// ── Navbar scroll effect ──
const navbar = document.getElementById('navbar');
const scrollTopBtn = document.createElement('button');
scrollTopBtn.className = 'scroll-top';
scrollTopBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
document.body.appendChild(scrollTopBtn);
scrollTopBtn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

window.addEventListener('scroll', () => {
  if (window.scrollY > 80) {
    navbar?.classList.add('scrolled');
    scrollTopBtn.classList.add('visible');
  } else {
    navbar?.classList.remove('scrolled');
    scrollTopBtn.classList.remove('visible');
  }
});

// ── Hamburger menu ──
const hamburger = document.getElementById('hamburger');
const navLinks = document.getElementById('navLinks');
hamburger?.addEventListener('click', () => navLinks.classList.toggle('open'));
document.addEventListener('click', (e) => {
  if (!e.target.closest('.navbar')) navLinks?.classList.remove('open');
});

// ── Hero Slider ──
function initSlider() {
  const slides = document.querySelectorAll('.slide');
  const dots = document.querySelectorAll('.dot');
  const track = document.querySelector('.slider-track');
  if (!track || slides.length === 0) return;

  let current = 0;
  let timer;

  function goTo(idx) {
    slides[current].classList.remove('active');
    dots[current]?.classList.remove('active');
    current = (idx + slides.length) % slides.length;
    slides[current].classList.add('active');
    dots[current]?.classList.add('active');
    track.style.transform = `translateX(-${current * 100}%)`;
  }

  function next() { goTo(current + 1); }
  function start() { timer = setInterval(next, 5000); }
  function stop() { clearInterval(timer); }

  document.querySelector('.slider-next')?.addEventListener('click', () => { stop(); next(); start(); });
  document.querySelector('.slider-prev')?.addEventListener('click', () => { stop(); goTo(current - 1); start(); });
  dots.forEach((dot, i) => dot.addEventListener('click', () => { stop(); goTo(i); start(); }));

  slides[0].classList.add('active');
  dots[0]?.classList.add('active');
  start();
}
initSlider();

// ── Scroll animations ──
const fadeEls = document.querySelectorAll('.fade-up');
const observer = new IntersectionObserver((entries) => {
  entries.forEach((e, i) => {
    if (e.isIntersecting) {
      setTimeout(() => e.target.classList.add('visible'), i * 80);
    }
  });
}, { threshold: 0.12 });
fadeEls.forEach(el => observer.observe(el));

// ── Counter animation ──
function animateCounter(el, target, suffix = '') {
  let start = 0;
  const duration = 2000;
  const step = target / (duration / 16);
  const timer = setInterval(() => {
    start = Math.min(start + step, target);
    el.textContent = Math.floor(start) + suffix;
    if (start >= target) clearInterval(timer);
  }, 16);
}

const statsObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      document.querySelectorAll('.stat-number').forEach(el => {
        const val = parseInt(el.dataset.val);
        const suf = el.dataset.suffix || '';
        animateCounter(el, val, suf);
      });
      statsObserver.disconnect();
    }
  });
}, { threshold: 0.5 });
const statsBar = document.querySelector('.stats-bar');
if (statsBar) statsObserver.observe(statsBar);

// ── Enquiry Modal ──
function openModal(productName) {
  const modal = document.getElementById('enquiryModal');
  const pName = document.getElementById('modalProductName');
  const pInput = document.getElementById('enquiryProduct');
  if (productName) {
    pName.textContent = 'Enquiring about: ' + productName;
    pInput.value = productName;
  } else {
    pName.textContent = 'Get in touch with our experts';
    pInput.value = '';
  }
  modal.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  document.getElementById('enquiryModal').classList.remove('active');
  document.body.style.overflow = '';
  document.getElementById('formMsg').className = 'form-msg';
  document.getElementById('formMsg').textContent = '';
  document.getElementById('enquiryForm').reset();
}

document.getElementById('enquiryModal')?.addEventListener('click', function(e) {
  if (e.target === this) closeModal();
});

document.getElementById('enquiryForm')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  const btn = this.querySelector('.btn-submit');
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
  btn.disabled = true;

  const data = {
    name: document.getElementById('eName').value,
    contact: document.getElementById('eContact').value,
    email: document.getElementById('eEmail').value,
    product: document.getElementById('enquiryProduct').value,
    requirements: document.getElementById('eReq').value,
  };

  try {
    const res = await fetch('/api/enquiry', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    const result = await res.json();
    const msg = document.getElementById('formMsg');
    if (result.success) {
      msg.className = 'form-msg success';
      msg.textContent = '✓ Enquiry submitted! We will contact you shortly.';
      this.reset();
      setTimeout(closeModal, 2500);
    } else {
      msg.className = 'form-msg error';
      msg.textContent = result.message || 'Something went wrong. Please try again.';
    }
  } catch {
    document.getElementById('formMsg').className = 'form-msg error';
    document.getElementById('formMsg').textContent = 'Network error. Please try again.';
  }
  btn.innerHTML = '<i class="fas fa-paper-plane"></i> Submit Enquiry';
  btn.disabled = false;
});

// ── Contact Form (home page) ──
document.getElementById('contactForm')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  const btn = this.querySelector('.btn-submit');
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
  btn.disabled = true;

  const data = {
    name: document.getElementById('cName').value,
    contact: document.getElementById('cPhone').value,
    email: document.getElementById('cEmail').value,
    product: document.getElementById('cProduct').value,
    requirements: document.getElementById('cMessage').value,
  };

  try {
    const res = await fetch('/api/enquiry', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    const result = await res.json();
    const msg = document.getElementById('contactMsg');
    msg.style.display = 'block';
    if (result.success) {
      msg.className = 'form-msg success';
      msg.textContent = '✓ Message sent! We will get back to you soon.';
      this.reset();
    } else {
      msg.className = 'form-msg error';
      msg.textContent = result.message;
    }
  } catch {
    document.getElementById('contactMsg').textContent = 'Error. Please try again.';
  }
  btn.innerHTML = '<i class="fas fa-paper-plane"></i> Send Message';
  btn.disabled = false;
});
