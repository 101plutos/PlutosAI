"""Compliance domain models for PlutosAI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict
from uuid import uuid4


class ComplianceCheckType(Enum):
    KYC = "kyc"
    AML = "aml"
    SANCTIONS = "sanctions"
    PEPS = "peps"  # Politically Exposed Persons
    ADVERSE_MEDIA = "adverse_media"
    CREDIT_CHECK = "credit_check"
    BACKGROUND_CHECK = "background_check"


class ComplianceStatus(Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REQUIRES_UPDATE = "requires_update"


class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


@dataclass
class ComplianceCheck:
    """Entity representing a compliance check."""
    id: str = field(default_factory=lambda: str(uuid4()))
    client_id: str
    check_type: ComplianceCheckType
    status: ComplianceStatus = ComplianceStatus.PENDING

    # Check details
    provider: str  # Third-party provider (e.g., LexisNexis, Dow Jones)
    reference_number: Optional[str] = None
    requested_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # Results
    score: Optional[Decimal] = None  # Risk score 0-100
    result_data: Dict[str, str] = field(default_factory=dict)
    findings: List[str] = field(default_factory=list)

    # Review
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None

    def complete(self, score: Decimal, findings: List[str], result_data: Dict[str, str], completed_by: str):
        """Mark check as completed."""
        self.status = ComplianceStatus.APPROVED if score <= Decimal('50') else ComplianceStatus.REJECTED
        self.score = score
        self.findings = findings
        self.result_data = result_data
        self.completed_at = datetime.utcnow()

        if self.status == ComplianceStatus.REJECTED:
            # Auto-generate alert for high-risk findings
            alert = ComplianceAlert(
                client_id=self.client_id,
                alert_type="compliance_check_failed",
                severity=AlertSeverity.HIGH,
                title=f"Compliance check failed: {self.check_type.value}",
                description=f"Risk score: {score}. Findings: {', '.join(findings[:3])}",
                triggered_by=f"compliance_check_{self.id}"
            )

    def review(self, status: ComplianceStatus, notes: str, reviewed_by: str):
        """Review and update check status."""
        self.status = status
        self.review_notes = notes
        self.reviewed_by = reviewed_by
        self.reviewed_at = datetime.utcnow()


@dataclass
class ComplianceAlert:
    """Entity representing a compliance alert."""
    id: str = field(default_factory=lambda: str(uuid4()))
    client_id: str
    alert_type: str  # e.g., "sanctions_hit", "large_transaction", "unusual_activity"
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.ACTIVE

    title: str
    description: str
    triggered_by: str  # Reference to triggering entity

    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

    # Additional context
    metadata: Dict[str, str] = field(default_factory=dict)

    def acknowledge(self, acknowledged_by: str):
        """Acknowledge the alert."""
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.utcnow()
        self.acknowledged_by = acknowledged_by

    def resolve(self, resolved_by: str):
        """Resolve the alert."""
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.utcnow()
        self.resolved_by = resolved_by


@dataclass
class TransactionMonitoring:
    """Entity for transaction monitoring."""
    id: str = field(default_factory=lambda: str(uuid4()))
    client_id: str
    transaction_id: str
    portfolio_id: str

    # Transaction details
    amount: Decimal
    currency: str
    transaction_type: str
    counterparty: Optional[str] = None

    # Monitoring results
    risk_score: Optional[Decimal] = None
    flags: List[str] = field(default_factory=list)  # e.g., ["unusual_amount", "new_counterparty"]
    reviewed: bool = False

    created_at: datetime = field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None

    def flag_transaction(self, flags: List[str], risk_score: Decimal):
        """Flag transaction for review."""
        self.flags = flags
        self.risk_score = risk_score

        if risk_score > Decimal('70'):
            # Auto-generate high-risk alert
            alert = ComplianceAlert(
                client_id=self.client_id,
                alert_type="high_risk_transaction",
                severity=AlertSeverity.HIGH,
                title=f"High-risk transaction flagged: {self.transaction_id}",
                description=f"Risk score: {risk_score}. Flags: {', '.join(flags)}",
                triggered_by=f"transaction_monitoring_{self.id}"
            )

    def review(self, reviewed_by: str):
        """Mark as reviewed."""
        self.reviewed = True
        self.reviewed_at = datetime.utcnow()
        self.reviewed_by = reviewed_by


@dataclass
class AuditLog:
    """Entity for audit logging."""
    id: str = field(default_factory=lambda: str(uuid4()))
    entity_type: str  # e.g., "client", "portfolio", "transaction"
    entity_id: str
    action: str  # e.g., "created", "updated", "deleted"
    user_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Change details
    old_values: Dict[str, str] = field(default_factory=dict)
    new_values: Dict[str, str] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Additional context
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class ComplianceReport:
    """Read model for compliance reporting."""
    client_id: str
    report_type: str  # e.g., "kyc_status", "transaction_summary", "alert_summary"
    period_start: date
    period_end: date

    # Report data
    data: Dict[str, str] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.utcnow)
    generated_by: str

    # Status
    status: str = "generated"  # generated, reviewed, approved


# Domain Events
@dataclass
class ComplianceCheckCompleted:
    check_id: str
    client_id: str
    check_type: ComplianceCheckType
    status: ComplianceStatus
    score: Optional[Decimal]
    completed_at: datetime


@dataclass
class ComplianceAlertCreated:
    alert_id: str
    client_id: str
    alert_type: str
    severity: AlertSeverity
    title: str
    created_at: datetime


@dataclass
class TransactionFlagged:
    monitoring_id: str
    client_id: str
    transaction_id: str
    risk_score: Decimal
    flags: List[str]
    flagged_at: datetime


@dataclass
class AuditEventLogged:
    audit_id: str
    entity_type: str
    entity_id: str
    action: str
    user_id: str
    timestamp: datetime
