"""
Phase 28-A (2.5.2026): EUROSOFT MCP server.

Standalone Python service co bezi na EC-SERVER2 (192.168.30.11),
naslouchá na localhost:8765, exponuje MCP HTTP/SSE pres Caddy
reverse-proxy na api.eurosoft.com/marti-mcp/.

Sluzi jako most mezi Marti-AI (STRATEGIE composer) a EUROSOFT
SQL Server (DB_EC). 6 tools (query/get/insert/count/bulk/describe),
11-table whitelist, Bearer auth, audit log, rate limit.

Deploy: viz scripts/install_eurosoft_mcp_on_ec_server2.ps1
"""
__version__ = "0.1.0"
