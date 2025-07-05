"""Baemin API for Baemin integration."""

from __future__ import annotations

import aiohttp
import base64
import hashlib
import os
import urllib.parse
from enum import StrEnum
from dataclasses import dataclass, field

from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.config_entries import ConfigEntry

from .const import LOGGER, KAKAO_CLIENT_ID, KAKAO_REDIRECT_URI


class LoginMethod(StrEnum):
    """Login method enum."""
    KAKAO = "kakao"
    NAVER = "naver"

@dataclass
class BaeminData:
    """Baemin data class."""
    bamin_address: dict = field(default_factory=dict)


class BaeminApi:
    """API for Baemin integration."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry = None) -> None:
        """Initialize the API."""
        self.hass = hass
        self.entry = entry
        self.code_verifier: str | None = None
        self.data = BaeminData()

    def get_kakao_auth_url(self) -> str:
        """Get Kakao OAuth authorization URL."""
        self.code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode().rstrip("=")
        self.code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(self.code_verifier.encode()).digest()
        ).decode().rstrip("=")

        auth_url = (
            "https://kauth.kakao.com/oauth/authorize?" +
            urllib.parse.urlencode({
                "response_type": "code",
                "client_id": KAKAO_CLIENT_ID,
                "redirect_uri": KAKAO_REDIRECT_URI,
                "code_challenge_method": "S256",
                "code_challenge": self.code_challenge,
                "deep_link_method": "universal_link",
            })
        )
        return auth_url

    async def get_kakao_oauth_token(self, auth_code: str) -> dict | None:
        """Get Kakao OAuth token."""
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Python-Requests",
        }

        data = {
            "grant_type": "authorization_code",
            "client_id": KAKAO_CLIENT_ID,
            "redirect_uri": KAKAO_REDIRECT_URI,
            "code": auth_code,
            "code_verifier": self.code_verifier,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post("https://kauth.kakao.com/oauth/token", headers=headers, data=data) as resp:
                if resp.status == 200:
                    token_data = await resp.json()
                    LOGGER.debug(f"Kakao OAuth Token: {token_data}")
                    return token_data
                else:
                    LOGGER.error(f"Kakao OAuth Error: {await resp.text()}")
                    return None

    async def get_kakao_user_info(self, access_token: str) -> dict | None:
        """Get Kakao user info."""
        headers = {
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Accept": "*/*",
            "User-Agent": "%EB%B0%B0%EB%8B%AC%EC%9D%98%EB%AF%BC%EC%A1%B1/15.6.1.53389 CFNetwork/3852.100.1 Darwin/25.0.0",
            "KA": "sdk/2.22.0 sdk_type/swift os/ios-19.0 lang/en-KR res/430x932 device/iPhone origin/com.jawebs.baedal app_ver/15.6.1",
            "Authorization": f"Bearer {access_token}",
            "Accept-Language": "en-US,en;q=0.9",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get("https://kapi.kakao.com/v2/user/me?secure_resource=true", headers=headers) as resp:
                if resp.status == 200:
                    user_info = await resp.json()
                    LOGGER.debug(f"Kakao User Info: {user_info}")
                    return user_info
                else:
                    LOGGER.error(f"Kakao User Info Error: {await resp.text()}")
                    return None

    async def get_baemin_oauth_token(self, post_data: dict) -> dict | None:
        """Get Baemin OAuth token."""
        headers = {
            "host": "auth.baemin.com",
            "content-type": "application/x-www-form-urlencoded; charset=utf-8",
            "user-agent": "iph1_15.6.1",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post("https://auth.baemin.com/oauth/token", headers=headers, data=post_data) as resp:
                if resp.status == 200:
                    token_data = await resp.json()
                    LOGGER.debug(f"Baemin OAuth Token: {token_data}")
                    return token_data
                else:
                    LOGGER.error(f"Baemin OAuth Error: {await resp.text()}")
                    return None

    async def login_to_baemin_mem2(self, access_token: str) -> dict | None:
        """Login to Baemin Mem2."""
        headers = {
            "content-type": "application/x-www-form-urlencoded; charset=utf-8",
            "accept": "*/*",
            "authorization": f"Bearer {access_token}",
            "user-agent": "iph1_15.6.1",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post("https://member.baemin.com/mem2/login", headers=headers) as resp:
                if resp.status == 200:
                    login_data = await resp.json()
                    LOGGER.debug(f"Baemin Mem2 Login: {login_data}")
                    return login_data
                else:
                    LOGGER.error(f"Baemin Mem2 Login Error: {await resp.text()}")
                    return None

    async def get_user_baemin_address(self) -> None:
        """Get Baemin Address."""
        headers = {
            "accept": "*/*",
            "authorization": f"Bearer {self.entry.data[CONF_ACCESS_TOKEN]}",
            "user-agent": "iph1_15.6.1",
        }

        params = {
            "dvcid": "-",
            "memberNo": "-",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get("https://location-api.baemin.com/v1/addresses", headers=headers, params=params) as resp:
                if resp.status == 200:
                    json_data = await resp.json()
                    LOGGER.debug(f"Baemin Address: {json_data}")
                    self.data.bamin_address = {
                        "favorite": json_data["data"]["favoriteAddresses"],
                        "normal": json_data["data"]["normalAddresses"],
                    }
                else:
                    LOGGER.error(f"Baemin Addresses Error: {await resp.text()}")
