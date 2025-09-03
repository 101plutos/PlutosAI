"""Shared events for PlutosAI event-driven architecture."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4


@dataclass
class Event:
    """Base event class."""
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str
    aggregate_id: str
    aggregate_type: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.event_type:
            self.event_type = self.__class__.__name__


# Client Events
@dataclass
class ClientCreated(Event):
    aggregate_type: str = "client"
    first_name: str
    last_name: str
    client_type: str


@dataclass
class ClientStatusChanged(Event):
    aggregate_type: str = "client"
    old_status: str
    new_status: str
    changed_by: str


@dataclass
class ClientKYCStatusChanged(Event):
    aggregate_type: str = "client"
    old_status: str
    new_status: str
    changed_by: str


# Investment Events
@dataclass
class PortfolioCreated(Event):
    aggregate_type: str = "portfolio"
    client_id: str
    name: str
    created_by: str


@dataclass
class PositionAdded(Event):
    aggregate_type: str = "portfolio"
    portfolio_id: str
    security_symbol: str
    quantity: str  # Using string for decimal serialization
    price: str
    added_by: str


@dataclass
class TransactionRecorded(Event):
    aggregate_type: str = "portfolio"
    portfolio_id: str
    transaction_id: str
    security_symbol: str
    transaction_type: str
    quantity: str
    price: str
    recorded_by: str


# Compliance Events
@dataclass
class ComplianceCheckCompleted(Event):
    aggregate_type: str = "compliance_check"
    client_id: str
    check_type: str
    status: str
    score: str
    completed_at: str  # ISO format datetime


@dataclass
class ComplianceAlertTriggered(Event):
    aggregate_type: str = "compliance_alert"
    client_id: str
    alert_type: str
    severity: str
    title: str
    description: str


@dataclass
class TransactionFlagged(Event):
    aggregate_type: str = "transaction"
    client_id: str
    transaction_id: str
    risk_score: str
    flags: list[str]


# System Events
@dataclass
class ServiceHealthChanged(Event):
    aggregate_type: str = "system"
    service_name: str
    status: str  # healthy, degraded, unhealthy
    message: str


@dataclass
class AuditEvent(Event):
    aggregate_type: str = "audit"
    entity_type: str
    entity_id: str
    action: str
    user_id: str
    old_values: Dict[str, Any] = field(default_factory=dict)
    new_values: Dict[str, Any] = field(default_factory=dict)
