# Platforma Tech Stack

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**STRATEGIE tech stack: FastAPI + statické HTML/JS + AG Grid (NE Django, NE React/Vue) | platforma architektura framework backend frontend**

Platforma STRATEGIE běží na FastAPI (Python, uvicorn, NSSM služba STRATEGIE-API) + statické HTML/JS v apps/api/static + knihovna AG Grid pro přehledy. NENÍ to Django ani React/Vue — pokud to někde stojí, je to chyba. PostgreSQL data_db (primární paměť) + MSSQL DB_EC (legacy Centrála 1, read) + cloud Helios mssql188.

