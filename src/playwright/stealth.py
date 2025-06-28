"""
Stealth Plugin for Playwright - Anti-bot detection
"""
from playwright.async_api import Page, BrowserContext
import json

class StealthPlugin:
    """Plugin to evade bot detection"""

    def __init__(self):
        self.evasions = [
            self._chrome_runtime,
            self._console_debug,
            self._iframe_contentWindow,
            self._media_codecs,
            self._navigator_languages,
            self._navigator_permissions,
            self._navigator_plugins,
            self._navigator_vendor,
            self._navigator_webdriver,
            self._user_agent_override,
            self._webgl_vendor,
            self._window_outerdimensions,
            self._chrome_app,
            self._chrome_csi,
            self._chrome_load_times,
            self._chrome_runtime
        ]

    async def apply_to_context(self, context: BrowserContext):
        """Apply stealth to browser context"""
        # Add init script to all pages
        await context.add_init_script(self._get_stealth_script())

    async def apply_to_page(self, page: Page):
        """Apply stealth to specific page"""
        # Evaluate stealth scripts
        await page.evaluate(self._get_stealth_script())

        # Override permissions
        await self._override_permissions(page)

    def _get_stealth_script(self) -> str:
        """Get combined stealth JavaScript"""
        scripts = []

        # WebDriver detection evasion
        scripts.append("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Remove chrome.runtime if not available
            if (!window.chrome) {
                window.chrome = {};
            }
            if (!window.chrome.runtime) {
                window.chrome.runtime = {};
            }
        """)

        # Chrome app evasion
        scripts.append("""
            // Chrome app properties
            if (window.chrome) {
                window.chrome.app = {
                    isInstalled: false,
                    InstallState: {
                        DISABLED: 'disabled',
                        INSTALLED: 'installed',
                        NOT_INSTALLED: 'not_installed'
                    },
                    RunningState: {
                        CANNOT_RUN: 'cannot_run',
                        READY_TO_RUN: 'ready_to_run',
                        RUNNING: 'running'
                    }
                };
            }
        """)

        # Navigator properties
        scripts.append("""
            // Override navigator properties
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });

            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const plugins = [
                        {
                            name: 'Chrome PDF Plugin',
                            description: 'Portable Document Format',
                            filename: 'internal-pdf-viewer',
                            length: 1
                        },
                        {
                            name: 'Chrome PDF Viewer',
                            description: '',
                            filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                            length: 1
                        },
                        {
                            name: 'Native Client',
                            description: '',
                            filename: 'internal-nacl-plugin',
                            length: 2
                        }
                    ];
                    return Object.create(PluginArray.prototype, {
                        length: { value: plugins.length },
                        ...plugins.reduce((acc, plugin, i) => {
                            acc[i] = { value: plugin };
                            return acc;
                        }, {})
                    });
                }
            });
        """)

        # Permission API override
        scripts.append("""
            // Override Permissions API
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => {
                if (parameters.name === 'notifications') {
                    return Promise.resolve({ state: Notification.permission });
                }
                return originalQuery(parameters);
            };
        """)

        # WebGL Vendor override
        scripts.append("""
            // Override WebGL vendor
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.apply(this, arguments);
            };

            const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter2.apply(this, arguments);
            };
        """)

        # Console.debug fix
        scripts.append("""
            // Fix console.debug
            window.console.debug = () => {};
        """)

        # Media codecs support
        scripts.append("""
            // Override media codecs
            Object.defineProperty(HTMLVideoElement.prototype, 'canPlayType', {
                value: function(type) {
                    if (type === 'video/mp4; codecs="avc1.42E01E"') return 'probably';
                    if (type === 'video/webm; codecs="vp8, vorbis"') return 'probably';
                    if (type === 'video/ogg; codecs="theora"') return 'maybe';
                    return '';
                }
            });
        """)

        # Battery API
        scripts.append("""
            // Mock Battery API
            if ('getBattery' in navigator) {
                window.navigator.getBattery = async () => ({
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 1
                });
            }
        """)

        return '\n'.join(scripts)

    async def _override_permissions(self, page: Page):
        """Override browser permissions"""
        # Grant common permissions
        await page.context.grant_permissions([
            'geolocation',
            'notifications',
            'camera',
            'microphone'
        ])

    def _chrome_runtime(self):
        return """
            window.chrome.runtime.sendMessage = () => {};
            window.chrome.runtime.connect = () => ({
                onMessage: { addListener: () => {} },
                onDisconnect: { addListener: () => {} },
                postMessage: () => {}
            });
        """

    def _console_debug(self):
        return "window.console.debug = () => {};"

    def _iframe_contentWindow(self):
        return """
            // Ensure iframe.contentWindow === window.frames[i]
            Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
                get: function() {
                    return window.frames[Array.from(document.querySelectorAll('iframe')).indexOf(this)];
                }
            });
        """

    def _media_codecs(self):
        return """
            // Ensure media codecs are available
            Object.defineProperty(HTMLMediaElement.prototype, 'canPlayType', {
                value: function(type) {
                    if (type.includes('mp4')) return 'probably';
                    if (type.includes('webm')) return 'probably';
                    if (type.includes('ogg')) return 'maybe';
                    return '';
                }
            });
        """

    def _navigator_languages(self):
        return """
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """

    def _navigator_permissions(self):
        return """
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => {
                if (parameters.name === 'notifications') {
                    return Promise.resolve({ state: Notification.permission });
                }
                return originalQuery(parameters);
            };
        """

    def _navigator_plugins(self):
        return """
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    return [
                        { name: 'Chrome PDF Plugin' },
                        { name: 'Chrome PDF Viewer' },
                        { name: 'Native Client' }
                    ];
                }
            });
        """

    def _navigator_vendor(self):
        return """
            Object.defineProperty(navigator, 'vendor', {
                get: () => 'Google Inc.'
            });
        """

    def _navigator_webdriver(self):
        return """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """

    def _user_agent_override(self):
        return """
            Object.defineProperty(navigator, 'userAgent', {
                get: () => navigator.userAgent.replace('HeadlessChrome', 'Chrome')
            });
        """

    def _webgl_vendor(self):
        return """
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Intel Inc.';
                if (parameter === 37446) return 'Intel Iris OpenGL Engine';
                return getParameter.apply(this, arguments);
            };
        """

    def _window_outerdimensions(self):
        return """
            window.outerWidth = window.innerWidth;
            window.outerHeight = window.innerHeight + 85;
        """

    def _chrome_app(self):
        return """
            window.chrome.app = {
                isInstalled: false
            };
        """

    def _chrome_csi(self):
        return """
            window.chrome.csi = () => ({
                startE: Date.now(),
                onloadT: Date.now(),
                pageT: Date.now()
            });
        """

    def _chrome_load_times(self):
        return """
            window.chrome.loadTimes = () => ({
                requestTime: Date.now() / 1000,
                startLoadTime: Date.now() / 1000,
                commitLoadTime: Date.now() / 1000,
                finishDocumentLoadTime: Date.now() / 1000,
                finishLoadTime: Date.now() / 1000,
                firstPaintTime: Date.now() / 1000,
                firstPaintAfterLoadTime: 0,
                navigationType: 'Other',
                wasFetchedViaSpdy: false,
                wasNpnNegotiated: true,
                npnNegotiatedProtocol: 'h2',
                wasAlternateProtocolAvailable: false,
                connectionInfo: 'h2'
            });
        """
