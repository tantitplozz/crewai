"""
Purchase Orchestrator - Main workflow controller
"""
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from crewai import Crew, Task, Agent
from ..logger import Logger, WebSocketHandler
from ..gologin import GoLoginManager
from ..playwright import PlaywrightHandler
from ..payment import PaymentProcessor

class PurchaseOrchestrator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = Logger()
        self.websocket = WebSocketHandler(config.get('websocket_url', 'ws://localhost:8000'))
        self.gologin = GoLoginManager(config.get('gologin_token'))
        self.session_id = None

    async def initialize(self):
        """Initialize all components"""
        await self.websocket.connect()
        self.logger.info("Purchase Orchestrator initialized")

    async def execute_purchase(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main purchase workflow"""
        self.session_id = str(uuid.uuid4())
        result = {
            'session_id': self.session_id,
            'status': 'started',
            'started_at': datetime.now().isoformat(),
            'steps': []
        }

        try:
            # Step 1: Create/Load GoLogin Profile
            await self._log_step("profile_setup", "Setting up browser profile")
            profile = await self.gologin.get_or_create_profile(
                profile_id=order_data.get('profile_id')
            )
            result['steps'].append({
                'name': 'profile_setup',
                'status': 'success',
                'profile_id': profile['id']
            })

            # Step 2: Initialize Playwright with Profile
            await self._log_step("browser_init", "Initializing browser")
            browser_handler = PlaywrightHandler(profile)
            await browser_handler.initialize()
            result['steps'].append({
                'name': 'browser_init',
                'status': 'success'
            })

            # Step 3: Human-like warm up
            await self._log_step("warmup", "Warming up with human-like behavior")
            await browser_handler.warmup_session(order_data['target_site'])
            result['steps'].append({
                'name': 'warmup',
                'status': 'success'
            })

            # Step 4: Product Selection
            await self._log_step("product_selection", "Selecting products")
            await browser_handler.select_products(order_data['products'])
            result['steps'].append({
                'name': 'product_selection',
                'status': 'success',
                'products': order_data['products']
            })

            # Step 5: Checkout Process
            await self._log_step("checkout", "Processing checkout")
            checkout_data = await browser_handler.proceed_to_checkout()
            result['steps'].append({
                'name': 'checkout',
                'status': 'success',
                'data': checkout_data
            })

            # Step 6: Payment Processing
            await self._log_step("payment", "Processing payment")
            payment_processor = PaymentProcessor(browser_handler.page)
            payment_result = await payment_processor.process_payment(
                order_data['payment_info']
            )
            result['steps'].append({
                'name': 'payment',
                'status': 'success',
                'order_id': payment_result.get('order_id')
            })

            # Step 7: Cleanup
            await self._log_step("cleanup", "Cleaning up session")
            await browser_handler.cleanup()
            await self.gologin.cleanup_profile(profile['id'])

            result['status'] = 'completed'
            result['completed_at'] = datetime.now().isoformat()

        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            await self._log_step("error", f"Error occurred: {str(e)}", "error")

        finally:
            # Always log final result
            await self.logger.log_session(self.session_id, result)
            await self.websocket.send_update(result)

        return result

    async def _log_step(self, step_name: str, message: str, level: str = "info"):
        """Log step to all channels"""
        log_data = {
            'session_id': self.session_id,
            'step': step_name,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }

        if level == "error":
            self.logger.error(message, extra=log_data)
        else:
            self.logger.info(message, extra=log_data)

        await self.websocket.send_update({
            'type': 'step_update',
            'data': log_data
        })

    def create_crew(self) -> Crew:
        """Create CrewAI crew with agents"""
        browser_agent = Agent(
            role='Browser Automation Specialist',
            goal='Navigate websites like a human and complete purchases',
            backstory='Expert in mimicking human behavior and evading detection',
            verbose=True
        )

        payment_agent = Agent(
            role='Payment Processing Expert',
            goal='Handle payment forms securely and efficiently',
            backstory='Specialist in automated payment processing',
            verbose=True
        )

        logger_agent = Agent(
            role='System Monitor',
            goal='Track and log all activities for replay and debugging',
            backstory='Expert in system monitoring and logging',
            verbose=True
        )

        # Define tasks
        tasks = [
            Task(
                description='Set up browser profile and navigate to target site',
                agent=browser_agent
            ),
            Task(
                description='Select products and add to cart',
                agent=browser_agent
            ),
            Task(
                description='Process checkout and payment',
                agent=payment_agent
            ),
            Task(
                description='Log all activities and results',
                agent=logger_agent
            )
        ]

        return Crew(
            agents=[browser_agent, payment_agent, logger_agent],
            tasks=tasks,
            verbose=True
        )
