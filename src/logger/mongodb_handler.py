"""
MongoDB Handler for Persistent Logging
"""
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import os

class MongoDBHandler:
    """Handle MongoDB operations for logging"""

    def __init__(self, mongodb_uri: Optional[str] = None):
        self.mongodb_uri = mongodb_uri or os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
        self.client = None
        self.db = None
        self.sessions_collection = None
        self.actions_collection = None
        self.logs_collection = None

    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.mongodb_uri)
            self.db = self.client['automation_logs']

            # Setup collections
            self.sessions_collection = self.db['sessions']
            self.actions_collection = self.db['actions']
            self.logs_collection = self.db['logs']

            # Create indexes
            await self._create_indexes()

            # Test connection
            await self.client.server_info()
            print("MongoDB connected successfully")

        except Exception as e:
            print(f"MongoDB connection failed: {e}")
            # Fallback to in-memory storage
            self.client = None

    async def _create_indexes(self):
        """Create database indexes for better performance"""
        # Sessions indexes
        await self.sessions_collection.create_index('session_id', unique=True)
        await self.sessions_collection.create_index('status')
        await self.sessions_collection.create_index('created_at')

        # Actions indexes
        await self.actions_collection.create_index('session_id')
        await self.actions_collection.create_index('action')
        await self.actions_collection.create_index('timestamp')

        # Logs indexes
        await self.logs_collection.create_index('session_id')
        await self.logs_collection.create_index('level')
        await self.logs_collection.create_index('timestamp')

    async def save_session(self, session_id: str, session_data: Dict[str, Any]):
        """Save complete session data"""
        if not self.client:
            return

        document = {
            '_id': session_id,
            'session_id': session_id,
            'data': session_data,
            'created_at': datetime.now(),
            'status': session_data.get('status', 'unknown')
        }

        try:
            await self.sessions_collection.replace_one(
                {'_id': session_id},
                document,
                upsert=True
            )
        except Exception as e:
            print(f"Failed to save session to MongoDB: {e}")

    async def log_action(self, action_data: Dict[str, Any]):
        """Log individual action"""
        if not self.client:
            return

        document = {
            'session_id': action_data.get('session_id'),
            'action': action_data.get('action'),
            'details': action_data.get('details', {}),
            'timestamp': datetime.fromisoformat(action_data.get('timestamp', datetime.now().isoformat())),
            'screenshot': action_data.get('screenshot')
        }

        try:
            await self.actions_collection.insert_one(document)
        except Exception as e:
            print(f"Failed to log action to MongoDB: {e}")

    async def log_entry(self, log_data: Dict[str, Any]):
        """Log general entry"""
        if not self.client:
            return

        document = {
            'session_id': log_data.get('session_id'),
            'level': log_data.get('level'),
            'message': log_data.get('message'),
            'timestamp': datetime.fromisoformat(log_data.get('timestamp', datetime.now().isoformat())),
            'extra': {k: v for k, v in log_data.items() if k not in ['session_id', 'level', 'message', 'timestamp']}
        }

        try:
            await self.logs_collection.insert_one(document)
        except Exception as e:
            print(f"Failed to log entry to MongoDB: {e}")

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by ID"""
        if not self.client:
            return None

        try:
            session = await self.sessions_collection.find_one({'_id': session_id})
            if session:
                return session['data']
        except Exception as e:
            print(f"Failed to get session from MongoDB: {e}")

        return None

    async def get_session_actions(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all actions for a session"""
        if not self.client:
            return []

        try:
            cursor = self.actions_collection.find(
                {'session_id': session_id}
            ).sort('timestamp', 1)

            actions = []
            async for action in cursor:
                action.pop('_id', None)  # Remove MongoDB ID
                actions.append(action)

            return actions
        except Exception as e:
            print(f"Failed to get actions from MongoDB: {e}")

        return []

    async def get_session_logs(self, session_id: str, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get logs for a session"""
        if not self.client:
            return []

        query = {'session_id': session_id}
        if level:
            query['level'] = level

        try:
            cursor = self.logs_collection.find(query).sort('timestamp', 1)

            logs = []
            async for log in cursor:
                log.pop('_id', None)
                logs.append(log)

            return logs
        except Exception as e:
            print(f"Failed to get logs from MongoDB: {e}")

        return []

    async def get_recent_sessions(self, limit: int = 10, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent sessions"""
        if not self.client:
            return []

        query = {}
        if status:
            query['status'] = status

        try:
            cursor = self.sessions_collection.find(query).sort('created_at', -1).limit(limit)

            sessions = []
            async for session in cursor:
                sessions.append({
                    'session_id': session['session_id'],
                    'status': session['status'],
                    'created_at': session['created_at'],
                    'summary': self._get_session_summary(session['data'])
                })

            return sessions
        except Exception as e:
            print(f"Failed to get recent sessions from MongoDB: {e}")

        return []

    def _get_session_summary(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract summary from session data"""
        steps = session_data.get('steps', [])

        summary = {
            'total_steps': len(steps),
            'completed_steps': len([s for s in steps if s.get('status') == 'success']),
            'duration': None
        }

        # Calculate duration
        if 'started_at' in session_data and 'completed_at' in session_data:
            try:
                start = datetime.fromisoformat(session_data['started_at'])
                end = datetime.fromisoformat(session_data['completed_at'])
                summary['duration'] = (end - start).total_seconds()
            except:
                pass

        # Get order info if available
        for step in steps:
            if 'order_id' in step:
                summary['order_id'] = step['order_id']
                break

        return summary

    async def search_sessions(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search sessions with custom query"""
        if not self.client:
            return []

        try:
            cursor = self.sessions_collection.find(query).sort('created_at', -1)

            sessions = []
            async for session in cursor:
                sessions.append(session['data'])

            return sessions
        except Exception as e:
            print(f"Failed to search sessions in MongoDB: {e}")

        return []

    async def delete_old_sessions(self, days: int = 30):
        """Delete sessions older than specified days"""
        if not self.client:
            return

        cutoff_date = datetime.now() - timedelta(days=days)

        try:
            # Delete old sessions
            result = await self.sessions_collection.delete_many({
                'created_at': {'$lt': cutoff_date}
            })

            print(f"Deleted {result.deleted_count} old sessions")

            # Also delete associated actions and logs
            await self.actions_collection.delete_many({
                'timestamp': {'$lt': cutoff_date}
            })

            await self.logs_collection.delete_many({
                'timestamp': {'$lt': cutoff_date}
            })

        except Exception as e:
            print(f"Failed to delete old sessions: {e}")

    async def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics"""
        if not self.client:
            return {}

        try:
            # Count sessions by status
            pipeline = [
                {
                    '$group': {
                        '_id': '$status',
                        'count': {'$sum': 1}
                    }
                }
            ]

            status_counts = {}
            async for item in self.sessions_collection.aggregate(pipeline):
                status_counts[item['_id']] = item['count']

            # Get total counts
            total_sessions = await self.sessions_collection.count_documents({})
            total_actions = await self.actions_collection.count_documents({})
            total_logs = await self.logs_collection.count_documents({})

            return {
                'total_sessions': total_sessions,
                'total_actions': total_actions,
                'total_logs': total_logs,
                'sessions_by_status': status_counts
            }

        except Exception as e:
            print(f"Failed to get statistics: {e}")

        return {}

    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("MongoDB connection closed")
