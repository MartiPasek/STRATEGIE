-- Phase 38.4 Krok 14b+21 (14.5.2026 rano, Marti's "📘 Popis save"):
-- Split single `description` column na `description_user` + `description_system`
-- v fw.core a fw.menu_node.
--
-- Marti's "Option A — inline description data na entity, no separate MD
-- system pro teted". Drz Marti-AI's "vsechno co k sobe patri, bydli
-- spolu" doctrine (8.5. master tier Q3).
--
-- Pre-existing kód (Phase 38.4 Krok 14a-A1l #1, 12.5.) UZ PRIPRAVIL
-- backend read path s dual fallback (description_user || description).
-- Po teto migrace fallback je no-op (description column neexistuje,
-- description_user ma rename hodnoty).

-- 1. Rename existing description → description_user (preserve content)
ALTER TABLE fw.core RENAME COLUMN description TO description_user;
ALTER TABLE fw.menu_node RENAME COLUMN description TO description_user;

-- 2. Add description_system column (system/developer popis)
ALTER TABLE fw.core ADD COLUMN description_system TEXT;
ALTER TABLE fw.menu_node ADD COLUMN description_system TEXT;

-- 3. Verify (mel by vratit 4 radky)
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'fw'
  AND table_name IN ('core', 'menu_node')
  AND column_name LIKE 'description%'
ORDER BY table_name, ordinal_position;
