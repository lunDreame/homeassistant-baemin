"""Config flow for Baemin."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_URL
import homeassistant.helpers.config_validation as cv

from .const import _LOGGER, DOMAIN, CONF_LOGIN_METHOD, CONF_AUTH_CODE
from .baemin_api import LoginMethod, BaeminApi

class BaeminFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Baemin."""

    VERSION = 1

    def __init__(self):
        """Initialize the flow."""
        self.api = BaeminApi(self.hass, entry=None)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            login_method = user_input[CONF_LOGIN_METHOD]
            if login_method == LoginMethod.KAKAO:
                return await self.async_step_kakao_login()
            elif login_method == LoginMethod.NAVER:
                return await self.async_step_naver_login()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_LOGIN_METHOD): vol.In([LoginMethod.KAKAO]),
            }),
        )

    async def async_step_kakao_login(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Kakao login info"""
        errors = {}
        processing_error = False

        if user_input is not None:
            token_data = await self.api.get_kakao_oauth_token(user_input[CONF_AUTH_CODE])
            if token_data is None:
                processing_error = True
                errors["base"] = "failed_token_issuance"

            if not processing_error:
                user_info = await self.api.get_kakao_user_info(token_data.get("access_token", ""))
                if user_info is None:
                    processing_error = True
                    errors["base"] = "failed_user_info_retrieval"

            if not processing_error:
                post_data = {
                    "auth_type": "KAKAO",
                    "grant_type": "sns_key",
                    "scope": "read",
                    "security_key": token_data.get("access_token", ""),
                    "sns_key": user_info.get("id", ""),
                }

                token_data = await self.api.get_baemin_oauth_token(post_data)
                if token_data is None:
                    processing_error = True
                    errors["base"] = "failed_token_issuance"

            if not processing_error:
                await self.async_set_unique_id("")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="", data=token_data)

        return self.async_show_form(
            step_id="kakao_login",
            data_schema=vol.Schema({
                vol.Required(CONF_AUTH_CODE): cv.string,
            }),
            errors=errors,
            description_placeholders={
                CONF_URL: self.api.get_kakao_auth_url(),
            }
        )

    async def async_step_naver_login(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Naver login info"""
