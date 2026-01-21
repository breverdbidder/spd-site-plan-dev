# Supabase MCP Configuration

## Overview
This directory contains Model Context Protocol (MCP) configuration for Supabase integration.

## Setup
1. Set `SUPABASE_MCP_TOKEN` in environment or GitHub Secrets
2. Run `npx -y @supabase/mcp-server` to start MCP server
3. Claude Code will automatically connect

## Security
- Token stored in GitHub Secrets (not committed)
- Scoped to read/write operations only
- Guardrails enforced via CLAUDE.md rules

## Documentation
- [Supabase MCP Server](https://github.com/supabase/mcp-server)
- [MCP Protocol](https://docs.anthropic.com/mcp)
