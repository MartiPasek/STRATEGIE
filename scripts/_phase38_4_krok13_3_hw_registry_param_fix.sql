-- Phase 38.4 Krok 13.3 hotfix (14.5.2026 rano, Marti's IT prezentace prep):
-- hw_registry endpoint_url ?type= -> ?mode= mismatch fix
--
-- Marti's catch: "v nekterych hardcoded prehledech postupne vyparilo
-- renderovani dulezitych dat urcitych sloupcu". Diagnostika odhalila
-- query parameter mismatch:
--   hw_registry.endpoint_url  → ?type=X
--   /system/security handler  → expects ?mode=X (FastAPI signature)
-- FastAPI tise ignoruje unknown query params + pouzije default
-- mode="users" → vsechny non-users gridy dostavaly users data.
--
-- Plus FastAPI 422 NE-trigger (Pydantic kept "type=" as orphan,
-- "mode=" defaultoval). Visible jen v wrong data shape downstream.

UPDATE fw.hw_registry
SET endpoint_url = REPLACE(endpoint_url, '?type=', '?mode=')
WHERE code IN (
    'security_devices',
    'security_users',
    'security_whitelists',
    'security_invites',
    'security_audit'
)
  AND endpoint_url LIKE '%?type=%';

-- Verify (mel by ukazat 5 radku, vsechny s ?mode=):
SELECT id, code, endpoint_url
FROM fw.hw_registry
WHERE code LIKE 'security_%'
ORDER BY code;
