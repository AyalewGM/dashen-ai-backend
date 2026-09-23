"""
Advanced Fraud Pattern Detection
Detects sophisticated fraud patterns for demo purposes
"""

from typing import List, Dict
from datetime import datetime
from collections import defaultdict
from .models import TransactionEventModel


def _device_id(txn: TransactionEventModel) -> str | None:
    return txn.device.device_id if txn.device else None


def _location_str(txn: TransactionEventModel) -> str | None:
    if not txn.location:
        return None
    if txn.location.city and txn.location.country:
        return f"{txn.location.city}, {txn.location.country}"
    return txn.location.city or txn.location.country or None


class FraudPattern:
    """Represents a detected fraud pattern"""

    def __init__(
        self,
        pattern_type: str,
        severity: str,
        confidence: float,
        transactions: List[TransactionEventModel],
        description: str,
        indicators: List[str],
        recommendation: str,
    ):
        self.pattern_type = pattern_type
        self.severity = severity
        self.confidence = confidence
        self.transactions = transactions
        self.description = description
        self.indicators = indicators
        self.recommendation = recommendation
        self.detected_at = datetime.utcnow().isoformat()


class PatternDetector:
    """Detects advanced fraud patterns in transaction streams"""

    # NBE threshold for CTR reporting
    NBE_REPORTING_THRESHOLD = 200000  # ETB

    def __init__(self):
        self.transaction_history: Dict[str, List[TransactionEventModel]] = defaultdict(list)
        self.device_history: Dict[str, List[TransactionEventModel]] = defaultdict(list)

    def detect_patterns(
        self,
        transactions: List[TransactionEventModel],
        lookback_hours: int = 24,
    ) -> List[FraudPattern]:
        """
        Detect fraud patterns in transaction stream

        Args:
            transactions: List of transactions to analyze
            lookback_hours: How far back to look for patterns

        Returns:
            List of detected fraud patterns
        """
        patterns = []

        # Update history
        for txn in transactions:
            if txn.customer_id:
                self.transaction_history[txn.customer_id].append(txn)
            dev_id = _device_id(txn)
            if dev_id:
                self.device_history[dev_id].append(txn)

        # Run pattern detection algorithms
        patterns.extend(self._detect_structuring(transactions))
        patterns.extend(self._detect_velocity_attack(transactions))
        patterns.extend(self._detect_account_takeover(transactions))
        patterns.extend(self._detect_smurfing(transactions))
        patterns.extend(self._detect_unusual_time_pattern(transactions))

        return patterns

    def _detect_structuring(self, transactions: List[TransactionEventModel]) -> List[FraudPattern]:
        """
        Detect structuring: Multiple transactions just below NBE reporting threshold
        Classic money laundering technique
        """
        patterns = []

        customer_txns = defaultdict(list)
        for txn in transactions:
            if txn.customer_id and txn.amount:
                customer_txns[txn.customer_id].append(txn)

        for customer_id, txns in customer_txns.items():
            suspicious_txns = [
                t for t in txns
                if 150000 <= t.amount < self.NBE_REPORTING_THRESHOLD
            ]

            if len(suspicious_txns) >= 3:
                total_amount = sum(t.amount for t in suspicious_txns)

                patterns.append(FraudPattern(
                    pattern_type="structuring",
                    severity="high",
                    confidence=0.85,
                    transactions=suspicious_txns,
                    description=f"Structuring detected: {len(suspicious_txns)} transactions totaling ETB {total_amount:,.2f}, each just below NBE reporting threshold",
                    indicators=[
                        f"{len(suspicious_txns)} transactions in 24 hours",
                        "All amounts between 150K-199K ETB",
                        f"Total: ETB {total_amount:,.2f}",
                        "Possible CTR avoidance",
                    ],
                    recommendation="Generate STR (Suspicious Transaction Report) to NBE immediately. Freeze account pending investigation.",
                ))

        return patterns

    def _detect_velocity_attack(self, transactions: List[TransactionEventModel]) -> List[FraudPattern]:
        """
        Detect velocity attacks: Rapid-fire transactions from same customer/device
        """
        patterns = []

        customer_txns = defaultdict(list)
        for txn in transactions:
            if txn.customer_id:
                customer_txns[txn.customer_id].append(txn)

        for customer_id, txns in customer_txns.items():
            sorted_txns = sorted(txns, key=lambda t: t.timestamp or "")

            if len(sorted_txns) >= 5:
                try:
                    first_time = datetime.fromisoformat(sorted_txns[0].timestamp.replace('Z', '+00:00'))
                    last_time = datetime.fromisoformat(sorted_txns[-1].timestamp.replace('Z', '+00:00'))
                    time_diff = (last_time - first_time).total_seconds() / 60  # minutes

                    if time_diff <= 5:
                        total_amount = sum(t.amount for t in sorted_txns)

                        patterns.append(FraudPattern(
                            pattern_type="velocity_attack",
                            severity="high",
                            confidence=0.92,
                            transactions=sorted_txns,
                            description=f"Velocity attack: {len(sorted_txns)} transactions in {time_diff:.1f} minutes",
                            indicators=[
                                f"{len(sorted_txns)} rapid transactions",
                                f"Time window: {time_diff:.1f} minutes",
                                f"Total amount: ETB {total_amount:,.2f}",
                                "Possible card testing or account compromise",
                            ],
                            recommendation="Block account immediately. Contact customer for verification. Review all recent transactions.",
                        ))
                except (ValueError, AttributeError):
                    pass

        return patterns

    def _detect_account_takeover(self, transactions: List[TransactionEventModel]) -> List[FraudPattern]:
        """
        Detect account takeover: New device + high amount + unusual location
        """
        patterns = []

        for txn in transactions:
            if not txn.customer_id or not txn.amount:
                continue

            history = self.transaction_history.get(txn.customer_id, [])

            if len(history) < 2:
                continue

            # Check for new device
            historical_devices = {_device_id(t) for t in history[:-1] if _device_id(t)}
            txn_device_id = _device_id(txn)
            is_new_device = txn_device_id and txn_device_id not in historical_devices

            # Check for high amount (> 50K ETB)
            is_high_amount = txn.amount > 50000

            # Check for unusual location
            historical_locations = {(t.location.city, t.location.country) for t in history[:-1] if t.location}
            is_new_location = txn.location and (txn.location.city, txn.location.country) not in historical_locations

            # Check for unusual time (late night 11pm-5am)
            try:
                txn_time = datetime.fromisoformat(txn.timestamp.replace('Z', '+00:00'))
                is_unusual_time = txn_time.hour >= 23 or txn_time.hour <= 5
            except (ValueError, AttributeError):
                is_unusual_time = False

            red_flags = sum([is_new_device, is_high_amount, is_new_location, is_unusual_time])

            if red_flags >= 2:
                indicators = []
                if is_new_device:
                    indicators.append(f"New device: {txn_device_id}")
                if is_high_amount:
                    indicators.append(f"High amount: ETB {txn.amount:,.2f}")
                if is_new_location:
                    indicators.append(f"New location: {_location_str(txn)}")
                if is_unusual_time:
                    indicators.append(f"Unusual time: {txn_time.strftime('%I:%M %p')}")

                patterns.append(FraudPattern(
                    pattern_type="account_takeover",
                    severity="high",
                    confidence=0.78,
                    transactions=[txn],
                    description=f"Possible account takeover: {red_flags} suspicious indicators",
                    indicators=indicators,
                    recommendation="Block transaction. Send OTP verification to registered phone. Contact customer immediately.",
                ))

        return patterns

    def _detect_smurfing(self, transactions: List[TransactionEventModel]) -> List[FraudPattern]:
        """
        Detect smurfing: Multiple accounts making similar transactions to same merchant
        """
        patterns = []

        merchant_patterns = defaultdict(list)
        for txn in transactions:
            if txn.merchant and txn.amount:
                amount_bucket = round(txn.amount / 1000) * 1000
                key = (txn.merchant, amount_bucket)
                merchant_patterns[key].append(txn)

        for (merchant, amount_bucket), txns in merchant_patterns.items():
            unique_customers = {t.customer_id for t in txns if t.customer_id}

            if len(unique_customers) >= 4:
                total_amount = sum(t.amount for t in txns)

                patterns.append(FraudPattern(
                    pattern_type="smurfing",
                    severity="medium",
                    confidence=0.68,
                    transactions=txns,
                    description=f"Smurfing detected: {len(unique_customers)} accounts sending ~ETB {amount_bucket:,.0f} to {merchant}",
                    indicators=[
                        f"{len(unique_customers)} different accounts",
                        f"Similar amounts (~ETB {amount_bucket:,.0f})",
                        f"Same merchant: {merchant}",
                        f"Total: ETB {total_amount:,.2f}",
                    ],
                    recommendation="Investigate merchant relationship. Check for coordinated fraud ring. Review all involved accounts.",
                ))

        return patterns

    def _detect_unusual_time_pattern(self, transactions: List[TransactionEventModel]) -> List[FraudPattern]:
        """
        Detect unusual time patterns: Transactions at odd hours
        """
        patterns = []

        customer_txns = defaultdict(list)
        for txn in transactions:
            if txn.customer_id and txn.timestamp:
                try:
                    txn_time = datetime.fromisoformat(txn.timestamp.replace('Z', '+00:00'))
                    if txn_time.hour >= 23 or txn_time.hour <= 5:
                        customer_txns[txn.customer_id].append(txn)
                except (ValueError, AttributeError):
                    pass

        for customer_id, txns in customer_txns.items():
            if len(txns) >= 3:
                total_amount = sum(t.amount for t in txns)

                patterns.append(FraudPattern(
                    pattern_type="unusual_time",
                    severity="medium",
                    confidence=0.62,
                    transactions=txns,
                    description=f"Unusual time pattern: {len(txns)} transactions during late night hours",
                    indicators=[
                        f"{len(txns)} transactions between 11pm-5am",
                        f"Total: ETB {total_amount:,.2f}",
                        "Deviates from normal customer behavior",
                    ],
                    recommendation="Monitor account closely. May indicate account compromise or insider fraud.",
                ))

        return patterns


# Global instance
_detector = PatternDetector()


def get_pattern_detector() -> PatternDetector:
    """Get the global pattern detector instance"""
    return _detector
