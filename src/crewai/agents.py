"""
CrewAI Agents for Purchase Automation
"""
from crewai import Agent
from typing import Dict, Any, List
import asyncio
import random

class BrowserAgent:
    """Agent responsible for browser automation"""

    def __init__(self, playwright_handler):
        self.browser = playwright_handler
        self.agent = Agent(
            role='Browser Automation Expert',
            goal='Navigate websites and complete purchases like a human',
            backstory='I am an expert at mimicking human browsing patterns',
            verbose=True,
            allow_delegation=False
        )

    async def browse_like_human(self, url: str):
        """Browse website with human-like behavior"""
        # Random delay before starting
        await asyncio.sleep(random.uniform(2, 5))

        # Navigate to homepage first
        await self.browser.goto(url)

        # Scroll and explore
        for _ in range(random.randint(3, 7)):
            await self.browser.random_scroll()
            await asyncio.sleep(random.uniform(1, 3))

        # Click random elements
        await self.browser.click_random_elements()

        return True

    async def search_products(self, keywords: List[str]):
        """Search for products with human behavior"""
        search_term = random.choice(keywords)

        # Type slowly like human
        await self.browser.human_type(search_term)
        await asyncio.sleep(random.uniform(0.5, 1.5))

        # Submit search
        await self.browser.submit_search()

        return True

    async def add_to_cart(self, product_selector: str):
        """Add product to cart with human delays"""
        # View product details first
        await self.browser.click(product_selector)
        await asyncio.sleep(random.uniform(2, 4))

        # Scroll through product page
        await self.browser.random_scroll()
        await asyncio.sleep(random.uniform(1, 2))

        # Add to cart
        await self.browser.click_add_to_cart()

        return True


class PaymentAgent:
    """Agent responsible for payment processing"""

    def __init__(self, payment_processor):
        self.payment = payment_processor
        self.agent = Agent(
            role='Payment Processing Specialist',
            goal='Complete payment forms accurately and securely',
            backstory='I handle automated payments with precision',
            verbose=True,
            allow_delegation=False
        )

    async def fill_payment_form(self, payment_info: Dict[str, Any]):
        """Fill payment form with provided information"""
        # Fill credit card info
        await self.payment.fill_card_number(payment_info['card_number'])
        await asyncio.sleep(random.uniform(0.5, 1))

        await self.payment.fill_expiry(payment_info['expiry'])
        await asyncio.sleep(random.uniform(0.3, 0.7))

        await self.payment.fill_cvv(payment_info['cvv'])
        await asyncio.sleep(random.uniform(0.3, 0.7))

        # Fill billing info
        await self.payment.fill_billing_info(payment_info['billing'])

        return True

    async def confirm_payment(self):
        """Confirm and submit payment"""
        # Double check filled info
        await asyncio.sleep(random.uniform(2, 4))

        # Submit payment
        await self.payment.submit_payment()

        return True


class LoggerAgent:
    """Agent responsible for logging and monitoring"""

    def __init__(self, logger, websocket):
        self.logger = logger
        self.websocket = websocket
        self.agent = Agent(
            role='System Monitor',
            goal='Track and log all activities for debugging and replay',
            backstory='I ensure complete visibility into system operations',
            verbose=True,
            allow_delegation=False
        )

    async def log_action(self, action: str, data: Dict[str, Any]):
        """Log action to all channels"""
        log_entry = {
            'action': action,
            'data': data,
            'timestamp': asyncio.get_event_loop().time()
        }

        # Log to file
        self.logger.info(f"Action: {action}", extra=log_entry)

        # Send to websocket
        await self.websocket.send_update({
            'type': 'action_log',
            'data': log_entry
        })

        return True

    async def capture_screenshot(self, page, name: str):
        """Capture and log screenshot"""
        screenshot_path = f"logs/screenshots/{name}.png"
        await page.screenshot(path=screenshot_path)

        await self.log_action('screenshot', {
            'name': name,
            'path': screenshot_path
        })

        return screenshot_path

    async def log_network_activity(self, requests: List[Dict]):
        """Log network requests for debugging"""
        for req in requests:
            await self.log_action('network_request', {
                'url': req['url'],
                'method': req['method'],
                'status': req.get('status'),
                'size': req.get('size')
            })

        return True
