"""
Factory functions for creating test data.

These factories create database entities following the Arrange-Act-Assert pattern.
Each factory creates a single entity and returns it for use in tests.
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional
from uuid import uuid4

from app.enums import (
    AcquisitionReason,
    ActivationStatus,
    AddressType,
    AskStatus,
    BidStatus,
    ExecutionMode,
    InstrumentStatus,
    ListingStatus,
    MaturityStatus,
    TradingStatus,
    UserRole,
)
from app.models.ask import Ask
from app.models.bid import Bid
from app.models.company import Company
from app.models.company_address import CompanyAddress
from app.models.documents.document import Document
from app.models.documents.instrument_document import InstrumentDocument
from app.models.instrument import Instrument
from app.models.instrument_ownership import InstrumentOwnership
from app.models.instrument_public_payload import InstrumentPublicPayload
from app.models.listing import Listing
from app.models.user import User
from app.security import encrypt_password
from sqlalchemy.ext.asyncio import AsyncSession


class CompanyFactory:
    """Factory for creating Company entities in the test database."""

    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        legal_name: Optional[str] = None,
        trade_name: Optional[str] = None,
        registration_number: Optional[str] = None,
        incorporation_date: Optional[date] = None,
    ) -> Company:
        """
        Create a Company entity in the database.

        Args:
            session: The async database session.
            legal_name: Company legal name (auto-generated if not provided).
            trade_name: Company trade name (optional).
            registration_number: Company registration number (auto-generated if not provided).
            incorporation_date: Date of incorporation (defaults to 2020-01-01).

        Returns:
            The created Company ORM model.
        """
        unique_suffix = uuid4().hex[:8]

        company = Company(
            id=uuid4(),
            legal_name=legal_name or f"Test Company {unique_suffix}",
            trade_name=trade_name,
            registration_number=registration_number or f"REG-{unique_suffix}",
            incorporation_date=incorporation_date or date(2020, 1, 1),
            created_at=datetime.utcnow(),
        )

        session.add(company)
        await session.flush()
        await session.refresh(company)
        return company


class UserFactory:
    """Factory for creating User entities in the test database."""

    @staticmethod
    async def create(
        session: AsyncSession,
        company: Company,
        *,
        email: Optional[str] = None,
        password: str = "TestPassword123!",
        first_name: str = "Test",
        last_name: str = "User",
        role: UserRole = UserRole.BUYER,
        account_status: ActivationStatus = ActivationStatus.ACTIVE,
    ) -> User:
        """
        Create a User entity in the database.

        Args:
            session: The async database session.
            company: The Company the user belongs to.
            email: User email (auto-generated if not provided).
            password: Plain text password (will be encrypted).
            first_name: User first name.
            last_name: User last name.
            role: User role (defaults to BUYER).
            account_status: Account status (defaults to ACTIVE).

        Returns:
            The created User ORM model.
        """
        unique_suffix = uuid4().hex[:8]

        user = User(
            id=uuid4(),
            email=email or f"test.user.{unique_suffix}@example.com",
            password=encrypt_password(password),
            first_name=first_name,
            last_name=last_name,
            company_id=company.id,
            role=role,
            account_status=account_status,
            created_at=datetime.utcnow(),
        )

        session.add(user)
        await session.flush()
        await session.refresh(user)
        return user

    @staticmethod
    async def create_admin(
        session: AsyncSession,
        company: Company,
        *,
        email: Optional[str] = None,
        password: str = "AdminPassword123!",
    ) -> User:
        """
        Create an admin User entity in the database.

        Args:
            session: The async database session.
            company: The Company the user belongs to.
            email: User email (auto-generated if not provided).
            password: Plain text password.

        Returns:
            The created admin User ORM model.
        """
        return await UserFactory.create(
            session,
            company,
            email=email,
            password=password,
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            account_status=ActivationStatus.ACTIVE,
        )

    @staticmethod
    async def create_inactive(
        session: AsyncSession,
        company: Company,
        *,
        email: Optional[str] = None,
        password: str = "TestPassword123!",
        account_status: ActivationStatus = ActivationStatus.AWAITING_APPROVAL,
    ) -> User:
        """
        Create an inactive User entity in the database.

        Args:
            session: The async database session.
            company: The Company the user belongs to.
            email: User email (auto-generated if not provided).
            password: Plain text password.
            account_status: The inactive account status.

        Returns:
            The created inactive User ORM model.
        """
        return await UserFactory.create(
            session,
            company,
            email=email,
            password=password,
            first_name="Inactive",
            last_name="User",
            role=UserRole.BUYER,
            account_status=account_status,
        )

    @staticmethod
    async def create_issuer(
        session: AsyncSession,
        company: Company,
        *,
        email: Optional[str] = None,
        password: str = "IssuerPassword123!",
    ) -> User:
        """
        Create an issuer User entity in the database.

        Args:
            session: The async database session.
            company: The Company the user belongs to.
            email: User email (auto-generated if not provided).
            password: Plain text password.

        Returns:
            The created issuer User ORM model.
        """
        return await UserFactory.create(
            session,
            company,
            email=email,
            password=password,
            first_name="Issuer",
            last_name="User",
            role=UserRole.ISSUER,
            account_status=ActivationStatus.ACTIVE,
        )


class InstrumentFactory:
    """Factory for creating Instrument entities in the test database."""

    @staticmethod
    async def create(
        session: AsyncSession,
        company: Company,
        user: User,
        *,
        name: Optional[str] = None,
        face_value: float = 10000.00,
        currency: str = "USD",
        maturity_date: Optional[date] = None,
        maturity_payment: float = 10500.00,
        instrument_status: InstrumentStatus = InstrumentStatus.DRAFT,
        maturity_status: MaturityStatus = MaturityStatus.NOT_DUE,
        trading_status: TradingStatus = TradingStatus.DRAFT,
        public_payload: Optional[Dict[str, Any]] = None,
    ) -> Instrument:
        """
        Create an Instrument entity in the database.

        Args:
            session: The async database session.
            company: The Company that issues the instrument.
            user: The User who created the instrument.
            name: Instrument name (auto-generated if not provided).
            face_value: Face value of the instrument.
            currency: Currency code (3 chars, e.g., USD).
            maturity_date: Date of maturity (defaults to 90 days from now).
            maturity_payment: Amount to be paid at maturity.
            instrument_status: Status of the instrument (defaults to DRAFT).
            maturity_status: Maturity status (defaults to NOT_DUE).
            trading_status: Trading status (defaults to DRAFT).
            public_payload: Optional payload dict (defaults to empty dict).

        Returns:
            The created Instrument ORM model.
        """
        unique_suffix = uuid4().hex[:8]
        instrument_id = uuid4()

        instrument = Instrument(
            id=instrument_id,
            name=name or f"Test Instrument {unique_suffix}",
            face_value=face_value,
            currency=currency,
            maturity_date=maturity_date or (date.today() + timedelta(days=90)),
            maturity_payment=maturity_payment,
            instrument_status=instrument_status,
            maturity_status=maturity_status,
            trading_status=trading_status,
            issuer_id=company.id,
            created_by=user.id,
            created_at=datetime.utcnow(),
        )

        session.add(instrument)
        await session.flush()

        # Create associated public payload
        payload_record = InstrumentPublicPayload(
            id=uuid4(),
            instrument_id=instrument_id,
            payload=public_payload if public_payload is not None else {},
            created_at=datetime.utcnow(),
        )
        session.add(payload_record)
        await session.flush()

        await session.refresh(instrument)
        return instrument

    @staticmethod
    async def create_pending_approval(
        session: AsyncSession,
        company: Company,
        user: User,
        *,
        name: Optional[str] = None,
    ) -> Instrument:
        """
        Create an Instrument with PENDING_APPROVAL status.

        Args:
            session: The async database session.
            company: The Company that issues the instrument.
            user: The User who created the instrument.
            name: Instrument name (auto-generated if not provided).

        Returns:
            The created Instrument ORM model with PENDING_APPROVAL status.
        """
        return await InstrumentFactory.create(
            session,
            company,
            user,
            name=name,
            instrument_status=InstrumentStatus.PENDING_APPROVAL,
        )

    @staticmethod
    async def create_active(
        session: AsyncSession,
        company: Company,
        user: User,
        *,
        name: Optional[str] = None,
    ) -> Instrument:
        """
        Create an active Instrument.

        Args:
            session: The async database session.
            company: The Company that issues the instrument.
            user: The User who created the instrument.
            name: Instrument name (auto-generated if not provided).

        Returns:
            The created active Instrument ORM model.
        """
        return await InstrumentFactory.create(
            session,
            company,
            user,
            name=name,
            instrument_status=InstrumentStatus.ACTIVE,
            maturity_status=MaturityStatus.DUE,
            trading_status=TradingStatus.LISTED,
        )


class CompanyAddressFactory:
    """Factory for creating CompanyAddress entities in the test database."""

    @staticmethod
    async def create(
        session: AsyncSession,
        company: Company,
        *,
        address_type: AddressType = AddressType.REGISTERED,
        street: Optional[str] = None,
        city: str = "New York",
        state: Optional[str] = "NY",
        postal_code: str = "10001",
        country: str = "US",
    ) -> CompanyAddress:
        """
        Create a CompanyAddress entity in the database.

        Args:
            session: The async database session.
            company: The Company this address belongs to.
            address_type: Type of address (defaults to REGISTERED).
            street: Street address (auto-generated if not provided).
            city: City name.
            state: State/province (optional).
            postal_code: Postal/ZIP code.
            country: ISO 3166-1 alpha-2 country code.

        Returns:
            The created CompanyAddress ORM model.
        """
        unique_suffix = uuid4().hex[:8]

        address = CompanyAddress(
            id=uuid4(),
            company_id=company.id,
            type=address_type,
            street=street or f"123 Test Street {unique_suffix}",
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            created_at=datetime.utcnow(),
        )

        session.add(address)
        await session.flush()
        await session.refresh(address)
        return address

    @staticmethod
    async def create_billing(
        session: AsyncSession,
        company: Company,
        *,
        street: Optional[str] = None,
    ) -> CompanyAddress:
        """
        Create a billing CompanyAddress.

        Args:
            session: The async database session.
            company: The Company this address belongs to.
            street: Street address (auto-generated if not provided).

        Returns:
            The created billing CompanyAddress ORM model.
        """
        return await CompanyAddressFactory.create(
            session,
            company,
            address_type=AddressType.BILLING,
            street=street,
        )

    @staticmethod
    async def create_office(
        session: AsyncSession,
        company: Company,
        *,
        street: Optional[str] = None,
    ) -> CompanyAddress:
        """
        Create an office CompanyAddress.

        Args:
            session: The async database session.
            company: The Company this address belongs to.
            street: Street address (auto-generated if not provided).

        Returns:
            The created office CompanyAddress ORM model.
        """
        return await CompanyAddressFactory.create(
            session,
            company,
            address_type=AddressType.OFFICE,
            street=street,
        )


class DocumentFactory:
    """Factory for creating Document entities in the test database."""

    @staticmethod
    async def create(
        session: AsyncSession,
        user: User,
        *,
        internal_filename: Optional[str] = None,
        mime: str = "application/pdf",
        storage_bucket: str = "test-bucket",
        storage_object_key: Optional[str] = None,
    ) -> Document:
        """
        Create a Document entity in the database.

        Args:
            session: The async database session.
            user: The User who created the document.
            internal_filename: Internal file name (auto-generated if not provided).
            mime: MIME type of the document.
            storage_bucket: Storage bucket name.
            storage_object_key: Storage object key (auto-generated if not provided).

        Returns:
            The created Document ORM model.
        """
        unique_suffix = uuid4().hex[:8]

        document = Document(
            id=uuid4(),
            internal_filename=internal_filename
            or f"test_document_{unique_suffix}.pdf",
            mime=mime,
            storage_bucket=storage_bucket,
            storage_object_key=storage_object_key
            or f"documents/{unique_suffix}",
            created_by=user.id,
            created_at=datetime.utcnow(),
        )

        session.add(document)
        await session.flush()
        await session.refresh(document)
        return document


class InstrumentDocumentFactory:
    """Factory for creating InstrumentDocument entities in the test database."""

    @staticmethod
    async def create(
        session: AsyncSession,
        instrument: Instrument,
        document: Document,
    ) -> InstrumentDocument:
        """
        Create an InstrumentDocument association entity in the database.

        Args:
            session: The async database session.
            instrument: The Instrument to associate.
            document: The Document to associate.

        Returns:
            The created InstrumentDocument ORM model.
        """
        instrument_document = InstrumentDocument(
            id=uuid4(),
            instrument_id=instrument.id,
            document_id=document.id,
            created_at=datetime.utcnow(),
        )

        session.add(instrument_document)
        await session.flush()
        await session.refresh(instrument_document)
        return instrument_document


class InstrumentOwnershipFactory:
    """Factory for creating InstrumentOwnership entities in the test database."""

    @staticmethod
    async def create(
        session: AsyncSession,
        instrument: Instrument,
        owner: Company,
        *,
        acquired_at: Optional[datetime] = None,
        relinquished_at: Optional[datetime] = None,
        acquisition_reason: AcquisitionReason = AcquisitionReason.ISSUANCE,
    ) -> InstrumentOwnership:
        """
        Create an InstrumentOwnership entity in the database.

        Args:
            session: The async database session.
            instrument: The Instrument being owned.
            owner: The Company that owns the instrument.
            acquired_at: When ownership was acquired (defaults to now).
            relinquished_at: When ownership was relinquished (None if still active).
            acquisition_reason: Reason for acquiring ownership.

        Returns:
            The created InstrumentOwnership ORM model.
        """
        ownership = InstrumentOwnership(
            id=uuid4(),
            instrument_id=instrument.id,
            owner_id=owner.id,
            acquired_at=acquired_at or datetime.utcnow(),
            relinquished_at=relinquished_at,
            acquisition_reason=acquisition_reason,
            created_at=datetime.utcnow(),
        )

        session.add(ownership)
        await session.flush()
        await session.refresh(ownership)
        return ownership

    @staticmethod
    async def create_active(
        session: AsyncSession,
        instrument: Instrument,
        owner: Company,
        *,
        acquisition_reason: AcquisitionReason = AcquisitionReason.ISSUANCE,
    ) -> InstrumentOwnership:
        """
        Create an active (non-relinquished) InstrumentOwnership.

        Args:
            session: The async database session.
            instrument: The Instrument being owned.
            owner: The Company that owns the instrument.
            acquisition_reason: Reason for acquiring ownership.

        Returns:
            The created active InstrumentOwnership ORM model.
        """
        return await InstrumentOwnershipFactory.create(
            session,
            instrument,
            owner,
            acquisition_reason=acquisition_reason,
            relinquished_at=None,
        )


class ListingFactory:
    """Factory for creating Listing entities in the test database."""

    @staticmethod
    async def create(
        session: AsyncSession,
        instrument: Instrument,
        seller_company: Company,
        creator_user: User,
        *,
        status: ListingStatus = ListingStatus.OPEN,
    ) -> Listing:
        """
        Create a Listing entity in the database.

        Args:
            session: The async database session.
            instrument: The Instrument being listed.
            seller_company: The Company selling the instrument.
            creator_user: The User who created the listing.
            status: Listing status (defaults to OPEN).

        Returns:
            The created Listing ORM model.
        """
        listing = Listing(
            id=uuid4(),
            instrument_id=instrument.id,
            seller_company_id=seller_company.id,
            listing_creator_user_id=creator_user.id,
            status=status,
            created_at=datetime.utcnow(),
        )

        session.add(listing)
        await session.flush()
        await session.refresh(listing)
        return listing

    @staticmethod
    async def create_open(
        session: AsyncSession,
        instrument: Instrument,
        seller_company: Company,
        creator_user: User,
    ) -> Listing:
        """
        Create an OPEN Listing.

        Args:
            session: The async database session.
            instrument: The Instrument being listed.
            seller_company: The Company selling the instrument.
            creator_user: The User who created the listing.

        Returns:
            The created OPEN Listing ORM model.
        """
        return await ListingFactory.create(
            session,
            instrument,
            seller_company,
            creator_user,
            status=ListingStatus.OPEN,
        )

    @staticmethod
    async def create_withdrawn(
        session: AsyncSession,
        instrument: Instrument,
        seller_company: Company,
        creator_user: User,
    ) -> Listing:
        """
        Create a WITHDRAWN Listing.

        Args:
            session: The async database session.
            instrument: The Instrument being listed.
            seller_company: The Company selling the instrument.
            creator_user: The User who created the listing.

        Returns:
            The created WITHDRAWN Listing ORM model.
        """
        return await ListingFactory.create(
            session,
            instrument,
            seller_company,
            creator_user,
            status=ListingStatus.WITHDRAWN,
        )

    @staticmethod
    async def create_suspended(
        session: AsyncSession,
        instrument: Instrument,
        seller_company: Company,
        creator_user: User,
    ) -> Listing:
        """
        Create a SUSPENDED Listing.

        Args:
            session: The async database session.
            instrument: The Instrument being listed.
            seller_company: The Company selling the instrument.
            creator_user: The User who created the listing.

        Returns:
            The created SUSPENDED Listing ORM model.
        """
        return await ListingFactory.create(
            session,
            instrument,
            seller_company,
            creator_user,
            status=ListingStatus.SUSPENDED,
        )

    @staticmethod
    async def create_closed(
        session: AsyncSession,
        instrument: Instrument,
        seller_company: Company,
        creator_user: User,
    ) -> Listing:
        """
        Create a CLOSED Listing.

        Args:
            session: The async database session.
            instrument: The Instrument being listed.
            seller_company: The Company selling the instrument.
            creator_user: The User who created the listing.

        Returns:
            The created CLOSED Listing ORM model.
        """
        return await ListingFactory.create(
            session,
            instrument,
            seller_company,
            creator_user,
            status=ListingStatus.CLOSED,
        )


class BidFactory:
    """Factory for creating Bid entities in the test database."""

    @staticmethod
    async def create(
        session: AsyncSession,
        listing: Listing,
        bidder_company: Company,
        bidder_user: User,
        *,
        amount: float = 10000.00,
        currency: str = "USD",
        valid_until: Optional[datetime] = None,
        status: BidStatus = BidStatus.PENDING,
    ) -> Bid:
        """
        Create a Bid entity in the database.

        Args:
            session: The async database session.
            listing: The Listing being bid on.
            bidder_company: The Company making the bid.
            bidder_user: The User who created the bid.
            amount: Bid amount (defaults to 10000.00).
            currency: ISO 4217 currency code (defaults to USD).
            valid_until: Optional bid expiration timestamp.
            status: Bid status (defaults to PENDING).

        Returns:
            The created Bid ORM model.
        """
        bid = Bid(
            id=uuid4(),
            listing_id=listing.id,
            bidder_company_id=bidder_company.id,
            bidder_user_id=bidder_user.id,
            amount=amount,
            currency=currency,
            valid_until=valid_until,
            status=status,
            created_at=datetime.utcnow(),
        )

        session.add(bid)
        await session.flush()
        await session.refresh(bid)
        return bid

    @staticmethod
    async def create_pending(
        session: AsyncSession,
        listing: Listing,
        bidder_company: Company,
        bidder_user: User,
        *,
        amount: float = 10000.00,
        currency: str = "USD",
    ) -> Bid:
        """
        Create a PENDING Bid.

        Args:
            session: The async database session.
            listing: The Listing being bid on.
            bidder_company: The Company making the bid.
            bidder_user: The User who created the bid.
            amount: Bid amount.
            currency: ISO 4217 currency code.

        Returns:
            The created PENDING Bid ORM model.
        """
        return await BidFactory.create(
            session,
            listing,
            bidder_company,
            bidder_user,
            amount=amount,
            currency=currency,
            status=BidStatus.PENDING,
        )

    @staticmethod
    async def create_withdrawn(
        session: AsyncSession,
        listing: Listing,
        bidder_company: Company,
        bidder_user: User,
        *,
        amount: float = 10000.00,
        currency: str = "USD",
    ) -> Bid:
        """
        Create a WITHDRAWN Bid.

        Args:
            session: The async database session.
            listing: The Listing being bid on.
            bidder_company: The Company making the bid.
            bidder_user: The User who created the bid.
            amount: Bid amount.
            currency: ISO 4217 currency code.

        Returns:
            The created WITHDRAWN Bid ORM model.
        """
        return await BidFactory.create(
            session,
            listing,
            bidder_company,
            bidder_user,
            amount=amount,
            currency=currency,
            status=BidStatus.WITHDRAWN,
        )

    @staticmethod
    async def create_selected(
        session: AsyncSession,
        listing: Listing,
        bidder_company: Company,
        bidder_user: User,
        *,
        amount: float = 10000.00,
        currency: str = "USD",
    ) -> Bid:
        """
        Create a SELECTED Bid.

        Args:
            session: The async database session.
            listing: The Listing being bid on.
            bidder_company: The Company making the bid.
            bidder_user: The User who created the bid.
            amount: Bid amount.
            currency: ISO 4217 currency code.

        Returns:
            The created SELECTED Bid ORM model.
        """
        return await BidFactory.create(
            session,
            listing,
            bidder_company,
            bidder_user,
            amount=amount,
            currency=currency,
            status=BidStatus.SELECTED,
        )


class AskFactory:
    """Factory for creating Ask entities in the test database."""

    @staticmethod
    async def create(
        session: AsyncSession,
        listing: Listing,
        asker_company: Company,
        asker_user: User,
        *,
        amount: float = 10000.00,
        currency: str = "USD",
        valid_until: Optional[datetime] = None,
        execution_mode: ExecutionMode = ExecutionMode.MANUAL,
        binding: bool = False,
        status: AskStatus = AskStatus.ACTIVE,
    ) -> Ask:
        """
        Create an Ask entity in the database.

        Args:
            session: The async database session.
            listing: The Listing this ask is for.
            asker_company: The Company making the ask (must be the listing owner).
            asker_user: The User who created the ask.
            amount: Ask amount (defaults to 10000.00).
            currency: ISO 4217 currency code (defaults to USD).
            valid_until: Optional ask expiration timestamp.
            execution_mode: Execution mode (defaults to MANUAL).
            binding: Whether the ask is binding (defaults to False).
            status: Ask status (defaults to ACTIVE).

        Returns:
            The created Ask ORM model.
        """
        ask = Ask(
            id=uuid4(),
            listing_id=listing.id,
            asker_company_id=asker_company.id,
            asker_user_id=asker_user.id,
            amount=amount,
            currency=currency,
            valid_until=valid_until,
            execution_mode=execution_mode,
            binding=binding,
            status=status,
            created_at=datetime.utcnow(),
        )

        session.add(ask)
        await session.flush()
        await session.refresh(ask)
        return ask

    @staticmethod
    async def create_active(
        session: AsyncSession,
        listing: Listing,
        asker_company: Company,
        asker_user: User,
        *,
        amount: float = 10000.00,
        currency: str = "USD",
    ) -> Ask:
        """
        Create an ACTIVE Ask.

        Args:
            session: The async database session.
            listing: The Listing this ask is for.
            asker_company: The Company making the ask.
            asker_user: The User who created the ask.
            amount: Ask amount.
            currency: ISO 4217 currency code.

        Returns:
            The created ACTIVE Ask ORM model.
        """
        return await AskFactory.create(
            session,
            listing,
            asker_company,
            asker_user,
            amount=amount,
            currency=currency,
            status=AskStatus.ACTIVE,
        )

    @staticmethod
    async def create_withdrawn(
        session: AsyncSession,
        listing: Listing,
        asker_company: Company,
        asker_user: User,
        *,
        amount: float = 10000.00,
        currency: str = "USD",
    ) -> Ask:
        """
        Create a WITHDRAWN Ask.

        Args:
            session: The async database session.
            listing: The Listing this ask is for.
            asker_company: The Company making the ask.
            asker_user: The User who created the ask.
            amount: Ask amount.
            currency: ISO 4217 currency code.

        Returns:
            The created WITHDRAWN Ask ORM model.
        """
        return await AskFactory.create(
            session,
            listing,
            asker_company,
            asker_user,
            amount=amount,
            currency=currency,
            status=AskStatus.WITHDRAWN,
        )

    @staticmethod
    async def create_suspended(
        session: AsyncSession,
        listing: Listing,
        asker_company: Company,
        asker_user: User,
        *,
        amount: float = 10000.00,
        currency: str = "USD",
    ) -> Ask:
        """
        Create a SUSPENDED Ask.

        Args:
            session: The async database session.
            listing: The Listing this ask is for.
            asker_company: The Company making the ask.
            asker_user: The User who created the ask.
            amount: Ask amount.
            currency: ISO 4217 currency code.

        Returns:
            The created SUSPENDED Ask ORM model.
        """
        return await AskFactory.create(
            session,
            listing,
            asker_company,
            asker_user,
            amount=amount,
            currency=currency,
            status=AskStatus.SUSPENDED,
        )
