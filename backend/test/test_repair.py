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


@pytest.mark.asyncio
async def test_reference_metadata_filter_excludes_out_of_scope_chunks(monkeypatch):
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session = async_sessionmaker(engine, expire_on_commit=False)()

    @asynccontextmanager
    async def test_db_context(_=None):
        yield session

    monkeypatch.setattr(repair, 'get_async_db_context', test_db_context)
    try:
        scoped_form = repair.RepairReferenceDocumentForm(
            file_id='file-voa',
            document_type='debug_guide',
            pn=['PCBA-001-A'],
            product_type='PCBA',
            failure_type='VOA',
            plant='A厂',
        )
        document, _ = await repair.RepairReferences.create_document(
            scoped_form,
            'voa-debug.md',
            '第一段：检查 VOA 电流。\n\n第二段：记录测量值。',
            'admin',
            {'engine': 'MinerU'},
            30,
            0,
        )
        await repair.RepairReferences.create_document(
            repair.RepairReferenceDocumentForm(
                file_id='file-other',
                document_type='work_requirement',
                pn=['EDFA-001-A'],
                product_type='EDFA',
                failure_type='VOA',
                plant='A厂',
            ),
            'edfa-work.md',
            '检查 VOA 电流。这条辅助材料不适用于 PCBA。',
            'admin',
            {'engine': 'MinerU'},
            30,
            0,
        )

        candidates = await repair.RepairReferences.get_metadata_candidates(
            'PCBA-001-A', None, 'PCBA', 'VOA', 'A厂'
        )

        assert candidates
        assert {chunk.document_id for chunk in candidates} == {document.id}
        full_text = await repair.RepairReferences.search_full_text(
            [chunk.id for chunk in candidates], '检查 VOA 电流', 10
        )
        assert full_text
        assert {chunk.document_id for chunk in full_text} == {document.id}

    finally:
        await session.close()
        await engine.dispose()
