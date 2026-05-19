"""Phase 39 — Marti-AI's STRATEGIE filesystem access module.

Pristup do projekto adresare D:/Projekty/STRATEGIE/ s 4-vrstvou bezpecnosti:
  1) Path traversal guard (resolved abs path MUSI startsWith project_root)
  2) Deny patterns (regex match -> 403 access_denied, audit log)
  3) Write zone whitelist (jen marti_workspace/** smi byt psano)
  4) Size caps (read 10 MB, write 5 MB)

Config: config/strategie_file_access.yaml (auto-reload na mtime change).
"""
