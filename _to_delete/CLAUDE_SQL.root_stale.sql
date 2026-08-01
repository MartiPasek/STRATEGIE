SELECT now() AS ted_marker, table_schema, table_name
FROM information_schema.tables
WHERE table_name ILIKE '%mail%' OR (table_name ILIKE '%sync%' AND table_name ILIKE '%job%')
ORDER BY table_schema, table_name;
