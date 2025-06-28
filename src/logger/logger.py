"""
Main Logger Module - Central logging system
"""
import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import asyncio
from .mongodb_handler import MongoDBHandler
from .websocket_handler import WebSocketHandler
from .telegram_notifier import TelegramNotifier

class Logger:
    """Central logging system with multiple outputs"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.session_id = None

        # Setup file logging
        self._setup_file_logging()

        # Setup handlers
        self.mongo_handler = None
        self.websocket_handler = None
        self.telegram_notifier = None

        if self.config.get('mongodb_enabled'):
            self.mongo_handler = MongoDBHandler(self.config.get('mongodb_uri'))

        if self.config.get('websocket_enabled'):
            self.websocket_handler = WebSocketHandler(self.config.get('websocket_url'))

        if self.config.get('telegram_enabled'):
            self.telegram_notifier = TelegramNotifier(
                self.config.get('telegram_token'),
                self.config.get('telegram_chat_id')
            )

    def _setup_file_logging(self):
        """Setup file-based logging"""
        # Create logs directory
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)

        # Setup formatters
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # File handler for all logs
        self.file_handler = logging.FileHandler(
            log_dir / f'automation_{datetime.now().strftime("%Y%m%d")}.log'
        )
        self.file_handler.setFormatter(formatter)

        # File handler for errors only
        self.error_handler = logging.FileHandler(
            log_dir / 'errors.log'
        )
        self.error_handler.setLevel(logging.ERROR)
        self.error_handler.setFormatter(formatter)

        # Console handler
        self.console_handler = logging.StreamHandler()
        self.console_handler.setFormatter(formatter)

        # Setup main logger
        self.logger = logging.getLogger('AutomationBot')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(self.file_handler)
        self.logger.addHandler(self.error_handler)
        self.logger.addHandler(self.console_handler)

    def set_session(self, session_id: str):
        """Set current session ID"""
        self.session_id = session_id

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info message"""
        log_data = self._prepare_log_data('INFO', message, extra)
        self.logger.info(message, extra=log_data)
        asyncio.create_task(self._send_to_handlers(log_data))

    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log error message"""
        log_data = self._prepare_log_data('ERROR', message, extra)
        self.logger.error(message, extra=log_data)
        asyncio.create_task(self._send_to_handlers(log_data))

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning message"""
        log_data = self._prepare_log_data('WARNING', message, extra)
        self.logger.warning(message, extra=log_data)
        asyncio.create_task(self._send_to_handlers(log_data))

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug message"""
        log_data = self._prepare_log_data('DEBUG', message, extra)
        self.logger.debug(message, extra=log_data)
        asyncio.create_task(self._send_to_handlers(log_data))

    async def log_session(self, session_id: str, session_data: Dict[str, Any]):
        """Log complete session data"""
        # Save to file
        session_file = Path('logs') / 'sessions' / f'{session_id}.json'
        session_file.parent.mkdir(exist_ok=True)

        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)

        # Send to handlers
        if self.mongo_handler:
            await self.mongo_handler.save_session(session_id, session_data)

        if self.websocket_handler:
            await self.websocket_handler.send_update({
                'type': 'session_complete',
                'session_id': session_id,
                'data': session_data
            })

        # Send summary to Telegram if enabled
        if self.telegram_notifier and session_data.get('status') in ['completed', 'failed']:
            await self._send_telegram_summary(session_data)

    async def log_action(self, action: str, details: Dict[str, Any], screenshot: Optional[str] = None):
        """Log specific action with details"""
        action_data = {
            'session_id': self.session_id,
            'action': action,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'screenshot': screenshot
        }

        # Log to file
        self.info(f"Action: {action}", extra=action_data)

        # Save to MongoDB
        if self.mongo_handler:
            await self.mongo_handler.log_action(action_data)

        # Send real-time update
        if self.websocket_handler:
            await self.websocket_handler.send_update({
                'type': 'action',
                'data': action_data
            })

    def _prepare_log_data(self, level: str, message: str, extra: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare log data with metadata"""
        log_data = {
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        }

        if extra:
            log_data.update(extra)

        return log_data

    async def _send_to_handlers(self, log_data: Dict[str, Any]):
        """Send log data to all configured handlers"""
        tasks = []

        if self.mongo_handler:
            tasks.append(self.mongo_handler.log_entry(log_data))

        if self.websocket_handler:
            tasks.append(self.websocket_handler.send_update({
                'type': 'log',
                'data': log_data
            }))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_telegram_summary(self, session_data: Dict[str, Any]):
        """Send session summary to Telegram"""
        status_emoji = "✅" if session_data['status'] == 'completed' else "❌"

        summary = f"""
{status_emoji} **Purchase Session Complete**

**Session ID:** `{session_data['session_id']}`
**Status:** {session_data['status']}
**Started:** {session_data.get('started_at', 'N/A')}
**Completed:** {session_data.get('completed_at', 'N/A')}

**Steps Completed:**
"""

        for step in session_data.get('steps', []):
            step_emoji = "✅" if step['status'] == 'success' else "❌"
            summary += f"{step_emoji} {step['name']}\n"

        if session_data['status'] == 'completed' and 'order_info' in session_data['steps'][-1]:
            order_info = session_data['steps'][-1]['order_info']
            summary += f"\n**Order ID:** `{order_info.get('order_id', 'N/A')}`"

        elif session_data['status'] == 'failed':
            summary += f"\n**Error:** {session_data.get('error', 'Unknown error')}"

        await self.telegram_notifier.send_message(summary, parse_mode='Markdown')

    async def close(self):
        """Close all handlers"""
        if self.mongo_handler:
            await self.mongo_handler.close()

        if self.websocket_handler:
            await self.websocket_handler.close()

        # Close file handlers
        self.file_handler.close()
        self.error_handler.close()
        self.console_handler.close()

    def get_session_logs(self, session_id: str) -> Dict[str, Any]:
        """Get logs for specific session"""
        session_file = Path('logs') / 'sessions' / f'{session_id}.json'

        if session_file.exists():
            with open(session_file, 'r') as f:
                return json.load(f)

        return {}

    def get_recent_errors(self, limit: int = 10) -> list:
        """Get recent error logs"""
        errors = []

        with open('logs/errors.log', 'r') as f:
            lines = f.readlines()

        # Parse last N error entries
        for line in lines[-limit:]:
            try:
                # Basic parsing - can be improved
                parts = line.strip().split(' - ')
                if len(parts) >= 4:
                    errors.append({
                        'timestamp': parts[0],
                        'level': parts[2],
                        'message': ' - '.join(parts[3:])
                    })
            except:
                continue

        return errors
