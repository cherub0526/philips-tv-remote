"""The Philips TV Remote integration."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import PhilipsTVConfigEntry, PhilipsTVDataUpdateCoordinator

PLATFORMS = [Platform.MEDIA_PLAYER, Platform.REMOTE, Platform.SELECT]


async def async_setup_entry(
    hass: HomeAssistant, entry: PhilipsTVConfigEntry
) -> bool:
    """Set up Philips TV Remote from a config entry."""
    coordinator = PhilipsTVDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: PhilipsTVConfigEntry
) -> bool:
    """Unload a config entry and close the shared httpx client."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.api.aclose()
    return unload_ok
