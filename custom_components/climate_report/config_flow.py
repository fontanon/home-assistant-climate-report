"""Config flow for Climate Report discovered through Supervisor."""

from __future__ import annotations

from typing import Any

from homeassistant import config_entries
from homeassistant.helpers.service_info.hassio import HassioServiceInfo

from .const import ADDON_SLUG, DOMAIN


class ClimateReportConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_hassio(self, discovery_info: HassioServiceInfo):
        await self.async_set_unique_id(discovery_info.uuid)
        self._abort_if_unique_id_configured()
        self._discovery_info = discovery_info
        self.context["title_placeholders"] = {"name": discovery_info.name}
        if self.context.get("confirm_only") is False:
            return self.async_create_entry(
                title=discovery_info.name,
                data={"addon_slug": discovery_info.slug},
            )
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(
                title="Climate Report",
                data={"addon_slug": self._discovery_info.slug},
            )
        return self.async_show_form(step_id="confirm")

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        await self.async_set_unique_id(ADDON_SLUG)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title="Climate Report",
            data={"addon_slug": ADDON_SLUG},
        )
