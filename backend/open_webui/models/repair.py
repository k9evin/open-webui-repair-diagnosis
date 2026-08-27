import re
import time
import uuid

from open_webui.internal.db import Base, get_async_db_context
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import JSON, BigInteger, Column, Text, select, update
from sqlalchemy.ext.asyncio import AsyncSession


def normalize_pn(value: str) -> str:
    return re.sub(r'[\s_-]+', '', value or '').upper()


class RepairCase(Base):
    __tablename__ = 'repair_case'

    id = Column(Text, primary_key=True)
    source_file = Column(Text, nullable=True)
    source_row_id = Column(Text, nullable=True)
    raw_record_json = Column(JSON, nullable=False, default=dict)
    pn_raw = Column(Text, nullable=False)
    pn_normalized = Column(Text, nullable=False, index=True)
    sn = Column(Text, nullable=True)
    product_type = Column(Text, nullable=False, index=True)
    product_family = Column(Text, nullable=True, index=True)
    plant = Column(Text, nullable=True)
    failure_type = Column(Text, nullable=True, index=True)
    failure_description_raw = Column(Text, nullable=False)
    repair_steps_raw = Column(Text, nullable=True)
    repair_steps_normalized = Column(Text, nullable=True)
    test_result_raw = Column(Text, nullable=True)
    measurement_status = Column(Text, nullable=False, default='not_recorded')
    original_part_pn = Column(Text, nullable=True)
    replacement_part_pn = Column(Text, nullable=True)
    replacement_part_raw = Column(Text, nullable=True)
    final_result = Column(Text, nullable=True)
    retest_result = Column(Text, nullable=True)
    root_cause = Column(Text, nullable=True)
    review_status = Column(Text, nullable=False, default='pending', index=True)
    case_quality = Column(Text, nullable=False, default='D')
    submitted_by = Column(Text, nullable=True)
    reviewed_by = Column(Text, nullable=True)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)


class RepairSOP(Base):
    __tablename__ = 'repair_sop'

    id = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    version = Column(Text, nullable=False)
    product_type = Column(Text, nullable=False, index=True)
    failure_type = Column(Text, nullable=True, index=True)
    applicable_pn = Column(Text, nullable=True)
    product_family = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    effective_date = Column(Text, nullable=True)
    expires_at = Column(Text, nullable=True)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)


class RepairAuditLog(Base):
    __tablename__ = 'repair_audit_log'

    id = Column(Text, primary_key=True)
    user_id = Column(Text, nullable=False)
    action = Column(Text, nullable=False)
    case_id = Column(Text, nullable=True, index=True)
    payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(BigInteger, nullable=False)


class RepairCaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_file: str | None = None
    source_row_id: str | None = None
    raw_record_json: dict = Field(default_factory=dict)
    pn_raw: str
    pn_normalized: str
    sn: str | None = None
    product_type: str
    product_family: str | None = None
    plant: str | None = None
    failure_type: str | None = None
    failure_description_raw: str
    repair_steps_raw: str | None = None
    repair_steps_normalized: str | None = None
    test_result_raw: str | None = None
    measurement_status: str
    original_part_pn: str | None = None
    replacement_part_pn: str | None = None
    replacement_part_raw: str | None = None
    final_result: str | None = None
    retest_result: str | None = None
    root_cause: str | None = None
    review_status: str
    case_quality: str
    submitted_by: str | None = None
    reviewed_by: str | None = None
    created_at: int
    updated_at: int


class RepairCaseForm(BaseModel):
    pn: str
    sn: str | None = None
    product_type: str
    plant: str | None = None
    failure_type: str | None = None
    failure_description: str
    repair_steps: str | None = None
    test_result: str | None = None
    measurement_status: str = 'not_recorded'
    original_part_pn: str | None = None
    replacement_part_pn: str | None = None
    replacement_part_raw: str | None = None
    final_result: str | None = None
    retest_result: str | None = None
    root_cause: str | None = None
    product_family: str | None = None
    source_file: str | None = None
    source_row_id: str | None = None
    raw_record_json: dict = Field(default_factory=dict)


class RepairSOPModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    version: str
    product_type: str
    failure_type: str | None = None
    applicable_pn: str | None = None
    product_family: str | None = None
    content: str
    effective_date: str | None = None
    expires_at: str | None = None
    created_at: int
    updated_at: int


class RepairSOPForm(BaseModel):
    name: str
    version: str
    product_type: str
    failure_type: str | None = None
    applicable_pn: str | None = None
    product_family: str | None = None
    content: str
    effective_date: str | None = None
    expires_at: str | None = None


class RepairCasesTable:
    async def create_case(
        self,
        form_data: RepairCaseForm,
        submitted_by: str,
        review_status: str = 'pending',
        case_prefix: str = 'FB',
        db: AsyncSession | None = None,
    ) -> RepairCaseModel:
        now = int(time.time())
        case = RepairCase(
            id=f'{case_prefix}-{uuid.uuid4().hex[:8].upper()}',
            source_file=form_data.source_file,
            source_row_id=form_data.source_row_id,
            raw_record_json=form_data.raw_record_json,
            pn_raw=form_data.pn,
            pn_normalized=normalize_pn(form_data.pn),
            sn=form_data.sn,
            product_type=form_data.product_type,
            product_family=form_data.product_family,
            plant=form_data.plant,
            failure_type=form_data.failure_type,
            failure_description_raw=form_data.failure_description,
            repair_steps_raw=form_data.repair_steps,
            repair_steps_normalized=form_data.repair_steps,
            test_result_raw=form_data.test_result,
            measurement_status=form_data.measurement_status,
            original_part_pn=form_data.original_part_pn,
            replacement_part_pn=form_data.replacement_part_pn,
            replacement_part_raw=form_data.replacement_part_raw,
            final_result=form_data.final_result,
            retest_result=form_data.retest_result,
            root_cause=form_data.root_cause,
            review_status=review_status,
            submitted_by=submitted_by,
            created_at=now,
            updated_at=now,
        )
        async with get_async_db_context(db) as session:
            session.add(case)
            await session.commit()
            await session.refresh(case)
            return RepairCaseModel.model_validate(case)

    async def get_case(self, case_id: str, db: AsyncSession | None = None) -> RepairCaseModel | None:
        async with get_async_db_context(db) as session:
            case = await session.get(RepairCase, case_id)
            return RepairCaseModel.model_validate(case) if case else None

    async def get_approved_candidates(
        self,
        pn: str,
        product_type: str,
        failure_type: str | None,
        db: AsyncSession | None = None,
    ) -> tuple[str, list[RepairCaseModel]]:
        async with get_async_db_context(db) as session:
            exact = await session.execute(
                select(RepairCase)
                .where(RepairCase.pn_normalized == normalize_pn(pn))
                .where(RepairCase.product_type == product_type)
                .where(RepairCase.review_status == 'approved')
                .order_by(RepairCase.updated_at.desc())
            )
            cases = exact.scalars().all()
            if cases:
                return 'exact_pn', [RepairCaseModel.model_validate(case) for case in cases]

            if failure_type:
                fallback = await session.execute(
                    select(RepairCase)
                    .where(RepairCase.product_type == product_type)
                    .where(RepairCase.failure_type == failure_type)
                    .where(RepairCase.review_status == 'approved')
                    .order_by(RepairCase.updated_at.desc())
                )
                cases = fallback.scalars().all()
                if cases:
                    return 'same_product_type_reference', [RepairCaseModel.model_validate(case) for case in cases]
            return 'no_reliable_case', []

    async def list_cases(
        self, review_status: str | None = None, db: AsyncSession | None = None
    ) -> list[RepairCaseModel]:
        async with get_async_db_context(db) as session:
            stmt = select(RepairCase).order_by(RepairCase.updated_at.desc())
            if review_status:
                stmt = stmt.where(RepairCase.review_status == review_status)
            result = await session.execute(stmt)
            return [RepairCaseModel.model_validate(case) for case in result.scalars().all()]

    async def review_case(
        self,
        case_id: str,
        review_status: str,
        reviewed_by: str,
        case_quality: str | None = None,
        root_cause: str | None = None,
        db: AsyncSession | None = None,
    ) -> RepairCaseModel | None:
        values = {'review_status': review_status, 'reviewed_by': reviewed_by, 'updated_at': int(time.time())}
        if case_quality is not None:
            values['case_quality'] = case_quality
        if root_cause is not None:
            values['root_cause'] = root_cause
        async with get_async_db_context(db) as session:
            await session.execute(update(RepairCase).where(RepairCase.id == case_id).values(**values))
            await session.commit()
            case = await session.get(RepairCase, case_id)
            return RepairCaseModel.model_validate(case) if case else None


class RepairSOPsTable:
    async def create(self, form_data: RepairSOPForm, db: AsyncSession | None = None) -> RepairSOPModel:
        now = int(time.time())
        sop = RepairSOP(
            id=f'SOP-{uuid.uuid4().hex[:8].upper()}',
            **form_data.model_dump(),
            created_at=now,
            updated_at=now,
        )
        async with get_async_db_context(db) as session:
            session.add(sop)
            await session.commit()
            await session.refresh(sop)
            return RepairSOPModel.model_validate(sop)

    async def find_for_retrieval(
        self, product_type: str, failure_type: str | None, db: AsyncSession | None = None
    ) -> RepairSOPModel | None:
        async with get_async_db_context(db) as session:
            stmt = select(RepairSOP).where(RepairSOP.product_type == product_type)
            if failure_type:
                stmt = stmt.where(RepairSOP.failure_type == failure_type)
            result = await session.execute(stmt.order_by(RepairSOP.updated_at.desc()))
            sop = result.scalars().first()
            return RepairSOPModel.model_validate(sop) if sop else None


class RepairAuditLogsTable:
    async def record(
        self,
        user_id: str,
        action: str,
        case_id: str | None = None,
        payload: dict | None = None,
        db: AsyncSession | None = None,
    ) -> None:
        async with get_async_db_context(db) as session:
            session.add(
                RepairAuditLog(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    action=action,
                    case_id=case_id,
                    payload=payload or {},
                    created_at=int(time.time()),
                )
            )
            await session.commit()


RepairCases = RepairCasesTable()
RepairSOPs = RepairSOPsTable()
RepairAuditLogs = RepairAuditLogsTable()
