"""
Human Behavior Mimicking Module
"""
from playwright.async_api import Page, ElementHandle
import asyncio
import random
import math
from typing import Tuple, List, Optional

class HumanMimic:
    """Mimic human behavior for browser automation"""

    def __init__(self):
        self.min_typing_delay = 50  # ms
        self.max_typing_delay = 150  # ms
        self.typo_probability = 0.05
        self.mouse_speed = 800  # pixels per second

    async def human_type(self, page: Page, element: ElementHandle, text: str):
        """Type text with human-like delays and occasional typos"""
        await element.focus()

        for i, char in enumerate(text):
            # Occasionally make typos
            if random.random() < self.typo_probability and i > 0 and i < len(text) - 1:
                # Type wrong character
                wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                await page.keyboard.type(wrong_char)
                await asyncio.sleep(random.uniform(0.1, 0.3))

                # Delete and correct
                await page.keyboard.press('Backspace')
                await asyncio.sleep(random.uniform(0.05, 0.15))

            # Type the actual character
            await page.keyboard.type(char)

            # Human-like delay between keystrokes
            delay = random.uniform(self.min_typing_delay, self.max_typing_delay) / 1000

            # Longer pause after punctuation
            if char in '.,!?;:':
                delay *= random.uniform(1.5, 2.5)

            # Longer pause after spaces occasionally
            elif char == ' ' and random.random() < 0.3:
                delay *= random.uniform(1.2, 1.8)

            await asyncio.sleep(delay)

    async def human_click(self, page: Page, element: ElementHandle):
        """Click element with human-like mouse movement"""
        # Get element position
        box = await element.bounding_box()
        if not box:
            await element.click()
            return

        # Calculate target position with small random offset
        target_x = box['x'] + box['width'] / 2 + random.uniform(-5, 5)
        target_y = box['y'] + box['height'] / 2 + random.uniform(-5, 5)

        # Move mouse to target with bezier curve
        await self._human_mouse_move(page, target_x, target_y)

        # Small pause before click
        await asyncio.sleep(random.uniform(0.05, 0.15))

        # Click with random hold duration
        await page.mouse.down()
        await asyncio.sleep(random.uniform(0.05, 0.15))
        await page.mouse.up()

    async def _human_mouse_move(self, page: Page, target_x: float, target_y: float):
        """Move mouse with human-like curve"""
        # Get current mouse position (approximate)
        current_x = await page.evaluate('window.mouseX || 0')
        current_y = await page.evaluate('window.mouseY || 0')

        # Calculate distance
        distance = math.sqrt((target_x - current_x)**2 + (target_y - current_y)**2)

        # Calculate number of steps based on distance and speed
        steps = max(10, int(distance / 50))

        # Generate bezier curve control points
        control_x1 = current_x + (target_x - current_x) * 0.25 + random.uniform(-30, 30)
        control_y1 = current_y + (target_y - current_y) * 0.25 + random.uniform(-30, 30)
        control_x2 = current_x + (target_x - current_x) * 0.75 + random.uniform(-30, 30)
        control_y2 = current_y + (target_y - current_y) * 0.75 + random.uniform(-30, 30)

        # Move along bezier curve
        for i in range(steps + 1):
            t = i / steps
            # Cubic bezier formula
            x = (1-t)**3 * current_x + 3*(1-t)**2*t * control_x1 + 3*(1-t)*t**2 * control_x2 + t**3 * target_x
            y = (1-t)**3 * current_y + 3*(1-t)**2*t * control_y1 + 3*(1-t)*t**2 * control_y2 + t**3 * target_y

            await page.mouse.move(x, y)

            # Variable delay based on distance
            if i < steps:
                delay = random.uniform(0.001, 0.003) * (distance / self.mouse_speed)
                await asyncio.sleep(delay)

        # Store mouse position for next movement
        await page.evaluate(f'window.mouseX = {target_x}; window.mouseY = {target_y};')

    async def random_scroll(self, page: Page):
        """Perform random scrolling like a human"""
        # Get current scroll position and page height
        scroll_info = await page.evaluate('''() => ({
            scrollY: window.scrollY,
            innerHeight: window.innerHeight,
            scrollHeight: document.body.scrollHeight
        })''')

        current_scroll = scroll_info['scrollY']
        viewport_height = scroll_info['innerHeight']
        total_height = scroll_info['scrollHeight']

        # Decide scroll direction and distance
        if current_scroll < total_height - viewport_height:
            # Can scroll down
            max_scroll = min(viewport_height * 0.8, total_height - viewport_height - current_scroll)
            scroll_distance = random.uniform(100, max_scroll)
        else:
            # At bottom, scroll up
            scroll_distance = -random.uniform(100, viewport_height * 0.5)

        # Perform smooth scroll
        await self._smooth_scroll(page, scroll_distance)

    async def _smooth_scroll(self, page: Page, distance: float):
        """Smooth scrolling animation"""
        steps = 20
        step_distance = distance / steps

        for i in range(steps):
            # Ease-out function for natural deceleration
            progress = i / steps
            eased_progress = 1 - (1 - progress) ** 3

            await page.evaluate(f'window.scrollBy(0, {step_distance})')
            await asyncio.sleep(random.uniform(0.01, 0.03))

    async def explore_site(self, page: Page):
        """Explore website like a human"""
        # Random scrolling
        for _ in range(random.randint(2, 4)):
            await self.random_scroll(page)
            await asyncio.sleep(random.uniform(1, 3))

        # Read some content (simulate with pauses)
        await asyncio.sleep(random.uniform(2, 5))

        # Move mouse randomly
        for _ in range(random.randint(3, 6)):
            x = random.uniform(100, 800)
            y = random.uniform(100, 600)
            await self._human_mouse_move(page, x, y)
            await asyncio.sleep(random.uniform(0.5, 1.5))

    async def random_actions(self, page: Page):
        """Perform random human-like actions"""
        actions = [
            self._hover_random_element,
            self._click_random_link,
            self._scroll_randomly,
            self._move_mouse_randomly
        ]

        # Perform 2-4 random actions
        for _ in range(random.randint(2, 4)):
            action = random.choice(actions)
            try:
                await action(page)
            except:
                pass  # Ignore errors in random actions
            await asyncio.sleep(random.uniform(1, 3))

    async def _hover_random_element(self, page: Page):
        """Hover over random element"""
        elements = await page.query_selector_all('a, button, img')
        if elements:
            element = random.choice(elements)
            box = await element.bounding_box()
            if box:
                x = box['x'] + box['width'] / 2
                y = box['y'] + box['height'] / 2
                await self._human_mouse_move(page, x, y)
                await asyncio.sleep(random.uniform(0.5, 1.5))

    async def _click_random_link(self, page: Page):
        """Click a random link (but don't navigate away)"""
        links = await page.query_selector_all('a[href^="#"]')  # Only fragment links
        if links:
            link = random.choice(links)
            await self.human_click(page, link)

    async def _scroll_randomly(self, page: Page):
        """Scroll randomly on the page"""
        await self.random_scroll(page)

    async def _move_mouse_randomly(self, page: Page):
        """Move mouse to random position"""
        x = random.uniform(100, 800)
        y = random.uniform(100, 600)
        await self._human_mouse_move(page, x, y)

    async def click_random_elements(self, page: Page, count: int = 3):
        """Click random elements on page to simulate exploration"""
        # Get clickable elements
        elements = await page.query_selector_all('a, button, [onclick]')

        # Filter out dangerous elements
        safe_elements = []
        for elem in elements[:20]:  # Limit to first 20
            try:
                href = await elem.get_attribute('href')
                onclick = await elem.get_attribute('onclick')

                # Skip external links and javascript: links
                if href and (href.startswith('http') or href.startswith('javascript:')):
                    continue

                # Skip logout/signout buttons
                text = await elem.text_content()
                if text and any(word in text.lower() for word in ['logout', 'signout', 'sign out']):
                    continue

                safe_elements.append(elem)
            except:
                continue

        # Click random safe elements
        for _ in range(min(count, len(safe_elements))):
            element = random.choice(safe_elements)
            safe_elements.remove(element)

            try:
                await self.human_click(page, element)
                await asyncio.sleep(random.uniform(1, 2))

                # Sometimes go back
                if random.random() < 0.5:
                    await page.go_back()
                    await asyncio.sleep(random.uniform(1, 2))
            except:
                continue
