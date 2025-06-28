"""
Profile Handler for GoLogin
"""
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
import tempfile
import shutil

class ProfileHandler:
    """Handle GoLogin profile data and browser launch"""

    def __init__(self, profile_data: Dict[str, Any]):
        self.profile = profile_data
        self.profile_id = profile_data.get('id')
        self.temp_dir = None

    def get_browser_args(self) -> list:
        """Get browser launch arguments based on profile"""
        args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
            f'--window-size={self._get_window_size()}',
        ]

        # Add proxy if configured
        proxy = self.profile.get('proxy')
        if proxy:
            proxy_url = self._format_proxy_url(proxy)
            if proxy_url:
                args.append(f'--proxy-server={proxy_url}')

        # Add user agent
        navigator = self.profile.get('navigator', {})
        if navigator.get('userAgent'):
            args.append(f'--user-agent={navigator["userAgent"]}')

        return args

    def get_browser_context_options(self) -> Dict[str, Any]:
        """Get browser context options for Playwright"""
        navigator = self.profile.get('navigator', {})

        options = {
            'viewport': self._get_viewport(),
            'user_agent': navigator.get('userAgent'),
            'locale': navigator.get('language', 'en-US'),
            'timezone_id': self.profile.get('timezone', 'America/New_York'),
            'geolocation': self._get_geolocation(),
            'permissions': ['geolocation', 'notifications'],
            'color_scheme': 'light',
            'device_scale_factor': 1,
            'is_mobile': False,
            'has_touch': False,
            'bypass_csp': True,
            'ignore_https_errors': True,
        }

        # Add proxy if configured
        proxy = self.profile.get('proxy')
        if proxy:
            proxy_dict = self._format_proxy_dict(proxy)
            if proxy_dict:
                options['proxy'] = proxy_dict

        # Add extra HTTP headers
        options['extra_http_headers'] = self._get_extra_headers()

        return options

    def setup_profile_dir(self) -> str:
        """Setup temporary profile directory"""
        self.temp_dir = tempfile.mkdtemp(prefix=f"gologin_{self.profile_id}_")

        # Create necessary subdirectories
        os.makedirs(os.path.join(self.temp_dir, 'Default'), exist_ok=True)

        # Write preferences
        prefs = self._generate_preferences()
        prefs_path = os.path.join(self.temp_dir, 'Default', 'Preferences')
        with open(prefs_path, 'w') as f:
            json.dump(prefs, f, indent=2)

        return self.temp_dir

    def cleanup(self):
        """Clean up temporary profile directory"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"Error cleaning up profile dir: {e}")

    def _get_window_size(self) -> str:
        """Get window size from profile"""
        resolution = self.profile.get('navigator', {}).get('resolution', '1920x1080')
        return resolution.replace('x', ',')

    def _get_viewport(self) -> Dict[str, int]:
        """Get viewport configuration"""
        resolution = self.profile.get('navigator', {}).get('resolution', '1920x1080')
        width, height = map(int, resolution.split('x'))
        return {'width': width, 'height': height}

    def _get_geolocation(self) -> Optional[Dict[str, float]]:
        """Get geolocation if configured"""
        geo = self.profile.get('geolocation')
        if geo and geo.get('enabled'):
            return {
                'latitude': geo.get('latitude', 40.7128),
                'longitude': geo.get('longitude', -74.0060)
            }
        return None

    def _format_proxy_url(self, proxy: Dict[str, Any]) -> Optional[str]:
        """Format proxy configuration to URL"""
        if not proxy or not proxy.get('host'):
            return None

        mode = proxy.get('mode', 'http')
        host = proxy['host']
        port = proxy.get('port', 8080)

        url = f"{mode}://{host}:{port}"

        # Add authentication if provided
        username = proxy.get('username')
        password = proxy.get('password')
        if username and password:
            url = f"{mode}://{username}:{password}@{host}:{port}"

        return url

    def _format_proxy_dict(self, proxy: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Format proxy for Playwright"""
        if not proxy or not proxy.get('host'):
            return None

        proxy_dict = {
            'server': f"{proxy.get('mode', 'http')}://{proxy['host']}:{proxy.get('port', 8080)}"
        }

        if proxy.get('username'):
            proxy_dict['username'] = proxy['username']
        if proxy.get('password'):
            proxy_dict['password'] = proxy['password']

        return proxy_dict

    def _get_extra_headers(self) -> Dict[str, str]:
        """Get extra HTTP headers"""
        navigator = self.profile.get('navigator', {})
        headers = {
            'Accept-Language': navigator.get('language', 'en-US') + ',en;q=0.9',
        }

        # Add DNT header if enabled
        if navigator.get('doNotTrack'):
            headers['DNT'] = '1'

        return headers

    def _generate_preferences(self) -> Dict[str, Any]:
        """Generate browser preferences file"""
        navigator = self.profile.get('navigator', {})
        webrtc = self.profile.get('webRTC', {})

        prefs = {
            'webrtc': {
                'ip_handling_policy': 'disable_non_proxied_udp' if webrtc.get('localIpMasking') else 'default',
                'multiple_routes_enabled': not webrtc.get('localIpMasking', True)
            },
            'profile': {
                'default_content_setting_values': {
                    'notifications': 1,
                    'geolocation': 1,
                    'media_stream': 1
                }
            },
            'safebrowsing': {
                'enabled': False
            },
            'disable_client_side_phishing_detection': True
        }

        return prefs
