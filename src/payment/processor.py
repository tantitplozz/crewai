"""
Payment Processor - Handle payment form filling and submission
"""
from playwright.async_api import Page
import asyncio
import random
from typing import Dict, Any, Optional
from datetime import datetime
from ..playwright.human_mimic import HumanMimic

class PaymentProcessor:
    """Process payment forms automatically"""

    def __init__(self, page: Page):
        self.page = page
        self.human_mimic = HumanMimic()
        self.filled_fields = {}

    async def process_payment(self, payment_info: Dict[str, Any]) -> Dict[str, Any]:
        """Main payment processing flow"""
        result = {
            'status': 'started',
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Fill payment form
            await self.fill_payment_form(payment_info)
            result['form_filled'] = True

            # Fill billing information
            if 'billing' in payment_info:
                await self.fill_billing_info(payment_info['billing'])
                result['billing_filled'] = True

            # Accept terms if needed
            await self.accept_terms()

            # Submit payment
            order_info = await self.submit_payment()

            result.update({
                'status': 'completed',
                'order_info': order_info,
                'completed_at': datetime.now().isoformat()
            })

        except Exception as e:
            result.update({
                'status': 'failed',
                'error': str(e),
                'failed_at': datetime.now().isoformat()
            })

        return result

    async def fill_payment_form(self, payment_info: Dict[str, Any]):
        """Fill payment form fields"""
        # Credit card number
        if 'card_number' in payment_info:
            await self.fill_card_number(payment_info['card_number'])

        # Expiry date
        if 'expiry' in payment_info:
            await self.fill_expiry(payment_info['expiry'])

        # CVV/CVC
        if 'cvv' in payment_info:
            await self.fill_cvv(payment_info['cvv'])

        # Cardholder name
        if 'cardholder_name' in payment_info:
            await self.fill_cardholder_name(payment_info['cardholder_name'])

    async def fill_card_number(self, card_number: str):
        """Fill credit card number with human-like behavior"""
        # Remove spaces from card number
        card_number = card_number.replace(' ', '').replace('-', '')

        # Find card number input
        selectors = [
            'input[name*="cardnumber" i]',
            'input[name*="card-number" i]',
            'input[name*="card_number" i]',
            'input[id*="cardnumber" i]',
            'input[placeholder*="card number" i]',
            'input[autocomplete="cc-number"]',
            'input[type="tel"][name*="card" i]'
        ]

        for selector in selectors:
            try:
                input_elem = await self.page.wait_for_selector(selector, timeout=5000)
                await input_elem.click()
                await input_elem.fill('')

                # Type card number in groups
                for i in range(0, len(card_number), 4):
                    group = card_number[i:i+4]
                    for char in group:
                        await self.page.keyboard.type(char)
                        await asyncio.sleep(random.uniform(0.05, 0.15))

                    # Pause between groups
                    if i < len(card_number) - 4:
                        await asyncio.sleep(random.uniform(0.2, 0.4))

                self.filled_fields['card_number'] = True
                return
            except:
                continue

        # Try iframe (for embedded payment forms)
        await self._try_iframe_payment('card_number', card_number)

    async def fill_expiry(self, expiry: str):
        """Fill expiry date (MM/YY or MM/YYYY format)"""
        # Parse expiry
        parts = expiry.replace('/', '').replace('-', '').replace(' ', '')
        if len(parts) == 4:  # MMYY
            month = parts[:2]
            year = parts[2:]
        elif len(parts) == 6:  # MMYYYY
            month = parts[:2]
            year = parts[4:]  # Last 2 digits
        else:
            month = expiry[:2]
            year = expiry[-2:]

        # Try combined expiry field first
        combined_selectors = [
            'input[name*="expiry" i]',
            'input[name*="exp" i]',
            'input[placeholder*="MM/YY" i]',
            'input[autocomplete="cc-exp"]'
        ]

        for selector in combined_selectors:
            try:
                input_elem = await self.page.wait_for_selector(selector, timeout=3000)
                await input_elem.click()
                await input_elem.fill('')
                await self.human_mimic.human_type(self.page, input_elem, f"{month}/{year}")
                self.filled_fields['expiry'] = True
                return
            except:
                continue

        # Try separate month/year fields
        await self._fill_separate_expiry(month, year)

    async def fill_cvv(self, cvv: str):
        """Fill CVV/CVC code"""
        selectors = [
            'input[name*="cvv" i]',
            'input[name*="cvc" i]',
            'input[name*="security" i]',
            'input[id*="cvv" i]',
            'input[placeholder*="CVV" i]',
            'input[placeholder*="CVC" i]',
            'input[autocomplete="cc-csc"]',
            'input[type="tel"][maxlength="3"]',
            'input[type="tel"][maxlength="4"]'
        ]

        for selector in selectors:
            try:
                input_elem = await self.page.wait_for_selector(selector, timeout=5000)
                await input_elem.click()
                await input_elem.fill('')
                await self.human_mimic.human_type(self.page, input_elem, cvv)
                self.filled_fields['cvv'] = True
                return
            except:
                continue

        # Try iframe
        await self._try_iframe_payment('cvv', cvv)

    async def fill_cardholder_name(self, name: str):
        """Fill cardholder name"""
        selectors = [
            'input[name*="cardholder" i]',
            'input[name*="name" i][name*="card" i]',
            'input[id*="cardholder" i]',
            'input[placeholder*="name on card" i]',
            'input[placeholder*="cardholder" i]',
            'input[autocomplete="cc-name"]'
        ]

        for selector in selectors:
            try:
                input_elem = await self.page.wait_for_selector(selector, timeout=3000)
                await input_elem.click()
                await input_elem.fill('')
                await self.human_mimic.human_type(self.page, input_elem, name)
                self.filled_fields['cardholder_name'] = True
                return
            except:
                continue

    async def fill_billing_info(self, billing: Dict[str, Any]):
        """Fill billing address information"""
        # Map of billing fields to selectors
        field_map = {
            'first_name': ['input[name*="firstname" i]', 'input[name*="first_name" i]', 'input[id*="firstname" i]'],
            'last_name': ['input[name*="lastname" i]', 'input[name*="last_name" i]', 'input[id*="lastname" i]'],
            'email': ['input[type="email"]', 'input[name*="email" i]', 'input[id*="email" i]'],
            'phone': ['input[type="tel"]', 'input[name*="phone" i]', 'input[name*="tel" i]'],
            'address': ['input[name*="address1" i]', 'input[name*="street" i]', 'input[name*="address" i]:not([name*="2"])'],
            'address2': ['input[name*="address2" i]', 'input[name*="apt" i]', 'input[name*="suite" i]'],
            'city': ['input[name*="city" i]', 'input[id*="city" i]'],
            'state': ['input[name*="state" i]', 'select[name*="state" i]', 'input[name*="province" i]'],
            'zip': ['input[name*="zip" i]', 'input[name*="postal" i]', 'input[name*="postcode" i]'],
            'country': ['select[name*="country" i]', 'input[name*="country" i]']
        }

        for field, value in billing.items():
            if field in field_map:
                await self._fill_field(field_map[field], value)
                await asyncio.sleep(random.uniform(0.5, 1))

    async def accept_terms(self):
        """Accept terms and conditions if present"""
        checkbox_selectors = [
            'input[type="checkbox"][name*="terms" i]',
            'input[type="checkbox"][name*="agree" i]',
            'input[type="checkbox"][name*="accept" i]',
            'input[type="checkbox"]:near(:text("terms"))',
            'input[type="checkbox"]:near(:text("agree"))'
        ]

        for selector in checkbox_selectors:
            try:
                checkbox = await self.page.wait_for_selector(selector, timeout=2000)
                is_checked = await checkbox.is_checked()
                if not is_checked:
                    await self.human_mimic.human_click(self.page, checkbox)
                    await asyncio.sleep(random.uniform(0.5, 1))
            except:
                continue

    async def submit_payment(self) -> Dict[str, Any]:
        """Submit the payment form"""
        # Find and click submit button
        submit_selectors = [
            'button[type="submit"]:has-text("Pay")',
            'button[type="submit"]:has-text("Complete")',
            'button[type="submit"]:has-text("Place Order")',
            'button[type="submit"]:has-text("Submit")',
            'button:has-text("Pay Now")',
            'button:has-text("Complete Order")',
            'button:has-text("Confirm")',
            'input[type="submit"][value*="Pay" i]',
            'button[class*="pay" i][class*="button" i]'
        ]

        for selector in submit_selectors:
            try:
                submit_btn = await self.page.wait_for_selector(selector, timeout=5000)

                # Scroll to button
                await submit_btn.scroll_into_view_if_needed()
                await asyncio.sleep(random.uniform(1, 2))

                # Take screenshot before submission
                await self.page.screenshot(path='screenshots/before_payment_submit.png')

                # Click submit
                await self.human_mimic.human_click(self.page, submit_btn)

                # Wait for response
                await self.page.wait_for_load_state('networkidle', timeout=30000)

                # Extract order information
                order_info = await self._extract_order_info()

                return order_info
            except:
                continue

        raise Exception("Could not find payment submit button")

    async def _fill_field(self, selectors: list, value: str):
        """Fill a form field with given selectors"""
        for selector in selectors:
            try:
                elem = await self.page.wait_for_selector(selector, timeout=3000)

                # Check if it's a select element
                tag_name = await elem.evaluate('el => el.tagName')
                if tag_name.lower() == 'select':
                    await elem.select_option(value=value)
                else:
                    await elem.click()
                    await elem.fill('')
                    await self.human_mimic.human_type(self.page, elem, value)

                return
            except:
                continue

    async def _fill_separate_expiry(self, month: str, year: str):
        """Fill separate month and year fields"""
        # Month selectors
        month_selectors = [
            'input[name*="month" i]',
            'select[name*="month" i]',
            'input[placeholder*="MM" i]',
            'select[autocomplete="cc-exp-month"]'
        ]

        # Year selectors
        year_selectors = [
            'input[name*="year" i]',
            'select[name*="year" i]',
            'input[placeholder*="YY" i]',
            'select[autocomplete="cc-exp-year"]'
        ]

        # Fill month
        for selector in month_selectors:
            try:
                elem = await self.page.wait_for_selector(selector, timeout=3000)
                tag_name = await elem.evaluate('el => el.tagName')

                if tag_name.lower() == 'select':
                    await elem.select_option(value=month)
                else:
                    await elem.click()
                    await elem.fill('')
                    await self.human_mimic.human_type(self.page, elem, month)

                break
            except:
                continue

        # Fill year
        for selector in year_selectors:
            try:
                elem = await self.page.wait_for_selector(selector, timeout=3000)
                tag_name = await elem.evaluate('el => el.tagName')

                if tag_name.lower() == 'select':
                    # Try full year first, then 2-digit
                    try:
                        await elem.select_option(value=f"20{year}")
                    except:
                        await elem.select_option(value=year)
                else:
                    await elem.click()
                    await elem.fill('')
                    await self.human_mimic.human_type(self.page, elem, year)

                break
            except:
                continue

    async def _try_iframe_payment(self, field_type: str, value: str):
        """Try to fill payment fields in iframes (Stripe, etc)"""
        iframes = await self.page.query_selector_all('iframe')

        for iframe in iframes:
            try:
                frame = await iframe.content_frame()
                if not frame:
                    continue

                # Try to fill field in iframe
                if field_type == 'card_number':
                    input_elem = await frame.wait_for_selector('input[name*="number" i]', timeout=2000)
                elif field_type == 'cvv':
                    input_elem = await frame.wait_for_selector('input[name*="cvc" i]', timeout=2000)
                else:
                    continue

                await input_elem.click()
                await input_elem.fill('')
                await frame.keyboard.type(value)

                self.filled_fields[field_type] = True
                return
            except:
                continue

    async def _extract_order_info(self) -> Dict[str, Any]:
        """Extract order confirmation information"""
        order_info = {}

        # Try to find order number
        order_selectors = [
            'text=/order\s*#?\s*(\d+)/i',
            'text=/order\s*number[:\s]*(\d+)/i',
            'text=/confirmation\s*#?\s*(\w+)/i'
        ]

        for selector in order_selectors:
            try:
                elem = await self.page.wait_for_selector(selector, timeout=5000)
                text = await elem.text_content()
                # Extract number/ID from text
                import re
                match = re.search(r'[\d\w]{6,}', text)
                if match:
                    order_info['order_id'] = match.group()
                    break
            except:
                continue

        # Get current URL (might contain order ID)
        order_info['confirmation_url'] = self.page.url

        # Take screenshot of confirmation
        await self.page.screenshot(path='screenshots/order_confirmation.png')
        order_info['screenshot'] = 'screenshots/order_confirmation.png'

        return order_info
