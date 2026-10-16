"""Remote entity that forwards key presses to a Philips TV."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from homeassistant.components.remote import RemoteEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import PhilipsTVConfigEntry, PhilipsTVDataUpdateCoordinator
from .entity import PhilipsTVEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PhilipsTVConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([PhilipsTVRemote(entry.runtime_data)])


class PhilipsTVRemote(PhilipsTVEntity, RemoteEntity):
    """Send remote-control keys to the TV."""

    _attr_name = "Remote"

    def __init__(self, coordinator: PhilipsTVDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.unique_id}_remote"

    @property
    def is_on(self) -> bool:
        return self.coordinator.api.powerstate == "On"

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.turn_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.turn_off()

    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        for key in command:
            await self.coordinator.api.sendKey(key)
        await self.coordinator.async_request_refresh()
