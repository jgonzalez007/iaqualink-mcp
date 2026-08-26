# iaqualink-mcp

[![CI](https://github.com/jgonzalez007/iaqualink-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/jgonzalez007/iaqualink-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An MCP server that exposes a Jandy iAqualink pool/spa system to Claude
(or any MCP client). It wraps the [`iaqualink`](https://github.com/flz/iaqualink-py)
Python library.

Tools provided:

- `list_systems` — all systems on the account
- `list_devices` — all devices on a system
- `get_device` — state of one device
- `get_system_status` — system + every device's state in one call
- `turn_on` / `turn_off` / `toggle_device`
- `set_temperature` — thermostat set points
- `set_light_effect` / `set_light_rgbw` / `set_light_brightness` — ICL/IntelliCenter lights

Set `IAQUALINK_READ_ONLY=true` to disable every write tool and only allow reads.

## Install

### From GitHub (once pushed)

```bash
uv tool install git+https://github.com/jgonzalez007/iaqualink-mcp
```

### From a local clone (recommended for development, and avoids `uvx`
having to clone/build the project on every launch)

```bash
git clone https://github.com/jgonzalez007/iaqualink-mcp
cd iaqualink-mcp
uv tool install .
```

Either way this registers a command called `iaqualink-mcp` that `uvx`/`uv tool`
can run directly.

## Configure Claude Desktop

Edit `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or
`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
and add:

```json
{
  "mcpServers": {
    "iaqualink": {
      "command": "uvx",
      "args": ["iaqualink-mcp"],
      "env": {
        "IAQUALINK_USERNAME": "you@example.com",
        "IAQUALINK_PASSWORD": "your-iaqualink-password"
      }
    }
  }
}
```

Add `"IAQUALINK_READ_ONLY": "true"` to `env` if you only want Claude to read
status, never control equipment.

Then fully quit Claude Desktop from the system tray (not just close the
window) and relaunch it.

## Development

```bash
git clone https://github.com/jgonzalez007/iaqualink-mcp
cd iaqualink-mcp
uv sync --extra dev

# Run tests
uv run pytest

# Lint
uvx ruff check .
```

Copy `.env.example` to `.env` and fill in your credentials for local manual
testing; `.env` is gitignored.

## Contributing

Issues and pull requests are welcome. Please run `pytest` and `ruff check .`
before opening a PR.

## Notes

- This uses a reverse-engineered/unofficial API (via `iaqualink-py`); Jandy/
  Zodiac/Fluidra don't publish an official one. Use at your own risk.
- Credentials are read from environment variables only — nothing is written
  to disk by this server.
- Your `claude_desktop_config.json` will contain your iAqualink password in
  plaintext. Don't commit that file or share it, and treat it like any other
  credential store on your machine.

## License

MIT — see [LICENSE](LICENSE).
