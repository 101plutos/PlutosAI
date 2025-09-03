"""Client domain models for PlutosAI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import uuid4


class ClientType(Enum):
    INDIVIDUAL = "individual"
    TRUST = "trust"
    CORPORATION = "corporation"
    PARTNERSHIP = "partnership"
    FOUNDATION = "foundation"


class ClientStatus(Enum):
    PROSPECT = "prospect"
    ONBOARDING = "onboarding"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class RiskProfile(Enum):
    CONSERVATIVE = "conservative"
    MODERATE_CONSERVATIVE = "moderate_conservative"
    MODERATE = "moderate"
    MODERATE_AGGRESSIVE = "moderate_aggressive"
    AGGRESSIVE = "aggressive"


class KYCStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_UPDATE = "requires_update"


@dataclass
class Address:
    """Value object for address information."""
    street1: str
    street2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str = "US"

    def __post_init__(self):
        self.street1 = self.street1.strip()
        self.city = self.city.strip()
        self.state = self.state.strip()
        self.postal_code = self.postal_code.strip()


@dataclass
class Identification:
    """Value object for identification documents."""
    type: str  # passport, drivers_license, ssn, etc.
    number: str
    issuing_country: str
    expiry_date: Optional[date] = None
    issuing_date: Optional[date] = None
    verified: bool = False
    verification_date: Optional[datetime] = None

    def __post_init__(self):
        self.number = self.number.strip().upper()


@dataclass
class BankAccount:
    """Value object for bank account information."""
    account_number: str
    routing_number: str
    bank_name: str
    account_type: str  # checking, savings
    currency: str = "USD"
    verified: bool = False


@dataclass
class Contact:
    """Value object for contact information."""
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None

    def __post_init__(self):
        if self.email:
            self.email = self.email.strip().lower()


@dataclass
class Client:
    """Aggregate root for client domain."""
    id: str = field(default_factory=lambda: str(uuid4()))
    type: ClientType = ClientType.INDIVIDUAL
    status: ClientStatus = ClientStatus.PROSPECT

    # Basic Information
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = None
    tax_id: Optional[str] = None

    # Contact Information
    address: Optional[Address] = None
    mailing_address: Optional[Address] = None
    contact: Contact = field(default_factory=Contact)

    # Compliance
    kyc_status: KYCStatus = KYCStatus.NOT_STARTED
    risk_profile: Optional[RiskProfile] = None
    identifications: List[Identification] = field(default_factory=list)

    # Financial Information
    net_worth: Optional[Decimal] = None
    annual_income: Optional[Decimal] = None
    investment_objectives: List[str] = field(default_factory=list)
    bank_accounts: List[BankAccount] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    # Domain events
    events: List[object] = field(default_factory=list, init=False)

    def __post_init__(self):
        if self.first_name:
            self.first_name = self.first_name.strip()
        if self.last_name:
            self.last_name = self.last_name.strip()
        if self.tax_id:
            self.tax_id = self.tax_id.strip()

    def update_status(self, new_status: ClientStatus, updated_by: str):
        """Update client status and record event."""
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by

        event = ClientStatusChanged(
            client_id=self.id,
            old_status=old_status,
            new_status=new_status,
            changed_at=self.updated_at,
            changed_by=updated_by
        )
        self.events.append(event)

    def update_kyc_status(self, new_status: KYCStatus, updated_by: str):
        """Update KYC status and record event."""
        old_status = self.kyc_status
        self.kyc_status = new_status
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by

        event = ClientKYCStatusChanged(
            client_id=self.id,
            old_status=old_status,
            new_status=new_status,
            changed_at=self.updated_at,
            changed_by=updated_by
        )
        self.events.append(event)

    def add_identification(self, identification: Identification, added_by: str):
        """Add identification document."""
        self.identifications.append(identification)
        self.updated_at = datetime.utcnow()
        self.updated_by = added_by

        event = ClientIdentificationAdded(
            client_id=self.id,
            identification_type=identification.type,
            added_at=self.updated_at,
            added_by=added_by
        )
        self.events.append(event)

    def update_risk_profile(self, risk_profile: RiskProfile, updated_by: str):
        """Update risk profile."""
        old_profile = self.risk_profile
        self.risk_profile = risk_profile
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by

        event = ClientRiskProfileChanged(
            client_id=self.id,
            old_profile=old_profile,
            new_profile=risk_profile,
            changed_at=self.updated_at,
            changed_by=updated_by
        )
        self.events.append(event)


# Domain Events
@dataclass
class ClientStatusChanged:
    client_id: str
    old_status: ClientStatus
    new_status: ClientStatus
    changed_at: datetime
    changed_by: str


@dataclass
class ClientKYCStatusChanged:
    client_id: str
    old_status: KYCStatus
    new_status: KYCStatus
    changed_at: datetime
    changed_by: str


@dataclass
class ClientIdentificationAdded:
    client_id: str
    identification_type: str
    added_at: datetime
    added_by: str


@dataclass
class ClientRiskProfileChanged:
    client_id: str
    old_profile: Optional[RiskProfile]
    new_profile: RiskProfile
    changed_at: datetime
    changed_by: str


@dataclass
class ClientCreated:
    client_id: str
    client_type: ClientType
    created_at: datetime
    created_by: str
