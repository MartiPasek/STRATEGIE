# Úklid public.documents — hotový skript pro ID23 (od Claude-27, 5. 7. 2026)

**Proč:** „černá díra" nezařazených dokumentů. Ověřeno v DB: NULL projekt = **1 294** dokumentů, z toho **571 duplicitních kopií** (stejný název+typ+velikost, hlavně opakované inline obrázky z mailů) + **10 `~$` Office temp/zámkových souborů** (0 KB, projekt 5 TISAX). Smazání uvolní **~149 MB** a zmenší NULL projekt na ~713.

**Proč ne já:** Marti-AI PG role nemá DELETE na `public.*` (doctrine 3-actor). Tohle je strategie-owner / ID23 path (jako lifespan DDL hook). Připraveno k jednomu spuštění.

## ⚠ Referenční pojistka (PROVĚŘIT PŘED DELETE)
Duplicitní `id` můžou být odkazované jinde — hlavně `email_inbox.meta->'attachment_doc_ids'` a `documents.storage_path` sdílení. Dedup drží **MIN(id)** z každé skupiny. Před spuštěním doporučuji ověřit, že mazané (vyšší) id nejsou odkazované, případně repointovat na ponechané MIN(id). RO soubory tím dotčené nejsou (mají vlastní kopie na share).

## Skript (pořadí kvůli FK: vectors → chunks → documents)
```sql
BEGIN;

CREATE TEMP TABLE _del_docs AS
-- 10x ~$ Office temp/zamkove soubory
SELECT id FROM public.documents WHERE COALESCE(original_filename,name) LIKE '%~$%'
UNION
-- 571x duplicity v NULL projektu (ponech nejnizsi id v kazde skupine)
SELECT id FROM (
  SELECT id, row_number() OVER (
    PARTITION BY COALESCE(NULLIF(original_filename,''),name), file_type, file_size_bytes
    ORDER BY id) AS rn
  FROM public.documents WHERE project_id IS NULL
) t WHERE rn > 1;

-- (volitelne) kontrola referenci v mailech pred smazanim:
-- SELECT id FROM _del_docs d WHERE EXISTS (
--   SELECT 1 FROM public.email_inbox e
--   WHERE e.meta::jsonb->'attachment_doc_ids' @> to_jsonb(d.id));

DELETE FROM public.document_vectors
 WHERE chunk_id IN (SELECT id FROM public.document_chunks WHERE document_id IN (SELECT id FROM _del_docs));
DELETE FROM public.document_chunks WHERE document_id IN (SELECT id FROM _del_docs);
DELETE FROM public.documents WHERE id IN (SELECT id FROM _del_docs);

-- COMMIT;  -- odkomentuj po overeni COUNTu (ocekavano ~581 documents)
ROLLBACK;   -- default: nejdriv suchy beh, zkontroluj counts
```

## Pozn.
- Fyzické soubory na disku (`storage_path`) skript nemaže — jen DB řádky. Případný úklid disku zvlášť.
- Po úklidu: NULL projekt ~713 → další ruční triáž na skutečné business (velká část zbytku = jednotlivé mailové obrázky/ISDOC).

— Claude-27 (CMS)
