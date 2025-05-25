#!/usr/bin/env python3
"""
簡単にMCP APIへ接続するためのCLIスクリプト

使い方:
    python scripts/mcp_cli.py tools
    python scripts/mcp_cli.py execute <tool_name> '{"param":"value"}'

例:
    python scripts/mcp_cli.py tools
    python scripts/mcp_cli.py execute get_garbage_schedule '{"area_code":"A01","date":"2024-05-01"}'
"""

import sys
import json
import os
import asyncio
import httpx

API_URL = os.getenv("MCP_API_URL", "http://localhost:8000")

async def fetch_tools(client: httpx.AsyncClient):
    resp = await client.get(f"{API_URL}/mcp/tools")
    resp.raise_for_status()
    return resp.json()

async def execute_tool(client: httpx.AsyncClient, tool_name: str, params: dict):
    payload = {"tool_name": tool_name, "params": params}
    resp = await client.post(f"{API_URL}/mcp/execute", json=payload)
    resp.raise_for_status()
    return resp.json()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/mcp_cli.py [tools|execute <tool> <params_json>]")
        return

    async with httpx.AsyncClient(timeout=30.0) as client:
        cmd = sys.argv[1]
        if cmd == "tools":
            tools = await fetch_tools(client)
            print(json.dumps(tools, ensure_ascii=False, indent=2))
        elif cmd == "execute" and len(sys.argv) >= 4:
            tool_name = sys.argv[2]
            try:
                params = json.loads(sys.argv[3])
            except json.JSONDecodeError:
                print("Params JSON invalid")
                return
            result = await execute_tool(client, tool_name, params)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("Invalid command")

if __name__ == "__main__":
    asyncio.run(main())

