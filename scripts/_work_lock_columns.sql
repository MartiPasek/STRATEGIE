-- ============================================================================
-- Work-lock + freshness sloupce na fw.claude_instance (Marti 3.6.2026)
-- ============================================================================
-- SPUSTIT V DBEAVERU (připojení Marti-AI nebo postgres) — NE přes bridge.
-- Důvod: bridge dělá presence-upsert na claude_instance při každém volání/pollu,
-- takže ALTER (ACCESS EXCLUSIVE) přes bridge prohrává s vlastní churnou. V DBeaveru
-- konkuruje jen 30s heartbeat → lock_timeout=15s pohodlně chytí mezeru.
--
-- Kdyby přesto hlásil "canceling statement due to lock timeout" → prostě spusť
-- znovu (v DBeaveru je to okamžité, chytí to další mezeru).
-- ============================================================================

SET lock_timeout = '15s';

ALTER TABLE fw.claude_instance
  ADD COLUMN IF NOT EXISTS current_work       TEXT,
  ADD COLUMN IF NOT EXISTS current_work_files TEXT,
  ADD COLUMN IF NOT EXISTS current_work_at    TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS work_status        VARCHAR(20) DEFAULT 'idle',
  ADD COLUMN IF NOT EXISTS local_head_sha     VARCHAR(40),
  ADD COLUMN IF NOT EXISTS local_behind       INT DEFAULT 0;

-- Ověření:
-- SELECT column_name FROM information_schema.columns
-- WHERE table_schema='fw' AND table_name='claude_instance'
--   AND column_name IN ('current_work','work_status','local_behind');
