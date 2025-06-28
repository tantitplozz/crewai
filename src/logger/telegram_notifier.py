"""
Telegram Notifier for Real-time Alerts
"""
import aiohttp
import asyncio
from typing import Optional, Dict, Any, List
import os

class TelegramNotifier:
    """Send notifications via Telegram Bot"""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def send_message(self, text: str, parse_mode: str = 'HTML',
                          disable_notification: bool = False):
        """Send text message to Telegram"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_notification': disable_notification
        }

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"Telegram send failed: {error_text}")
                    return False

                return True
        except Exception as e:
            print(f"Failed to send Telegram message: {e}")
            return False

    async def send_photo(self, photo_path: str, caption: Optional[str] = None):
        """Send photo to Telegram"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.base_url}/sendPhoto"

        try:
            with open(photo_path, 'rb') as photo:
                data = aiohttp.FormData()
                data.add_field('chat_id', self.chat_id)
                data.add_field('photo', photo, filename=os.path.basename(photo_path))
                if caption:
                    data.add_field('caption', caption)

                async with self.session.post(url, data=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"Telegram photo send failed: {error_text}")
                        return False

                    return True
        except Exception as e:
            print(f"Failed to send Telegram photo: {e}")
            return False

    async def send_document(self, document_path: str, caption: Optional[str] = None):
        """Send document to Telegram"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.base_url}/sendDocument"

        try:
            with open(document_path, 'rb') as doc:
                data = aiohttp.FormData()
                data.add_field('chat_id', self.chat_id)
                data.add_field('document', doc, filename=os.path.basename(document_path))
                if caption:
                    data.add_field('caption', caption)

                async with self.session.post(url, data=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"Telegram document send failed: {error_text}")
                        return False

                    return True
        except Exception as e:
            print(f"Failed to send Telegram document: {e}")
            return False

    async def send_action_alert(self, action: str, details: Dict[str, Any]):
        """Send formatted action alert"""
        message = f"🔄 <b>Action: {action}</b>\n\n"

        for key, value in details.items():
            message += f"<b>{key.replace('_', ' ').title()}:</b> {value}\n"

        await self.send_message(message)

    async def send_error_alert(self, error: str, session_id: Optional[str] = None,
                              details: Optional[Dict[str, Any]] = None):
        """Send error alert with details"""
        message = f"❌ <b>ERROR ALERT</b>\n\n"

        if session_id:
            message += f"<b>Session:</b> <code>{session_id}</code>\n"

        message += f"<b>Error:</b> {error}\n"

        if details:
            message += "\n<b>Details:</b>\n"
            for key, value in details.items():
                message += f"• {key}: {value}\n"

        await self.send_message(message, disable_notification=False)

    async def send_success_alert(self, message_text: str, order_info: Optional[Dict[str, Any]] = None):
        """Send success alert"""
        message = f"✅ <b>SUCCESS</b>\n\n{message_text}"

        if order_info:
            message += "\n\n<b>Order Details:</b>\n"
            if 'order_id' in order_info:
                message += f"Order ID: <code>{order_info['order_id']}</code>\n"
            if 'total' in order_info:
                message += f"Total: ${order_info['total']}\n"
            if 'items' in order_info:
                message += f"Items: {order_info['items']}\n"

        await self.send_message(message)

    async def send_progress_update(self, step: str, progress: int, total: int,
                                  details: Optional[str] = None):
        """Send progress update"""
        percentage = round((progress / total) * 100)
        progress_bar = self._create_progress_bar(percentage)

        message = f"📊 <b>Progress Update</b>\n\n"
        message += f"<b>Step:</b> {step}\n"
        message += f"<b>Progress:</b> {progress_bar} {percentage}%\n"
        message += f"<b>Status:</b> {progress}/{total}\n"

        if details:
            message += f"\n{details}"

        await self.send_message(message, disable_notification=True)

    def _create_progress_bar(self, percentage: int, length: int = 10) -> str:
        """Create text progress bar"""
        filled = int(length * percentage / 100)
        empty = length - filled
        return "▓" * filled + "░" * empty

    async def send_session_summary(self, session_data: Dict[str, Any]):
        """Send comprehensive session summary"""
        status_emoji = "✅" if session_data.get('status') == 'completed' else "❌"

        message = f"{status_emoji} <b>Session Summary</b>\n\n"
        message += f"<b>Session ID:</b> <code>{session_data.get('session_id', 'N/A')}</code>\n"
        message += f"<b>Status:</b> {session_data.get('status', 'Unknown')}\n"
        message += f"<b>Duration:</b> {self._format_duration(session_data)}\n"

        # Add steps summary
        steps = session_data.get('steps', [])
        if steps:
            message += "\n<b>Steps Completed:</b>\n"
            for step in steps:
                step_emoji = "✅" if step.get('status') == 'success' else "❌"
                message += f"{step_emoji} {step.get('name', 'Unknown step')}\n"

        # Add error info if failed
        if session_data.get('status') == 'failed' and 'error' in session_data:
            message += f"\n<b>Error:</b> {session_data['error']}\n"

        # Add order info if completed
        if session_data.get('status') == 'completed':
            for step in steps:
                if 'order_id' in step:
                    message += f"\n<b>Order ID:</b> <code>{step['order_id']}</code>\n"
                    break

        await self.send_message(message)

    def _format_duration(self, session_data: Dict[str, Any]) -> str:
        """Format session duration"""
        try:
            from datetime import datetime
            start = datetime.fromisoformat(session_data.get('started_at', ''))
            end = datetime.fromisoformat(session_data.get('completed_at', ''))
            duration = (end - start).total_seconds()

            minutes = int(duration // 60)
            seconds = int(duration % 60)

            return f"{minutes}m {seconds}s"
        except:
            return "N/A"

    async def send_inline_keyboard(self, text: str, buttons: List[List[Dict[str, str]]]):
        """Send message with inline keyboard buttons"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.base_url}/sendMessage"

        # Create inline keyboard markup
        keyboard = {
            'inline_keyboard': [
                [{'text': btn['text'], 'callback_data': btn.get('callback_data', btn['text'])}
                 for btn in row]
                for row in buttons
            ]
        }

        payload = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': 'HTML',
            'reply_markup': keyboard
        }

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"Telegram keyboard send failed: {error_text}")
                    return False

                return True
        except Exception as e:
            print(f"Failed to send Telegram keyboard: {e}")
            return False

    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None
