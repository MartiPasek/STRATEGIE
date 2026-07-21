# Produkční infrastruktura STRATEGIE (cloud APP/SQL, NSSM služby, HA Blue-Green)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Production setup** (od 30. 4. 2026 — Phase 25):
- Cloud APP `10.200.188.11` (Windows Server, NSSM services: STRATEGIE-API,
  STRATEGIE-CADDY, STRATEGIE-EMAIL-FETCHER, STRATEGIE-TASK-WORKER, STRATEGIE-QUESTION-GENERATOR)
- Cloud SQL `10.200.188.12` (Windows Server, PostgreSQL 16 + pgvector)
- Public domain `https://strategie-ai.com` s real Let's Encrypt certem
- PWA install (Add to Home Screen → standalone bez chrome) od 6. 5.
- **HA Blue-Green** (od 23. 5.): STRATEGIE-API (8002, current) + STRATEGIE-API-B
  (8003, day-old snapshot `C:\Projekty\STRATEGIE-prev\`), Caddy `lb_policy first`
  + user-controlled fallback (pin/unpin v patičce, cookie routing).

