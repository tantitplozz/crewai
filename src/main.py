"""
Main Entry Point for Automation System
"""
import asyncio
import json
import os
import sys
from typing import Dict, Any, Optional
from pathlib import Path
import argparse
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crewai import PurchaseOrchestrator
from logger import Logger, WebSocketServer
from payment import PaymentAutofill

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class AutomationSystem:
    """Main automation system controller"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.orchestrator = None
        self.logger = None
        self.websocket_server = None

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or environment"""
        # Default configuration
        config = {
            'gologin_token': os.getenv('GOLOGIN_TOKEN', ''),
            'mongodb_uri': os.getenv('MONGODB_URI', 'mongodb://localhost:27017'),
            'mongodb_enabled': os.getenv('MONGODB_ENABLED', 'false').lower() == 'true',
            'websocket_url': os.getenv('WEBSOCKET_URL', 'ws://localhost:8000'),
            'websocket_enabled': os.getenv('WEBSOCKET_ENABLED', 'true').lower() == 'true',
            'telegram_token': os.getenv('TELEGRAM_TOKEN', ''),
            'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID', ''),
            'telegram_enabled': os.getenv('TELEGRAM_ENABLED', 'false').lower() == 'true',
            'headless': os.getenv('HEADLESS', 'false').lower() == 'true',
            'screenshots_enabled': os.getenv('SCREENSHOTS_ENABLED', 'true').lower() == 'true',
            'log_level': os.getenv('LOG_LEVEL', 'INFO')
        }

        # Load from config file if provided
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)

        return config

    async def initialize(self):
        """Initialize all system components"""
        print("🚀 Initializing Automation System...")

        # Initialize logger
        self.logger = Logger(self.config)

        # Initialize orchestrator
        self.orchestrator = PurchaseOrchestrator(self.config)
        await self.orchestrator.initialize()

        # Start WebSocket server if enabled
        if self.config['websocket_enabled']:
            self.websocket_server = WebSocketServer()
            asyncio.create_task(self._run_websocket_server())

        print("✅ System initialized successfully!")

    async def _run_websocket_server(self):
        """Run WebSocket server in background"""
        try:
            await self.websocket_server.start()
        except Exception as e:
            print(f"WebSocket server error: {e}")

    async def execute_order(self, order_file: str) -> Dict[str, Any]:
        """Execute order from JSON file"""
        # Load order data
        with open(order_file, 'r') as f:
            order_data = json.load(f)

        print(f"\n📋 Processing order: {order_data.get('name', 'Unknown')}")
        print(f"Target site: {order_data.get('target_site', 'Unknown')}")
        print(f"Products: {len(order_data.get('products', []))}")

        # Execute purchase
        result = await self.orchestrator.execute_purchase(order_data)

        # Print summary
        if result['status'] == 'completed':
            print(f"\n✅ Order completed successfully!")
            if 'order_info' in result['steps'][-1]:
                print(f"Order ID: {result['steps'][-1]['order_info'].get('order_id', 'N/A')}")
        else:
            print(f"\n❌ Order failed: {result.get('error', 'Unknown error')}")

        return result

    async def batch_execute(self, orders_dir: str):
        """Execute multiple orders from directory"""
        orders_path = Path(orders_dir)
        order_files = list(orders_path.glob('*.json'))

        print(f"\n📦 Found {len(order_files)} orders to process")

        results = []
        for i, order_file in enumerate(order_files, 1):
            print(f"\n{'='*50}")
            print(f"Processing order {i}/{len(order_files)}: {order_file.name}")
            print(f"{'='*50}")

            try:
                result = await self.execute_order(str(order_file))
                results.append({
                    'file': order_file.name,
                    'result': result
                })

                # Delay between orders
                if i < len(order_files):
                    await asyncio.sleep(30)  # 30 seconds between orders

            except Exception as e:
                print(f"Failed to process {order_file.name}: {e}")
                results.append({
                    'file': order_file.name,
                    'result': {'status': 'failed', 'error': str(e)}
                })

        # Save batch results
        batch_report = {
            'timestamp': datetime.now().isoformat(),
            'total_orders': len(order_files),
            'completed': len([r for r in results if r['result']['status'] == 'completed']),
            'failed': len([r for r in results if r['result']['status'] == 'failed']),
            'results': results
        }

        report_file = f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(batch_report, f, indent=2)

        print(f"\n📊 Batch execution complete. Report saved to: {report_file}")

    async def interactive_mode(self):
        """Interactive mode with menu"""
        while True:
            print("\n" + "="*50)
            print("🤖 AUTOMATION SYSTEM - MAIN MENU")
            print("="*50)
            print("1. Execute single order")
            print("2. Batch execute orders")
            print("3. Create test order")
            print("4. View recent sessions")
            print("5. Test payment profiles")
            print("6. System status")
            print("0. Exit")
            print("="*50)

            choice = input("\nSelect option: ").strip()

            if choice == '0':
                print("👋 Goodbye!")
                break
            elif choice == '1':
                await self._interactive_single_order()
            elif choice == '2':
                await self._interactive_batch_orders()
            elif choice == '3':
                self._create_test_order()
            elif choice == '4':
                await self._view_recent_sessions()
            elif choice == '5':
                self._test_payment_profiles()
            elif choice == '6':
                await self._show_system_status()
            else:
                print("❌ Invalid option")

    async def _interactive_single_order(self):
        """Interactive single order execution"""
        order_file = input("Enter order file path: ").strip()

        if not os.path.exists(order_file):
            print("❌ File not found")
            return

        await self.execute_order(order_file)

    async def _interactive_batch_orders(self):
        """Interactive batch order execution"""
        orders_dir = input("Enter orders directory path: ").strip()

        if not os.path.isdir(orders_dir):
            print("❌ Directory not found")
            return

        await self.batch_execute(orders_dir)

    def _create_test_order(self):
        """Create a test order file"""
        print("\n📝 Creating test order...")

        # Get basic info
        target_site = input("Target site URL: ").strip()
        product_url = input("Product URL: ").strip()
        quantity = int(input("Quantity (default 1): ").strip() or "1")

        # Create payment profile
        autofill = PaymentAutofill()
        billing = autofill.generate_billing_address()
        card = autofill.generate_test_card()

        # Create order
        order = {
            "name": f"Test Order - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "target_site": target_site,
            "products": [
                {
                    "name": "Test Product",
                    "url": product_url,
                    "quantity": quantity
                }
            ],
            "payment_info": {
                "card_number": card['card_number'],
                "expiry": card['expiry'],
                "cvv": card['cvv'],
                "cardholder_name": f"{billing['first_name']} {billing['last_name']}"
            },
            "billing": billing
        }

        # Save order
        filename = f"test_order_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(order, f, indent=2)

        print(f"✅ Test order saved to: {filename}")

    async def _view_recent_sessions(self):
        """View recent session logs"""
        if self.logger.mongo_handler:
            sessions = await self.logger.mongo_handler.get_recent_sessions(10)

            print("\n📋 Recent Sessions:")
            print("="*80)

            for session in sessions:
                status_icon = "✅" if session['status'] == 'completed' else "❌"
                print(f"{status_icon} {session['session_id']} - {session['status']} - {session['created_at']}")

                summary = session.get('summary', {})
                if summary.get('order_id'):
                    print(f"   Order ID: {summary['order_id']}")
                if summary.get('duration'):
                    print(f"   Duration: {summary['duration']}s")

                print()
        else:
            print("❌ MongoDB not enabled")

    def _test_payment_profiles(self):
        """Test payment profile generation"""
        autofill = PaymentAutofill()

        print("\n💳 Test Payment Profiles:")
        print("="*50)

        for card_type in ['visa', 'mastercard', 'amex', 'discover']:
            card = autofill.generate_test_card(card_type)
            print(f"\n{card_type.upper()}:")
            print(f"  Number: {card['card_number']}")
            print(f"  Expiry: {card['expiry']}")
            print(f"  CVV: {card['cvv']}")

        print("\n📍 Test Billing Address:")
        billing = autofill.generate_billing_address()
        for key, value in billing.items():
            print(f"  {key}: {value}")

    async def _show_system_status(self):
        """Show system status"""
        print("\n📊 System Status:")
        print("="*50)

        # Check components
        components = {
            'Orchestrator': '✅' if self.orchestrator else '❌',
            'Logger': '✅' if self.logger else '❌',
            'WebSocket': '✅' if self.websocket_server else '❌',
            'MongoDB': '✅' if self.logger.mongo_handler and self.logger.mongo_handler.client else '❌',
            'Telegram': '✅' if self.logger.telegram_notifier else '❌'
        }

        for component, status in components.items():
            print(f"{status} {component}")

        # Show statistics if MongoDB is available
        if self.logger.mongo_handler and self.logger.mongo_handler.client:
            stats = await self.logger.mongo_handler.get_statistics()

            print("\n📈 Statistics:")
            print(f"  Total Sessions: {stats.get('total_sessions', 0)}")
            print(f"  Total Actions: {stats.get('total_actions', 0)}")
            print(f"  Total Logs: {stats.get('total_logs', 0)}")

            if 'sessions_by_status' in stats:
                print("\n  Sessions by Status:")
                for status, count in stats['sessions_by_status'].items():
                    print(f"    {status}: {count}")

    async def cleanup(self):
        """Clean up resources"""
        if self.logger:
            await self.logger.close()

        print("\n🧹 System cleaned up")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Automation System')
    parser.add_argument('--config', help='Config file path')
    parser.add_argument('--order', help='Execute single order file')
    parser.add_argument('--batch', help='Batch execute orders from directory')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')

    args = parser.parse_args()

    # Create system
    system = AutomationSystem(args.config)

    try:
        # Initialize
        await system.initialize()

        # Execute based on arguments
        if args.order:
            await system.execute_order(args.order)
        elif args.batch:
            await system.batch_execute(args.batch)
        elif args.interactive:
            await system.interactive_mode()
        else:
            # Default to interactive mode
            await system.interactive_mode()

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ System error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await system.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
