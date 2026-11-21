(function () {
  var q = document.getElementById('q');
  if (!q) return;
  var subjects = [].slice.call(document.querySelectorAll('.subject'));
  var shown = document.getElementById('shown');
  var none = document.getElementById('none');

  function apply() {
    var term = q.value.trim().toLowerCase();
    var total = 0;
    subjects.forEach(function (s) {
      var n = 0;
      [].forEach.call(s.querySelectorAll('.row'), function (r) {
        var ok = !term || r.dataset.text.indexOf(term) !== -1;
        r.hidden = !ok;
        if (ok) n++;
      });
      s.hidden = n === 0;
      total += n;
    });
    shown.textContent = total + (total === 1 ? ' result' : ' results');
    none.hidden = total !== 0;
  }

  q.addEventListener('input', apply);
})();
