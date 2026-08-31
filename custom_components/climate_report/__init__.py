"""Climate Report integration."""

from __future__ import annotations

import json

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState, Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later

from .const import DOMAIN, EVENT_REPORT_GENERATED, SIGNAL_UPDATE

PLATFORMS = ["sensor", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"summary": {}}

    async def receive_report(event: Event) -> None:
        hass.data[DOMAIN][entry.entry_id]["summary"] = dict(event.data)
        async_dispatcher_send(hass, SIGNAL_UPDATE, entry.entry_id)

    entry.async_on_unload(hass.bus.async_listen(EVENT_REPORT_GENERATED, receive_report))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    async def publish_summary(_now=None) -> None:
        await hass.services.async_call(
            "hassio",
            "addon_stdin",
            {
                "addon": entry.data["addon_slug"],
                "input": json.dumps({"command": "publish_summary"}),
            },
            blocking=False,
        )

    if hass.state is CoreState.running:
        await publish_summary()
    else:
        @callback
        def schedule_publish(_event: Event) -> None:
            entry.async_on_unload(async_call_later(hass, 10, publish_summary))

        entry.async_on_unload(
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, schedule_publish)
        )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
