// xinhertz v2 — shared scripts
(function(){
  // mobile nav
  var burger = document.querySelector('.burger');
  var links = document.querySelector('.nav-links');
  if (burger && links) {
    burger.addEventListener('click', function(){ links.classList.toggle('open'); });
    links.querySelectorAll('a').forEach(function(a){
      a.addEventListener('click', function(){ links.classList.remove('open'); });
    });
  }

  // hero part-number search -> contact page with prefilled part
  var searchForm = document.getElementById('part-search');
  if (searchForm) {
    searchForm.addEventListener('submit', function(e){
      e.preventDefault();
      var q = document.getElementById('part-input').value.trim();
      window.location.href = 'contact.html' + (q ? '?part=' + encodeURIComponent(q) : '');
    });
  }

  // prefill quote form from ?part=
  var params = new URLSearchParams(window.location.search);
  var part = params.get('part');
  var bomField = document.getElementById('f-bom');
  if (part && bomField && !bomField.value) {
    bomField.value = 'Part number: ' + part + '\nQuantity: \nTarget price: \n';
  }

  // quote form -> WhatsApp deep link (no backend needed)
  var form = document.getElementById('quote-form');
  if (form) {
    form.addEventListener('submit', function(e){
      e.preventDefault();
      var name = document.getElementById('f-name').value.trim();
      var email = document.getElementById('f-email').value.trim();
      var bom = document.getElementById('f-bom').value.trim();
      var msg = 'Hi xinhertz! I would like a quote.\n'
        + (name ? 'Name: ' + name + '\n' : '')
        + (email ? 'Email: ' + email + '\n' : '')
        + 'Details:\n' + bom;
      window.open('https://wa.me/85257177318?text=' + encodeURIComponent(msg), '_blank');
    });
  }

  // footer year
  var y = document.getElementById('year');
  if (y) y.textContent = new Date().getFullYear();
})();
