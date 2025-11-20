document.addEventListener('DOMContentLoaded', () => {
  // nav toggle for mobile
  const navToggle = document.getElementById('navToggle');
  const mainNav = document.getElementById('mainNav');
  navToggle && navToggle.addEventListener('click', () => {
    mainNav.style.display = (mainNav.style.display === 'flex') ? 'none' : 'flex';
  });

  // current year
  const y = new Date().getFullYear();
  const yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = y;
});
