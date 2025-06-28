"""
Payment Autofill Manager
"""
import json
import os
from typing import Dict, Any, List
from pathlib import Path
import random

class PaymentAutofill:
    """Manage payment autofill profiles"""

    def __init__(self, profiles_path: str = "payment_profiles.json"):
        self.profiles_path = profiles_path
        self.profiles = self._load_profiles()

    def _load_profiles(self) -> Dict[str, Any]:
        """Load payment profiles from file"""
        if os.path.exists(self.profiles_path):
            with open(self.profiles_path, 'r') as f:
                return json.load(f)
        return {}

    def save_profiles(self):
        """Save profiles to file"""
        with open(self.profiles_path, 'w') as f:
            json.dump(self.profiles, f, indent=2)

    def add_profile(self, name: str, payment_data: Dict[str, Any]):
        """Add new payment profile"""
        self.profiles[name] = {
            'payment_info': payment_data.get('payment_info', {}),
            'billing': payment_data.get('billing', {}),
            'created_at': payment_data.get('created_at', ''),
            'last_used': None
        }
        self.save_profiles()

    def get_profile(self, name: str) -> Dict[str, Any]:
        """Get payment profile by name"""
        return self.profiles.get(name, {})

    def get_random_profile(self) -> Dict[str, Any]:
        """Get random payment profile"""
        if self.profiles:
            name = random.choice(list(self.profiles.keys()))
            return self.profiles[name]
        return {}

    def update_last_used(self, name: str, timestamp: str):
        """Update last used timestamp"""
        if name in self.profiles:
            self.profiles[name]['last_used'] = timestamp
            self.save_profiles()

    def get_sample_profiles(self) -> Dict[str, Any]:
        """Get sample payment profiles for testing"""
        return {
            "test_profile_1": {
                "payment_info": {
                    "card_number": "4111111111111111",
                    "expiry": "12/25",
                    "cvv": "123",
                    "cardholder_name": "John Doe"
                },
                "billing": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com",
                    "phone": "+1234567890",
                    "address": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "zip": "10001",
                    "country": "US"
                }
            },
            "test_profile_2": {
                "payment_info": {
                    "card_number": "5555555555554444",
                    "expiry": "03/26",
                    "cvv": "456",
                    "cardholder_name": "Jane Smith"
                },
                "billing": {
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "email": "jane.smith@example.com",
                    "phone": "+1987654321",
                    "address": "456 Oak Ave",
                    "address2": "Apt 2B",
                    "city": "Los Angeles",
                    "state": "CA",
                    "zip": "90001",
                    "country": "US"
                }
            }
        }

    def generate_test_card(self, card_type: str = "visa") -> Dict[str, str]:
        """Generate test credit card numbers"""
        test_cards = {
            "visa": {
                "numbers": ["4111111111111111", "4012888888881881", "4222222222222"],
                "cvv_length": 3
            },
            "mastercard": {
                "numbers": ["5555555555554444", "5105105105105100", "2223003122003222"],
                "cvv_length": 3
            },
            "amex": {
                "numbers": ["378282246310005", "371449635398431", "378734493671000"],
                "cvv_length": 4
            },
            "discover": {
                "numbers": ["6011111111111117", "6011000990139424", "6011601160116611"],
                "cvv_length": 3
            }
        }

        card_info = test_cards.get(card_type, test_cards["visa"])
        card_number = random.choice(card_info["numbers"])

        # Generate random expiry (future date)
        import datetime
        now = datetime.datetime.now()
        future_year = now.year + random.randint(1, 5)
        month = random.randint(1, 12)

        return {
            "card_number": card_number,
            "expiry": f"{month:02d}/{str(future_year)[-2:]}",
            "cvv": ''.join([str(random.randint(0, 9)) for _ in range(card_info["cvv_length"])]),
            "type": card_type
        }

    def generate_billing_address(self, country: str = "US") -> Dict[str, str]:
        """Generate random billing address"""
        us_addresses = [
            {
                "address": "123 Main Street",
                "city": "New York",
                "state": "NY",
                "zip": "10001"
            },
            {
                "address": "456 Oak Avenue",
                "city": "Los Angeles",
                "state": "CA",
                "zip": "90001"
            },
            {
                "address": "789 Pine Road",
                "city": "Chicago",
                "state": "IL",
                "zip": "60601"
            },
            {
                "address": "321 Elm Street",
                "city": "Houston",
                "state": "TX",
                "zip": "77001"
            },
            {
                "address": "654 Maple Drive",
                "city": "Phoenix",
                "state": "AZ",
                "zip": "85001"
            }
        ]

        first_names = ["John", "Jane", "Robert", "Emily", "Michael", "Sarah", "David", "Lisa"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]

        address = random.choice(us_addresses)
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)

        return {
            "first_name": first_name,
            "last_name": last_name,
            "email": f"{first_name.lower()}.{last_name.lower()}@example.com",
            "phone": f"+1{random.randint(2000000000, 9999999999)}",
            "address": address["address"],
            "city": address["city"],
            "state": address["state"],
            "zip": address["zip"],
            "country": country
        }

    def mask_card_number(self, card_number: str) -> str:
        """Mask credit card number for display"""
        cleaned = card_number.replace(' ', '').replace('-', '')
        if len(cleaned) >= 8:
            return f"****{cleaned[-4:]}"
        return "****"
