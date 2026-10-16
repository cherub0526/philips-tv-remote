"""Constants for the Philips TV Remote integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "philips_tv_remote"

DEFAULT_API_VERSION = 6
DEFAULT_SECURED_TRANSPORT = True

CONF_API_VERSION = "api_version"
CONF_SECURED_TRANSPORT = "secured_transport"
CONF_SYSTEM = "system"

PAIR_APP_ID = "ha-philipsjs"
PAIR_APP_NAME = "ha-philipsjs"
PAIR_DEVICE_NAME = "Home Assistant"
PAIR_DEVICE_OS = "Linux"

SCAN_INTERVAL = timedelta(seconds=15)
