/* nav-back.js (Marti 1.7.2026): univerzální tlačítko „‹ Zpět" pro samostatné
   přehledy otevřené z ERP ikonek / cockpitu. Pořadí: history.back → zavřít
   popup (pokud otevřeno z okna) → fallback domů. Vlož: <script src="/static/nav-back.js"></script> */
(function () {
  if (window.__navBack) return; window.__navBack = 1;
  function add() {
    if (document.getElementById("navBackBtn")) return;
    if (!document.body) return;
    var b = document.createElement("button");
    b.id = "navBackBtn"; b.type = "button"; b.textContent = "‹ Zpět"; b.title = "Zpět";
    b.style.cssText = "position:fixed;bottom:14px;left:14px;z-index:2147483000;" +
      "background:#16181c;border:1px solid #2a2e35;color:#2dd4bf;padding:9px 15px;" +
      "border-radius:11px;font:600 13px system-ui,-apple-system,Segoe UI,sans-serif;" +
      "cursor:pointer;box-shadow:0 3px 10px rgba(0,0,0,.45);opacity:.9";
    b.onmouseenter = function () { b.style.opacity = "1"; };
    b.onmouseleave = function () { b.style.opacity = ".9"; };
    b.onclick = function () {
      try {
        if (window.history && history.length > 1) { history.back(); return; }
        if (window.opener && !window.opener.closed) { window.close(); return; }
      } catch (e) {}
      location.href = "/";
    };
    document.body.appendChild(b);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", add);
  else add();
})();
