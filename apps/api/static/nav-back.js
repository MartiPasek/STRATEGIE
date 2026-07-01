/* nav-back.js (Marti 1.7.2026): univerzální tlačítko „‹ Zpět" pro samostatné
   přehledy otevřené z ERP ikonek / cockpitu.
   Logika (Marti 1.7. v2 — přehledy se otvírají jako popup okna, i s noopener):
     1) je kam v historii (navigace ve stejném okně) → history.back()
     2) jinak = samostatné okno → window.close() (návrat do ERP)
     3) když se okno nezavře (není popup) → fallback domů.
   Vlož: <script src="/static/nav-back.js"></script> */
(function () {
  if (window.__navBack) return; window.__navBack = 1;
  function goBack() {
    try {
      if (window.history && history.length > 1) { history.back(); return; }
    } catch (e) {}
    // samostatné okno (popup z ERP, klidně i noopener) → zavřít
    try { window.close(); } catch (e) {}
    // pokud se okno nezavřelo (nebyl to popup), po chvíli fallback domů
    setTimeout(function () { try { location.href = "/"; } catch (e) {} }, 250);
  }
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
    b.onclick = goBack;
    document.body.appendChild(b);
  }
  // Marti 1.7.2026: ESC = zpět (globálně, čisté — nikdo nic nehledá).
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape" && e.keyCode !== 27) return;
    if (e.defaultPrevented) return;
    var t = e.target || {}, tag = (t.tagName || "").toUpperCase();
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || t.isContentEditable) return;
    goBack();
  }, false);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", add);
  else add();
})();
