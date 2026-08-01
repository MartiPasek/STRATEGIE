# -*- coding: utf-8 -*-
# Mirror scheduler self-heal patcher (C23, 31.7.2026).
# Bezpecne: fetch + reset --hard origin/main (srovna zamotany lokal), pak 2 male
# chirurgicke edity (idempotentni, s kontrolou kotev), py_compile, commit, push.
# Nic velkeho se nekomituje; kdyz kotva nesedi, skript spadne PRED commitem.
import subprocess, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SDIR = os.path.join(ROOT, "scripts")

def run(cmd):
    print(">>", " ".join(cmd)); sys.stdout.flush()
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if (r.stdout or "").strip(): print(r.stdout.strip())
    if (r.stderr or "").strip(): print(r.stderr.strip())
    return r.returncode

print("=== 1) srovnani lokalu na origin/main ===")
if run(["git", "fetch", "origin"]) != 0: sys.exit("FETCH FAIL")
if run(["git", "reset", "--hard", "origin/main"]) != 0: sys.exit("RESET FAIL")

def rd(p):
    with open(os.path.join(SDIR, p), "r", encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")

r_insert_lf = rd("_sh_r_insert.txt")
a_anchor_lf = rd("_sh_a_anchor.txt")
a_replace_lf = rd("_sh_a_replace.txt")

rp = os.path.join(ROOT, "modules", "erp", "api", "router.py")
ap = os.path.join(ROOT, "modules", "erp", "api", "automat.py")

def patch(path, do):
    with open(path, "rb") as f: raw = f.read()
    nl = "\r\n" if b"\r\n" in raw else "\n"
    txt = raw.decode("utf-8")
    if "_mirror_sched_ensure_alive" in txt:
        print(os.path.basename(path), "- marker uz pritomen, preskakuji"); return
    txt2 = do(txt, nl)
    with open(path, "wb") as f: f.write(txt2.encode("utf-8"))
    print(os.path.basename(path), "- upraveno (nl=%r)" % nl)

def do_router(txt, nl):
    anchor = "def _mirror_sched_stop_now():"
    n = txt.count(anchor)
    if n != 1: sys.exit("router.py: kotva '%s' x%d (ceka se 1)" % (anchor, n))
    return txt.replace(anchor, r_insert_lf.replace("\n", nl) + anchor, 1)

def do_automat(txt, nl):
    a = a_anchor_lf.replace("\n", nl); b = a_replace_lf.replace("\n", nl)
    n = txt.count(a)
    if n != 1: sys.exit("automat.py: kotva (if _SCHED_STOP/break/loop) x%d (ceka se 1)" % n)
    return txt.replace(a, b, 1)

print("=== 2) aplikace patche ===")
patch(rp, do_router)
patch(ap, do_automat)

print("=== 3) py_compile ===")
for f in (rp, ap):
    r = subprocess.run([sys.executable, "-m", "py_compile", f],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(r.stderr or r.stdout); sys.exit("PY_COMPILE FAIL: " + f)
print("py_compile OK (oba soubory)")

print("=== 4) commit + push ===")
run(["git", "add", "modules/erp/api/router.py", "modules/erp/api/automat.py"])
if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0:
    print("Nic ke commitu - self-heal uz je na origin/main. Koncim."); sys.exit(0)
if run(["git", "commit", "-m",
        "fix(mirror-sched): self-heal - automat hlida a ozivi mrtvy mirror loop (C23 31.7.)"]) != 0:
    sys.exit("COMMIT FAIL")
if run(["git", "push"]) != 0:
    sys.exit("PUSH FAIL (nekdo mezitim pushnul? Spust skript znovu - je bezpecny.)")
print("")
print("=== HOTOVO: self-heal je na origin/main. ===")
print("Rekni Claudovi 'hotovo' - spusti cloud deploy (pull+restart) pres most a overi.")
