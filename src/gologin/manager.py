"""
GoLogin Profile Manager
"""
import aiohttp
import asyncio
import json
import os
import random
from typing import Dict, Any, Optional, List
from pathlib import Path

class GoLoginManager:
    """Manager for GoLogin browser profiles"""

    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://api.gologin.com/browser"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        self.profiles_cache = {}

    async def get_or_create_profile(self, profile_id: Optional[str] = None) -> Dict[str, Any]:
        """Get existing profile or create new one"""
        if profile_id and profile_id in self.profiles_cache:
            return self.profiles_cache[profile_id]

        if profile_id:
            # Try to get existing profile
            profile = await self.get_profile(profile_id)
            if profile:
                return profile

        # Create new profile with random settings
        return await self.create_random_profile()

    async def get_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Get profile by ID"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/{profile_id}",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        profile = await response.json()
                        self.profiles_cache[profile_id] = profile
                        return profile
        except Exception as e:
            print(f"Error getting profile: {e}")
        return None

    async def create_random_profile(self) -> Dict[str, Any]:
        """Create new profile with random fingerprint"""
        profile_data = {
            "name": f"AutoProfile_{random.randint(1000, 9999)}",
            "os": random.choice(["win", "mac", "lin"]),
            "navigator": {
                "userAgent": self._get_random_user_agent(),
                "resolution": random.choice(["1920x1080", "1366x768", "1440x900"]),
                "language": random.choice(["en-US", "en-GB", "en"]),
                "platform": random.choice(["Win32", "MacIntel", "Linux x86_64"]),
                "doNotTrack": random.choice([True, False]),
                "hardwareConcurrency": random.choice([4, 8, 16])
            },
            "storage": {
                "local": True,
                "extensions": True,
                "bookmarks": True,
                "history": True,
                "passwords": True
            },
            "proxyEnabled": True,
            "proxy": self._get_proxy_config(),
            "webRTC": {
                "mode": "alerted",
                "enabled": True,
                "customize": True,
                "localIpMasking": True
            },
            "canvas": {
                "mode": "noise"
            },
            "webGL": {
                "mode": "noise"
            },
            "webGLMetadata": {
                "mode": "mask",
                "vendor": random.choice(["Intel Inc.", "NVIDIA Corporation", "AMD"]),
                "renderer": self._get_random_gpu()
            },
            "audioContext": {
                "mode": "noise"
            },
            "fonts": {
                "families": self._get_random_fonts()
            },
            "mediaDevices": {
                "videoInputs": random.randint(0, 2),
                "audioInputs": random.randint(1, 3),
                "audioOutputs": random.randint(1, 2)
            },
            "screenResolution": random.choice(["1920x1080", "1366x768", "1440x900", "1280x720"])
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    headers=self.headers,
                    json=profile_data
                ) as response:
                    if response.status == 201:
                        profile = await response.json()
                        self.profiles_cache[profile['id']] = profile
                        return profile
                    else:
                        raise Exception(f"Failed to create profile: {await response.text()}")
        except Exception as e:
            print(f"Error creating profile: {e}")
            # Return mock profile for development
            return {
                "id": f"mock_{random.randint(1000, 9999)}",
                "name": profile_data["name"],
                "proxy": profile_data.get("proxy"),
                "navigator": profile_data["navigator"]
            }

    async def update_profile(self, profile_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing profile"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"{self.base_url}/{profile_id}",
                    headers=self.headers,
                    json=updates
                ) as response:
                    if response.status == 200:
                        profile = await response.json()
                        self.profiles_cache[profile_id] = profile
                        return profile
        except Exception as e:
            print(f"Error updating profile: {e}")
        return self.profiles_cache.get(profile_id, {})

    async def cleanup_profile(self, profile_id: str):
        """Clean up profile data after use"""
        # Clear cookies and storage
        updates = {
            "storage": {
                "cookies": [],
                "localStorage": {},
                "sessionStorage": {}
            }
        }
        await self.update_profile(profile_id, updates)

        # Remove from cache
        if profile_id in self.profiles_cache:
            del self.profiles_cache[profile_id]

    def _get_random_user_agent(self) -> str:
        """Get random realistic user agent"""
        user_agents = [
            # Chrome on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            # Chrome on Mac
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            # Firefox
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            # Edge
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        ]
        return random.choice(user_agents)

    def _get_proxy_config(self) -> Optional[Dict[str, Any]]:
        """Get proxy configuration"""
        # In production, this would return actual proxy configs
        # For now, return None to use direct connection
        return None

        # Example proxy config:
        # return {
        #     "mode": "http",
        #     "host": "proxy.example.com",
        #     "port": 8080,
        #     "username": "user",
        #     "password": "pass"
        # }

    def _get_random_gpu(self) -> str:
        """Get random GPU renderer string"""
        gpus = [
            "ANGLE (Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)",
            "ANGLE (NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0)",
            "ANGLE (AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0)",
            "ANGLE (Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0)"
        ]
        return random.choice(gpus)

    def _get_random_fonts(self) -> List[str]:
        """Get random font list"""
        all_fonts = [
            "Arial", "Verdana", "Helvetica", "Times New Roman", "Georgia",
            "Courier New", "Trebuchet MS", "Comic Sans MS", "Impact",
            "Lucida Console", "Tahoma", "Geneva", "Century Gothic"
        ]
        # Return random subset
        num_fonts = random.randint(8, len(all_fonts))
        return random.sample(all_fonts, num_fonts)
