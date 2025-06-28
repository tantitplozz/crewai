"""
Playwright Handler for Browser Automation
"""
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import asyncio
import random
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
from ..gologin import ProfileHandler
from .stealth import StealthPlugin
from .human_mimic import HumanMimic

class PlaywrightHandler:
    """Main handler for Playwright browser automation"""

    def __init__(self, profile_data: Dict[str, Any]):
        self.profile_handler = ProfileHandler(profile_data)
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.stealth = StealthPlugin()
        self.human_mimic = HumanMimic()
        self.screenshots = []

    async def initialize(self):
        """Initialize browser with GoLogin profile"""
        # Start Playwright
        self.playwright = await async_playwright().start()

        # Get browser args from profile
        browser_args = self.profile_handler.get_browser_args()
        context_options = self.profile_handler.get_browser_context_options()

        # Launch browser
        self.browser = await self.playwright.chromium.launch(
            headless=False,  # Set to True for production
            args=browser_args,
            channel='chrome'
        )

        # Create context with profile settings
        self.context = await self.browser.new_context(**context_options)

        # Apply stealth techniques
        await self.stealth.apply_to_context(self.context)

        # Create page
        self.page = await self.context.new_page()

        # Apply stealth to page
        await self.stealth.apply_to_page(self.page)

        # Set up request interception
        await self._setup_request_interception()

    async def warmup_session(self, target_site: str):
        """Warm up session with human-like behavior"""
        # Visit homepage
        await self.goto(target_site)
        await self.take_screenshot('homepage')

        # Random exploration
        await self.human_mimic.explore_site(self.page)

        # Visit common pages
        common_pages = ['/about', '/contact', '/products', '/categories']
        for _ in range(random.randint(2, 4)):
            page_path = random.choice(common_pages)
            try:
                await self.goto(f"{target_site}{page_path}")
                await self.human_mimic.random_actions(self.page)
            except:
                pass  # Page might not exist

    async def select_products(self, products: List[Dict[str, Any]]):
        """Select and add products to cart"""
        for product in products:
            # Search for product
            if 'search_term' in product:
                await self.search_product(product['search_term'])
            elif 'url' in product:
                await self.goto(product['url'])

            # Add to cart
            await self.add_product_to_cart(product)

            # Human-like delay
            await asyncio.sleep(random.uniform(2, 5))

    async def search_product(self, search_term: str):
        """Search for product with human-like typing"""
        # Find search input
        search_input = await self.page.wait_for_selector(
            'input[type="search"], input[name="q"], input[placeholder*="search" i]',
            timeout=10000
        )

        # Click and clear
        await search_input.click()
        await search_input.fill('')

        # Type like human
        await self.human_mimic.human_type(self.page, search_input, search_term)

        # Submit search
        await self.page.keyboard.press('Enter')
        await self.page.wait_for_load_state('networkidle')

    async def add_product_to_cart(self, product: Dict[str, Any]):
        """Add product to cart with human behavior"""
        # Click on product if needed
        if 'selector' in product:
            product_elem = await self.page.wait_for_selector(product['selector'])
            await self.human_mimic.human_click(self.page, product_elem)
            await self.page.wait_for_load_state('networkidle')

        # Select options if needed
        if 'options' in product:
            for option_name, option_value in product['options'].items():
                await self._select_product_option(option_name, option_value)

        # Select quantity
        if 'quantity' in product and product['quantity'] > 1:
            await self._set_quantity(product['quantity'])

        # Find and click add to cart button
        add_to_cart_selectors = [
            'button[class*="add-to-cart" i]',
            'button[class*="addtocart" i]',
            'button[id*="add-to-cart" i]',
            'button:has-text("Add to Cart")',
            'button:has-text("Add to Bag")',
            'input[value*="Add to Cart" i]'
        ]

        for selector in add_to_cart_selectors:
            try:
                button = await self.page.wait_for_selector(selector, timeout=5000)
                await self.human_mimic.human_click(self.page, button)
                await self.take_screenshot(f'added_to_cart_{product.get("name", "product")}')
                break
            except:
                continue

        # Wait for cart update
        await asyncio.sleep(random.uniform(1, 2))

    async def proceed_to_checkout(self) -> Dict[str, Any]:
        """Proceed to checkout page"""
        checkout_data = {}

        # Go to cart first
        cart_selectors = [
            'a[href*="/cart"]',
            'a[href*="/bag"]',
            'button[class*="cart"]',
            'div[class*="cart-icon"]'
        ]

        for selector in cart_selectors:
            try:
                cart_elem = await self.page.wait_for_selector(selector, timeout=5000)
                await self.human_mimic.human_click(self.page, cart_elem)
                await self.page.wait_for_load_state('networkidle')
                break
            except:
                continue

        await self.take_screenshot('cart_page')

        # Click checkout button
        checkout_selectors = [
            'button:has-text("Checkout")',
            'button:has-text("Proceed to Checkout")',
            'a[href*="/checkout"]',
            'button[class*="checkout"]'
        ]

        for selector in checkout_selectors:
            try:
                checkout_btn = await self.page.wait_for_selector(selector, timeout=5000)
                await self.human_mimic.human_click(self.page, checkout_btn)
                await self.page.wait_for_load_state('networkidle')
                checkout_data['checkout_url'] = self.page.url
                break
            except:
                continue

        await self.take_screenshot('checkout_page')

        return checkout_data

    async def goto(self, url: str):
        """Navigate to URL with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await self.page.goto(url, wait_until='networkidle', timeout=30000)
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                else:
                    raise e

    async def take_screenshot(self, name: str):
        """Take screenshot and save"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"screenshots/{timestamp}_{name}.png"

        # Create directory if not exists
        os.makedirs('screenshots', exist_ok=True)

        await self.page.screenshot(path=filename, full_page=False)
        self.screenshots.append(filename)

        return filename

    async def cleanup(self):
        """Clean up browser resources"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

        # Clean up profile
        self.profile_handler.cleanup()

    async def _setup_request_interception(self):
        """Set up request interception for monitoring"""
        async def handle_route(route):
            # Log request
            request = route.request
            print(f"Request: {request.method} {request.url}")

            # Continue request
            await route.continue_()

        # Intercept all requests
        await self.page.route('**/*', handle_route)

    async def _select_product_option(self, option_name: str, option_value: str):
        """Select product option (size, color, etc)"""
        # Try select dropdown first
        selects = await self.page.query_selector_all('select')
        for select in selects:
            label = await select.get_attribute('aria-label') or ''
            name = await select.get_attribute('name') or ''
            if option_name.lower() in label.lower() or option_name.lower() in name.lower():
                await select.select_option(value=option_value)
                return

        # Try radio buttons or clickable options
        option_selectors = [
            f'input[value="{option_value}"]',
            f'label:has-text("{option_value}")',
            f'button:has-text("{option_value}")',
            f'div[class*="option"]:has-text("{option_value}")'
        ]

        for selector in option_selectors:
            try:
                option_elem = await self.page.wait_for_selector(selector, timeout=3000)
                await self.human_mimic.human_click(self.page, option_elem)
                return
            except:
                continue

    async def _set_quantity(self, quantity: int):
        """Set product quantity"""
        # Find quantity input
        qty_selectors = [
            'input[name*="quantity" i]',
            'input[id*="quantity" i]',
            'input[type="number"]'
        ]

        for selector in qty_selectors:
            try:
                qty_input = await self.page.wait_for_selector(selector, timeout=3000)
                await qty_input.click()
                await qty_input.fill('')
                await self.human_mimic.human_type(self.page, qty_input, str(quantity))
                return
            except:
                continue
