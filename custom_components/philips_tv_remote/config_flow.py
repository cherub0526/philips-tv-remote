"""Config flow for the Philips TV Remote integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from haphilipsjs import PhilipsTV

try:
    from haphilipsjs import PairingFailure
except ImportError:  # Older library layouts may not export it.

    class PairingFailure(Exception):
        """Fallback used when the library does not export PairingFailure."""


from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import (
    CONF_HOST,
    CONF_MAC,
    CONF_PASSWORD,
    CONF_PIN,
    CONF_USERNAME,
)

from .const import (
    CONF_API_VERSION,
    CONF_SECURED_TRANSPORT,
    CONF_SYSTEM,
    DEFAULT_API_VERSION,
    DEFAULT_SECURED_TRANSPORT,
    DOMAIN,
    PAIR_APP_ID,
    PAIR_APP_NAME,
    PAIR_DEVICE_NAME,
    PAIR_DEVICE_OS,
)

_LOGGER = logging.getLogger(__name__)

PIN_SCHEMA = vol.Schema({vol.Required(CONF_PIN): str})


def _pairing_type(system: dict | None) -> str | None:
    try:
        return system["featuring"]["systemfeatures"].get("pairing_type")
    except (KeyError, TypeError):
        return None


class PhilipsTVConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow that pairs with the TV over digest auth."""

    VERSION = 1

    def __init__(self) -> None:
        self._api: PhilipsTV | None = None
        self._host: str | None = None
        self._mac: str | None = None
        self._system: dict | None = None
        self._pair_state: Any = None

    async def _close_api(self) -> None:
        if self._api is not None:
            await self._api.aclose()
            self._api = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            mac = user_input.get(CONF_MAC) or None
            api = PhilipsTV(
                host,
                api_version=DEFAULT_API_VERSION,
                secured_transport=DEFAULT_SECURED_TRANSPORT,
            )
            try:
                await api.getSystem()
            except Exception:  # noqa: BLE001 - any failure here means unreachable
                errors["base"] = "cannot_connect"
                await api.aclose()
            else:
                self._api = api
                self._host = host
                self._mac = mac
                self._system = api.system
                if _pairing_type(api.system) == "digest_auth_pairing":
                    try:
                        self._pair_state = await api.pairRequest(
                            PAIR_APP_ID,
                            PAIR_APP_NAME,
                            PAIR_DEVICE_NAME,
                            PAIR_DEVICE_OS,
                            "native",
                        )
                    except PairingFailure:
                        errors["base"] = "unknown"
                        await self._close_api()
                    except Exception:  # noqa: BLE001
                        errors["base"] = "cannot_connect"
                        await self._close_api()
                    else:
                        return await self.async_step_pair()
                else:
                    return await self._async_create_entry()

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_MAC): str,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    async def async_step_pair(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None and self._api is not None:
            try:
                username, password = await self._api.pairGrant(
                    self._pair_state, user_input[CONF_PIN]
                )
            except PairingFailure:
                errors["base"] = "invalid_pin"
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                return await self._async_create_entry(
                    username=username, password=password
                )

        return self.async_show_form(
            step_id="pair", data_schema=PIN_SCHEMA, errors=errors
        )

    async def _async_create_entry(
        self, username: str | None = None, password: str | None = None
    ) -> ConfigFlowResult:
        system = self._system or {}
        unique_id = system.get("serialnumber") or username or self._host
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()
        await self._close_api()
        return self.async_create_entry(
            title=system.get("name") or "Philips TV",
            data={
                CONF_HOST: self._host,
                CONF_API_VERSION: DEFAULT_API_VERSION,
                CONF_SECURED_TRANSPORT: DEFAULT_SECURED_TRANSPORT,
                CONF_USERNAME: username,
                CONF_PASSWORD: password,
                CONF_SYSTEM: system,
                CONF_MAC: self._mac,
            },
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        self._host = entry_data[CONF_HOST]
        self._mac = entry_data.get(CONF_MAC)
        self._system = entry_data.get(CONF_SYSTEM)
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is None:
            # Trigger pairing so the TV shows a fresh PIN, then ask for it.
            api = PhilipsTV(
                self._host,
                api_version=DEFAULT_API_VERSION,
                secured_transport=DEFAULT_SECURED_TRANSPORT,
            )
            try:
                await api.getSystem()
                self._pair_state = await api.pairRequest(
                    PAIR_APP_ID,
                    PAIR_APP_NAME,
                    PAIR_DEVICE_NAME,
                    PAIR_DEVICE_OS,
                    "native",
                )
            except Exception:  # noqa: BLE001
                await api.aclose()
                return self.async_abort(reason="cannot_connect")
            self._api = api
            self._system = api.system or self._system
            return self.async_show_form(
                step_id="reauth_confirm", data_schema=PIN_SCHEMA
            )

        if self._api is not None:
            try:
                username, password = await self._api.pairGrant(
                    self._pair_state, user_input[CONF_PIN]
                )
            except PairingFailure:
                errors["base"] = "invalid_pin"
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                await self._close_api()
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data_updates={
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm", data_schema=PIN_SCHEMA, errors=errors
        )
