"""Coordinator that owns the PhilipsTV client and polls the TV."""

from __future__ import annotations

import logging

from haphilipsjs import AutenticationFailure, PhilipsTV
from wakeonlan import send_magic_packet

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_API_VERSION,
    CONF_SECURED_TRANSPORT,
    CONF_SYSTEM,
    DEFAULT_API_VERSION,
    DEFAULT_SECURED_TRANSPORT,
    DOMAIN,
    SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

type PhilipsTVConfigEntry = ConfigEntry[PhilipsTVDataUpdateCoordinator]


class PhilipsTVDataUpdateCoordinator(DataUpdateCoordinator[None]):
    """Hold the single PhilipsTV client and refresh its state on a schedule."""

    config_entry: PhilipsTVConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: PhilipsTVConfigEntry
    ) -> None:
        """Build the client from the config entry data."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        data = entry.data
        self.api = PhilipsTV(
            data[CONF_HOST],
            api_version=data.get(CONF_API_VERSION, DEFAULT_API_VERSION),
            secured_transport=data.get(
                CONF_SECURED_TRANSPORT, DEFAULT_SECURED_TRANSPORT
            ),
            username=data.get(CONF_USERNAME),
            password=data.get(CONF_PASSWORD),
        )
        # Seed system info so DeviceInfo has model and serial before the first poll.
        self.api.system = data.get(CONF_SYSTEM)
        self.mac: str | None = data.get(CONF_MAC)
        self.unique_id = entry.unique_id

    @property
    def system(self) -> dict | None:
        """Return the TV system block (name, model, serialnumber)."""
        return self.api.system

    async def _async_update_data(self) -> None:
        host = self.config_entry.data[CONF_HOST]
        try:
            # update() swallows connection errors and reports them via tv.on,
            # so a raised AutenticationFailure means the stored pairing was rejected.
            await self.api.update()
        except AutenticationFailure as error:
            raise ConfigEntryAuthFailed(str(error)) from error
        except Exception as error:
            raise UpdateFailed(f"Error talking to {host}: {error}") from error

    async def turn_on(self) -> None:
        """Wake the TV over the network if possible, then request power on."""
        if self.mac:
            send_magic_packet(self.mac)
        await self.api.setPowerState("On")
        await self.async_request_refresh()

    async def turn_off(self) -> None:
        await self.api.setPowerState("Standby")
        await self.async_request_refresh()
