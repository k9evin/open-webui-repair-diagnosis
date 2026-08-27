from contextlib import asynccontextmanager

import pytest
from open_webui.internal.db import Base
from open_webui.models import repair
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.mark.asyncio
async def test_approved_exact_pn_candidates_exclude_pending_and_other_pns(monkeypatch):
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session = async_sessionmaker(engine, expire_on_commit=False)()

    @asynccontextmanager
    async def test_db_context(_=None):
        yield session

    monkeypatch.setattr(repair, 'get_async_db_context', test_db_context)
    try:
        approved = await repair.RepairCases.create_case(
            repair.RepairCaseForm(
                pn='PCBA-001-A',
                product_type='PCBA',
                failure_type='VOA',
                failure_description='VOA 无电流',
            ),
            'engineer',
            review_status='approved',
            case_prefix='R',
        )
        await repair.RepairCases.create_case(
            repair.RepairCaseForm(
                pn='PCBA-001-A',
                product_type='PCBA',
                failure_type='VOA',
                failure_description='待审核案例',
            ),
            'operator',
        )
        await repair.RepairCases.create_case(
            repair.RepairCaseForm(
                pn='PCBA-999-Z',
                product_type='PCBA',
                failure_type='VOA',
                failure_description='同类型参考案例',
            ),
            'engineer',
            review_status='approved',
            case_prefix='R',
        )

        scope, candidates = await repair.RepairCases.get_approved_candidates('pcba 001 a', 'PCBA', 'VOA')

        assert scope == 'exact_pn'
        assert [case.id for case in candidates] == [approved.id]
        assert all(case.review_status == 'approved' for case in candidates)
    finally:
        await session.close()
        await engine.dispose()


@pytest.mark.asyncio
async def test_fallback_is_limited_to_same_product_type_and_failure_type(monkeypatch):
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session = async_sessionmaker(engine, expire_on_commit=False)()

    @asynccontextmanager
    async def test_db_context(_=None):
        yield session

    monkeypatch.setattr(repair, 'get_async_db_context', test_db_context)
    try:
        reference = await repair.RepairCases.create_case(
            repair.RepairCaseForm(
                pn='PCBA-002-A',
                product_type='PCBA',
                failure_type='VOA',
                failure_description='VOA 无电流',
            ),
            'engineer',
            review_status='approved',
            case_prefix='R',
        )
        await repair.RepairCases.create_case(
            repair.RepairCaseForm(
                pn='PCBA-003-A',
                product_type='PCBA',
                failure_type='通信',
                failure_description='通信异常',
            ),
            'engineer',
            review_status='approved',
            case_prefix='R',
        )
        await repair.RepairCases.create_case(
            repair.RepairCaseForm(
                pn='EDFA-001-A',
                product_type='EDFA',
                failure_type='VOA',
                failure_description='不应跨产品类型返回',
            ),
            'engineer',
            review_status='approved',
            case_prefix='R',
        )

        scope, candidates = await repair.RepairCases.get_approved_candidates('PCBA-404-A', 'PCBA', 'VOA')

        assert scope == 'same_product_type_reference'
        assert [case.id for case in candidates] == [reference.id]
        assert all(case.product_type == 'PCBA' and case.failure_type == 'VOA' for case in candidates)
    finally:
        await session.close()
        await engine.dispose()
