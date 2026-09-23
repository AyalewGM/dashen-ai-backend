"""
Real-time demo data generator for Gasha fraud monitoring
Generates realistic transaction streams for demonstration purposes
"""

import random
import time
from datetime import datetime, timezone
from typing import List
from .models import TransactionEventModel, LocationModel, DeviceModel


# Ethiopian bank account patterns
ACCOUNT_PREFIXES = ["1000", "2000", "3000", "4000", "5000"]
CUSTOMER_IDS = [f"CUST{str(i).zfill(6)}" for i in range(1, 101)]

# Transaction channels
CHANNELS = ["mobile", "web", "atm", "branch", "pos"]

# Merchant categories
MERCHANTS = [
    "Grocery Store",
    "Restaurant",
    "Gas Station",
    "Online Shopping",
    "Utility Payment",
    "Mobile Top-up",
    "ATM Withdrawal",
    "Bank Transfer",
    "Salary Payment",
    "Rent Payment",
]

# Ethiopian cities for geolocation
CITIES = [
    "Addis Ababa",
    "Dire Dawa",
    "Mekelle",
    "Gondar",
    "Hawassa",
    "Bahir Dar",
    "Jimma",
    "Adama",
    "Dessie",
    "Harar",
]

FOREIGN_CITIES = [
    ("Dubai", "AE"),
    ("London", "GB"),
    ("New York", "US"),
    ("Beijing", "CN"),
]


class DemoTransactionGenerator:
    """Generates realistic demo transactions for fraud monitoring"""

    def __init__(self):
        self.transaction_counter = 1000
        self.active_sessions = {}

    def _generate_account_id(self) -> str:
        """Generate realistic Ethiopian bank account number"""
        prefix = random.choice(ACCOUNT_PREFIXES)
        suffix = str(random.randint(100000, 999999))
        return f"{prefix}{suffix}"

    def _generate_device_id(self) -> str:
        """Generate device fingerprint"""
        return f"dev-{random.randint(10000, 99999)}"

    def _generate_ip_address(self) -> str:
        """Generate Ethiopian IP address range"""
        prefixes = ["196.188", "196.189", "213.55", "62.171"]
        prefix = random.choice(prefixes)
        return f"{prefix}.{random.randint(1, 255)}.{random.randint(1, 255)}"

    def _now_iso(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat()

    def _generate_device(self) -> DeviceModel:
        return DeviceModel(device_id=self._generate_device_id(), ip=self._generate_ip_address())

    def _generate_location(self, city: str | None = None, country: str = "ET") -> LocationModel:
        return LocationModel(city=city or random.choice(CITIES), country=country)

    def generate_normal_transaction(self) -> TransactionEventModel:
        """Generate a normal, low-risk transaction"""
        self.transaction_counter += 1

        amount = random.choice([
            random.uniform(50, 500),
            random.uniform(500, 2000),
            random.uniform(2000, 10000),
        ])

        return TransactionEventModel(
            event_id=f"txn-{self.transaction_counter}",
            event_type="transaction",
            customer_id=random.choice(CUSTOMER_IDS),
            amount=round(amount, 2),
            currency="ETB",
            channel=random.choice(["mobile", "web", "branch"]),
            timestamp=self._now_iso(),
            session_id=f"sess-{random.randint(1000, 9999)}",
            device=self._generate_device(),
            merchant=random.choice(MERCHANTS),
            location=self._generate_location(),
        )

    def generate_suspicious_transaction(self, fraud_type: str = "random") -> TransactionEventModel:
        """Generate a suspicious transaction based on fraud type"""
        base_txn = self.generate_normal_transaction()

        if fraud_type == "random":
            fraud_type = random.choice(["high_amount", "velocity", "new_device", "unusual_location"])

        if fraud_type == "high_amount":
            base_txn.amount = round(random.uniform(50000, 200000), 2)

        elif fraud_type == "velocity":
            base_txn.customer_id = "CUST000001"
            base_txn.device = DeviceModel(device_id="dev-12345", ip="196.188.10.15")
            base_txn.amount = round(random.uniform(5000, 15000), 2)

        elif fraud_type == "new_device":
            base_txn.device = DeviceModel(device_id=f"dev-NEW-{random.randint(1000, 9999)}", ip="196.189.55.12")
            base_txn.amount = round(random.uniform(20000, 80000), 2)

        elif fraud_type == "unusual_location":
            city, country = random.choice(FOREIGN_CITIES)
            base_txn.location = self._generate_location(city=city, country=country)
            base_txn.amount = round(random.uniform(10000, 50000), 2)

        return base_txn

    def generate_fraud_pattern(self, pattern_type: str = "velocity_attack") -> List[TransactionEventModel]:
        """Generate a sequence of transactions representing a fraud pattern"""
        transactions = []

        if pattern_type == "velocity_attack":
            customer_id = random.choice(CUSTOMER_IDS)
            device_id = self._generate_device_id()
            session_id = f"sess-{random.randint(1000, 9999)}"

            for i in range(random.randint(5, 7)):
                self.transaction_counter += 1
                txn = TransactionEventModel(
                    event_id=f"txn-{self.transaction_counter}",
                    event_type="transaction",
                    customer_id=customer_id,
                    amount=round(random.uniform(5000, 15000), 2),
                    currency="ETB",
                    channel="mobile",
                    timestamp=self._now_iso(),
                    session_id=session_id,
                    device=DeviceModel(device_id=device_id, ip=self._generate_ip_address()),
                    merchant=random.choice(MERCHANTS),
                    location=self._generate_location(),
                )
                transactions.append(txn)
                time.sleep(0.1)

        elif pattern_type == "structuring":
            customer_id = random.choice(CUSTOMER_IDS)

            for i in range(random.randint(3, 5)):
                self.transaction_counter += 1
                amount = random.uniform(180000, 199000)
                txn = TransactionEventModel(
                    event_id=f"txn-{self.transaction_counter}",
                    event_type="transaction",
                    customer_id=customer_id,
                    amount=round(amount, 2),
                    currency="ETB",
                    channel=random.choice(["branch", "atm"]),
                    timestamp=self._now_iso(),
                    session_id=f"sess-{random.randint(1000, 9999)}",
                    device=self._generate_device(),
                    merchant="Cash Withdrawal",
                    location=self._generate_location(),
                )
                transactions.append(txn)
                time.sleep(0.2)

        return transactions

    def generate_transaction_stream(self, count: int = 10, fraud_probability: float = 0.15) -> List[TransactionEventModel]:
        """
        Generate a stream of transactions with some fraud mixed in.
        Injects full fraud-pattern sequences so pattern detection has data to find.
        """
        transactions: List[TransactionEventModel] = []
        pattern_injected = False

        while len(transactions) < count:
            if not pattern_injected and random.random() < 0.6:
                pattern_type = random.choice(["velocity_attack", "structuring"])
                pattern_txns = self.generate_fraud_pattern(pattern_type)
                transactions.extend(pattern_txns[: max(0, count - len(transactions))])
                pattern_injected = True
                continue

            if random.random() < fraud_probability:
                transactions.append(self.generate_suspicious_transaction())
            else:
                transactions.append(self.generate_normal_transaction())

            time.sleep(0.05)

        return transactions[:count]

    def generate_live_metrics(self) -> dict:
        """Generate realistic live monitoring metrics"""
        total_transactions = random.randint(1500, 2000)
        high_risk = random.randint(15, 25)
        medium_risk = random.randint(80, 120)
        low_risk = total_transactions - high_risk - medium_risk

        return {
            "totalTransactions": total_transactions,
            "totalAlerts": high_risk + medium_risk,
            "highRisk": high_risk,
            "mediumRisk": medium_risk,
            "lowRisk": low_risk,
            "fraudPrevented": round(random.uniform(2500000, 4000000), 2),
            "accuracy": round(random.uniform(96.5, 98.5), 1),
            "detectionRate": round(random.uniform(98.0, 99.5), 1),
            "falsePositiveRate": round(random.uniform(0.5, 1.2), 2),
            "transactionsMonitored": f"{random.uniform(12.0, 13.5):.1f}M",
        }


# Global instance for reuse
_generator = DemoTransactionGenerator()


def get_demo_generator() -> DemoTransactionGenerator:
    """Get the global demo generator instance"""
    return _generator
