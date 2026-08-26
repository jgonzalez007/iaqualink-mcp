"""
MCP server that exposes Jandy iAqualink pool/spa control as tools.

Wraps the async `iaqualink` library (https://github.com/flz/iaqualink-py).

Credentials are read from environment variables:
    IAQUALINK_USERNAME
    IAQUALINK_PASSWORD

Optional:
    IAQUALINK_READ_ONLY=true   -> disables every tool that changes device state
"""

from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from iaqualink.client import AqualinkClient

mcp = FastMCP(
    "iAqualink",
    instructions=(
        "Tools for monitoring and controlling a Jandy iAqualink pool/spa system: "
        "list systems, list devices, read device state, and turn things on/off, "
        "toggle switches, adjust thermostats, and control ICL/IntelliCenter lights. "
        "System serials come from list_systems; device keys come from list_devices. "
        "When the server is in read-only mode, write tools return an error instead "
        "of acting."
    ),
)


def _read_only() -> bool:
    return os.environ.get("IAQUALINK_READ_ONLY", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _creds() -> tuple[str, str]:
    username = os.environ.get("IAQUALINK_USERNAME")
    password = os.environ.get("IAQUALINK_PASSWORD")
    if not username or not password:
        raise RuntimeError(
            "IAQUALINK_USERNAME and IAQUALINK_PASSWORD environment variables "
            "must both be set."
        )
    return username, password


def _device_summary(key: str, device: Any) -> dict[str, Any]:
    return {
        "key": key,
        "label": getattr(device, "label", key),
        "state": getattr(device, "state", None),
        "is_on": getattr(device, "is_on", None),
        "name": getattr(device, "name", None),
    }


def _system_summary(serial: str, system: Any) -> dict[str, Any]:
    return {
        "serial": serial,
        "name": getattr(system, "name", None),
        "device_type": system.data.get("device_type") if getattr(system, "data", None) else None,
        "online": getattr(system, "online", None),
    }


async def _get_system(client: AqualinkClient, system_serial: str):
    systems = await client.get_systems()
    system = systems.get(system_serial)
    if system is None:
        available = ", ".join(systems.keys()) or "(none found on this account)"
        raise ValueError(
            f"No system with serial '{system_serial}'. Available serials: {available}"
        )
    return system


async def _get_device(client: AqualinkClient, system_serial: str, device_key: str):
    system = await _get_system(client, system_serial)
    devices = await system.get_devices()
    device = devices.get(device_key)
    if device is None:
        available = ", ".join(devices.keys()) or "(none found on this system)"
        raise ValueError(
            f"No device with key '{device_key}' on system '{system_serial}'. "
            f"Available keys: {available}"
        )
    return device


def _require_write_access() -> None:
    if _read_only():
        raise RuntimeError(
            "This server is running in read-only mode "
            "(IAQUALINK_READ_ONLY is set); write actions are disabled."
        )


# --------------------------------------------------------------------------
# Read tools
# --------------------------------------------------------------------------


@mcp.tool()
async def list_systems() -> dict[str, Any]:
    """List every pool/spa system on the iAqualink account, keyed by serial."""
    username, password = _creds()
    async with AqualinkClient(username, password) as client:
        systems = await client.get_systems()
        return {serial: _system_summary(serial, sys) for serial, sys in systems.items()}


@mcp.tool()
async def list_devices(system_serial: str) -> dict[str, Any]:
    """List every device on one system (pumps, heaters, lights, sensors, aux switches).

    Args:
        system_serial: A system serial from list_systems.
    """
    username, password = _creds()
    async with AqualinkClient(username, password) as client:
        system = await _get_system(client, system_serial)
        devices = await system.get_devices()
        return {key: _device_summary(key, dev) for key, dev in devices.items()}


@mcp.tool()
async def get_device(system_serial: str, device_key: str) -> dict[str, Any]:
    """Get the current state of a single device.

    Args:
        system_serial: A system serial from list_systems.
        device_key: A device key from list_devices.
    """
    username, password = _creds()
    async with AqualinkClient(username, password) as client:
        device = await _get_device(client, system_serial, device_key)
        return _device_summary(device_key, device)


@mcp.tool()
async def get_system_status(system_serial: str) -> dict[str, Any]:
    """Get a full tree view: system info plus the state of every device on it.

    Args:
        system_serial: A system serial from list_systems.
    """
    username, password = _creds()
    async with AqualinkClient(username, password) as client:
        system = await _get_system(client, system_serial)
        await system.update()
        devices = await system.get_devices()
        return {
            "system": _system_summary(system_serial, system),
            "devices": {key: _device_summary(key, dev) for key, dev in devices.items()},
        }


# --------------------------------------------------------------------------
# Write tools
# --------------------------------------------------------------------------


@mcp.tool()
async def turn_on(system_serial: str, device_key: str) -> dict[str, Any]:
    """Turn a device on (pump, heater, light, aux switch, etc).

    Args:
        system_serial: A system serial from list_systems.
        device_key: A device key from list_devices.
    """
    _require_write_access()
    username, password = _creds()
    async with AqualinkClient(username, password) as client:
        device = await _get_device(client, system_serial, device_key)
        await device.turn_on()
        return _device_summary(device_key, device)


@mcp.tool()
async def turn_off(system_serial: str, device_key: str) -> dict[str, Any]:
    """Turn a device off (pump, heater, light, aux switch, etc).

    Args:
        system_serial: A system serial from list_systems.
        device_key: A device key from list_devices.
    """
    _require_write_access()
    username, password = _creds()
    async with AqualinkClient(username, password) as client:
        device = await _get_device(client, system_serial, device_key)
        await device.turn_off()
        return _device_summary(device_key, device)


@mcp.tool()
async def toggle_device(system_serial: str, device_key: str) -> dict[str, Any]:
    """Toggle a device between on and off.

    Args:
        system_serial: A system serial from list_systems.
        device_key: A device key from list_devices.
    """
    _require_write_access()
    username, password = _creds()
    async with AqualinkClient(username, password) as client:
        device = await _get_device(client, system_serial, device_key)
        await device.toggle()
        return _device_summary(device_key, device)


@mcp.tool()
async def set_temperature(system_serial: str, device_key: str, temperature: float) -> dict[str, Any]:
    """Set a thermostat's target temperature (pool_set_point / spa_set_point, etc).

    Args:
        system_serial: A system serial from list_systems.
        device_key: A thermostat device key from list_devices.
        temperature: Target temperature in the unit the system is configured for.
    """
    _require_write_access()
    username, password = _creds()
    async with AqualinkClient(username, password) as client:
        device = await _get_device(client, system_serial, device_key)
        await device.set_temperature(temperature)
        return _device_summary(device_key, device)


@mcp.tool()
async def set_light_effect(system_serial: str, device_key: str, effect: str) -> dict[str, Any]:
    """Set an ICL/IntelliCenter light to a named preset color/effect (e.g. 'Emerald Green').

    Args:
        system_serial: A system serial from list_systems.
        device_key: An ICL light device key from list_devices.
        effect: The preset effect/color name.
    """
    _require_write_access()
    username, password = _creds()
    async with AqualinkClient(username, password) as client:
        device = await _get_device(client, system_serial, device_key)
        await device.set_effect(effect)
        return _device_summary(device_key, device)


@mcp.tool()
async def set_light_rgbw(
    system_serial: str,
    device_key: str,
    red: int,
    green: int,
    blue: int,
    white: int = 0,
) -> dict[str, Any]:
    """Set a custom RGBW color (0-255 each channel) on an ICL/IntelliCenter light.

    Args:
        system_serial: A system serial from list_systems.
        device_key: An ICL light device key from list_devices.
        red: Red channel, 0-255.
        green: Green channel, 0-255.
        blue: Blue channel, 0-255.
        white: White channel, 0-255. Defaults to 0.
    """
    _require_write_access()
    username, password = _creds()
    async with AqualinkClient(username, password) as client:
        device = await _get_device(client, system_serial, device_key)
        await device.set_rgbw(red, green, blue, white=white)
        return _device_summary(device_key, device)


@mcp.tool()
async def set_light_brightness(system_serial: str, device_key: str, percentage: int) -> dict[str, Any]:
    """Set brightness (0-100) on an ICL/IntelliCenter light.

    Args:
        system_serial: A system serial from list_systems.
        device_key: An ICL light device key from list_devices.
        percentage: Brightness from 0 to 100.
    """
    _require_write_access()
    username, password = _creds()
    async with AqualinkClient(username, password) as client:
        device = await _get_device(client, system_serial, device_key)
        await device.set_brightness_percentage(percentage)
        return _device_summary(device_key, device)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
