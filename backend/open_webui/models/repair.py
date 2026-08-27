import json
import re
import time
import uuid

from open_webui.internal.db import Base, get_async_db_context
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import JSON, BigInteger, Column, Integer, Text, bindparam, delete, select, text, update
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


class RepairReferenceDocument(Base):
    __tablename__ = 'repair_reference_document'

    id = Column(Text, primary_key=True)
    file_id = Column(Text, nullable=False, unique=True)
    document_type = Column(Text, nullable=False, index=True)
    version = Column(Text, nullable=True)
    source_name = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    pn_normalized = Column(JSON, nullable=False, default=list)
    product_family = Column(Text, nullable=True, index=True)
    product_type = Column(Text, nullable=True, index=True)
    failure_type = Column(Text, nullable=True, index=True)
    plant = Column(Text, nullable=True, index=True)
    extraction_config = Column(JSON, nullable=False, default=dict)
    created_by = Column(Text, nullable=False)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)


class RepairReferenceChunk(Base):
    __tablename__ = 'repair_reference_chunk'

    id = Column(Text, primary_key=True)
    document_id = Column(Text, nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    chunk_metadata = Column('metadata', JSON, nullable=False, default=dict)
    created_at = Column(BigInteger, nullable=False)


class RepairIndexVersion(Base):
    __tablename__ = 'repair_index_version'

    id = Column(Text, primary_key=True)
    config_hash = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    indexed_at = Column(BigInteger, nullable=True)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)


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


class RepairReferenceDocumentModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_id: str
    document_type: str
    version: str | None = None
    source_name: str
    content: str
    pn_normalized: list[str] = Field(default_factory=list)
    product_family: str | None = None
    product_type: str | None = None
    failure_type: str | None = None
    plant: str | None = None
    extraction_config: dict = Field(default_factory=dict)
    created_by: str
    created_at: int
    updated_at: int


class RepairReferenceChunkModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    chunk_index: int
    content: str
    chunk_metadata: dict = Field(default_factory=dict)
    created_at: int


class RepairReferenceDocumentForm(BaseModel):
    file_id: str
    document_type: str
    version: str | None = None
    pn: list[str] = Field(default_factory=list)
    product_family: str | None = None
    product_type: str | None = None
    failure_type: str | None = None
    plant: str | None = None


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


def chunk_reference_content(content: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in re.split(r'\n\s*\n', content) if paragraph.strip()]
    chunks: list[str] = []
    current = ''
    for paragraph in paragraphs:
        candidate = f'{current}\n\n{paragraph}'.strip()
        if current and len(candidate) > chunk_size:
            chunks.append(current)
            current = current[-chunk_overlap:] + '\n\n' + paragraph if chunk_overlap else paragraph
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


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


class RepairReferencesTable:
    @staticmethod
    def _chunk_model_from_row(row) -> RepairReferenceChunkModel:
        metadata = row.metadata
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        return RepairReferenceChunkModel(
            id=row.id,
            document_id=row.document_id,
            chunk_index=row.chunk_index,
            content=row.content,
            chunk_metadata=metadata,
            created_at=row.created_at,
        )

    async def set_index_status(
        self,
        config_hash: str,
        status: str,
        indexed_at: int | None = None,
        db: AsyncSession | None = None,
    ) -> RepairIndexVersion:
        now = int(time.time())
        async with get_async_db_context(db) as session:
            version = await session.get(RepairIndexVersion, 'repair_documents')
            if version:
                version.config_hash = config_hash
                version.status = status
                version.indexed_at = indexed_at
                version.updated_at = now
            else:
                version = RepairIndexVersion(
                    id='repair_documents',
                    config_hash=config_hash,
                    status=status,
                    indexed_at=indexed_at,
                    created_at=now,
                    updated_at=now,
                )
                session.add(version)
            await session.commit()
            await session.refresh(version)
            return version

    async def get_index_status(self, db: AsyncSession | None = None) -> RepairIndexVersion | None:
        async with get_async_db_context(db) as session:
            return await session.get(RepairIndexVersion, 'repair_documents')

    async def create_document(
        self,
        form_data: RepairReferenceDocumentForm,
        source_name: str,
        content: str,
        created_by: str,
        extraction_config: dict,
        chunk_size: int,
        chunk_overlap: int,
        db: AsyncSession | None = None,
    ) -> tuple[RepairReferenceDocumentModel, list[RepairReferenceChunkModel]]:
        now = int(time.time())
        document = RepairReferenceDocument(
            id=f'REF-{uuid.uuid4().hex[:8].upper()}',
            file_id=form_data.file_id,
            document_type=form_data.document_type,
            version=form_data.version,
            source_name=source_name,
            content=content,
            pn_normalized=[normalize_pn(pn) for pn in form_data.pn],
            product_family=form_data.product_family,
            product_type=form_data.product_type,
            failure_type=form_data.failure_type,
            plant=form_data.plant,
            extraction_config=extraction_config,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        chunks = [
            RepairReferenceChunk(
                id=f'REFC-{uuid.uuid4().hex[:8].upper()}',
                document_id=document.id,
                chunk_index=index,
                content=chunk,
                chunk_metadata={
                    'document_type': form_data.document_type,
                    'file_id': form_data.file_id,
                    'source_name': source_name,
                    'pn_normalized': [normalize_pn(pn) for pn in form_data.pn],
                    'product_type': form_data.product_type,
                    'failure_type': form_data.failure_type,
                    'plant': form_data.plant,
                    'version': form_data.version,
                },
                created_at=now,
            )
            for index, chunk in enumerate(chunk_reference_content(content, chunk_size, chunk_overlap))
        ]
        async with get_async_db_context(db) as session:
            session.add(document)
            session.add_all(chunks)
            await session.commit()
            await self._upsert_sqlite_full_text(session, chunks)
            return (
                RepairReferenceDocumentModel.model_validate(document),
                [RepairReferenceChunkModel.model_validate(chunk) for chunk in chunks],
            )

    @staticmethod
    async def _upsert_sqlite_full_text(session: AsyncSession, chunks: list[RepairReferenceChunk]) -> None:
        """Maintain the repair-only FTS index when the configured DB is SQLite."""
        if session.bind.dialect.name != 'sqlite' or not chunks:
            return
        await session.execute(
            text(
                "CREATE VIRTUAL TABLE IF NOT EXISTS repair_reference_chunk_fts "
                "USING fts5(id UNINDEXED, content, tokenize='trigram')"
            )
        )
        await session.execute(
            text('DELETE FROM repair_reference_chunk_fts WHERE id IN :chunk_ids').bindparams(
                bindparam('chunk_ids', expanding=True)
            ),
            {'chunk_ids': [chunk.id for chunk in chunks]},
        )
        await session.execute(
            text('INSERT INTO repair_reference_chunk_fts (id, content) VALUES (:id, :content)'),
            [{'id': chunk.id, 'content': chunk.content} for chunk in chunks],
        )
        await session.commit()

    @staticmethod
    async def _replace_sqlite_full_text(session: AsyncSession, chunks: list[RepairReferenceChunk]) -> None:
        if session.bind.dialect.name != 'sqlite':
            return
        await session.execute(
            text(
                "CREATE VIRTUAL TABLE IF NOT EXISTS repair_reference_chunk_fts "
                "USING fts5(id UNINDEXED, content, tokenize='trigram')"
            )
        )
        await session.execute(text('DELETE FROM repair_reference_chunk_fts'))
        if chunks:
            await session.execute(
                text('INSERT INTO repair_reference_chunk_fts (id, content) VALUES (:id, :content)'),
                [{'id': chunk.id, 'content': chunk.content} for chunk in chunks],
            )
        await session.commit()

    async def rebuild_chunks(
        self,
        chunk_size: int,
        chunk_overlap: int,
        extraction_config: dict,
        db: AsyncSession | None = None,
    ) -> list[RepairReferenceChunkModel]:
        now = int(time.time())
        async with get_async_db_context(db) as session:
            documents = (await session.execute(select(RepairReferenceDocument))).scalars().all()
            await session.execute(delete(RepairReferenceChunk))
            chunks = []
            for document in documents:
                document.extraction_config = extraction_config
                document.updated_at = now
                chunks.extend(
                    RepairReferenceChunk(
                        id=f'REFC-{uuid.uuid4().hex[:8].upper()}',
                        document_id=document.id,
                        chunk_index=index,
                        content=chunk,
                        chunk_metadata={
                            'document_type': document.document_type,
                            'file_id': document.file_id,
                            'source_name': document.source_name,
                            'pn_normalized': document.pn_normalized or [],
                            'product_type': document.product_type,
                            'failure_type': document.failure_type,
                            'plant': document.plant,
                            'version': document.version,
                        },
                        created_at=now,
                    )
                    for index, chunk in enumerate(
                        chunk_reference_content(document.content, chunk_size, chunk_overlap)
                    )
                )
            session.add_all(chunks)
            await session.commit()
            await self._replace_sqlite_full_text(session, chunks)
            return [RepairReferenceChunkModel.model_validate(chunk) for chunk in chunks]

    async def search_full_text(
        self,
        candidate_chunk_ids: list[str],
        query: str,
        limit: int,
        db: AsyncSession | None = None,
    ) -> list[RepairReferenceChunkModel]:
        """Run native FTS only after metadata filtering has supplied chunk IDs."""
        if not candidate_chunk_ids or not query.strip():
            return []
        async with get_async_db_context(db) as session:
            dialect = session.bind.dialect.name
            if dialect == 'sqlite':
                # Quoting the query makes it a phrase, not an FTS expression supplied by a user.
                phrase = '"' + query.replace('"', ' ') + '"'
                result = await session.execute(
                    text(
                        'SELECT c.id, c.document_id, c.chunk_index, c.content, c.metadata, c.created_at '
                        'FROM repair_reference_chunk_fts f '
                        'JOIN repair_reference_chunk c ON c.id = f.id '
                        'WHERE f.content MATCH :query AND c.id IN :candidate_ids '
                        'ORDER BY bm25(repair_reference_chunk_fts) LIMIT :limit'
                    ).bindparams(bindparam('candidate_ids', expanding=True)),
                    {'query': phrase, 'candidate_ids': candidate_chunk_ids, 'limit': limit},
                )
                return [self._chunk_model_from_row(row) for row in result]
            if dialect == 'postgresql':
                result = await session.execute(
                    text(
                        "SELECT id, document_id, chunk_index, content, metadata, created_at "
                        "FROM repair_reference_chunk "
                        "WHERE id IN :candidate_ids "
                        "AND to_tsvector('simple', content) @@ plainto_tsquery('simple', :query) "
                        "ORDER BY ts_rank(to_tsvector('simple', content), plainto_tsquery('simple', :query)) DESC "
                        "LIMIT :limit"
                    ).bindparams(bindparam('candidate_ids', expanding=True)),
                    {'candidate_ids': candidate_chunk_ids, 'query': query, 'limit': limit},
                )
                return [self._chunk_model_from_row(row) for row in result]
            return []

    async def list_documents(self, db: AsyncSession | None = None) -> list[RepairReferenceDocumentModel]:
        async with get_async_db_context(db) as session:
            result = await session.execute(
                select(RepairReferenceDocument).order_by(RepairReferenceDocument.updated_at.desc())
            )
            return [RepairReferenceDocumentModel.model_validate(document) for document in result.scalars().all()]

    async def list_chunks(self, db: AsyncSession | None = None) -> list[RepairReferenceChunkModel]:
        async with get_async_db_context(db) as session:
            result = await session.execute(
                select(RepairReferenceChunk).order_by(
                    RepairReferenceChunk.document_id, RepairReferenceChunk.chunk_index
                )
            )
            return [RepairReferenceChunkModel.model_validate(chunk) for chunk in result.scalars().all()]

    async def get_metadata_candidates(
        self,
        pn: str,
        product_family: str | None,
        product_type: str,
        failure_type: str | None,
        plant: str | None,
        db: AsyncSession | None = None,
    ) -> list[RepairReferenceChunkModel]:
        async with get_async_db_context(db) as session:
            stmt = select(RepairReferenceDocument).where(
                (RepairReferenceDocument.product_type.is_(None))
                | (RepairReferenceDocument.product_type == product_type)
            )
            if product_family:
                stmt = stmt.where(
                    (RepairReferenceDocument.product_family.is_(None))
                    | (RepairReferenceDocument.product_family == product_family)
                )
            else:
                stmt = stmt.where(RepairReferenceDocument.product_family.is_(None))
            if failure_type:
                stmt = stmt.where(
                    (RepairReferenceDocument.failure_type.is_(None))
                    | (RepairReferenceDocument.failure_type == failure_type)
                )
            else:
                stmt = stmt.where(RepairReferenceDocument.failure_type.is_(None))
            if plant:
                stmt = stmt.where((RepairReferenceDocument.plant.is_(None)) | (RepairReferenceDocument.plant == plant))
            else:
                stmt = stmt.where(RepairReferenceDocument.plant.is_(None))
            documents = (await session.execute(stmt)).scalars().all()
            normalized_pn = normalize_pn(pn)
            matching_documents = [
                document
                for document in documents
                if not document.pn_normalized or normalized_pn in document.pn_normalized
            ]
            if not matching_documents:
                return []
            document_ids = [document.id for document in matching_documents]
            chunks = await session.execute(
                select(RepairReferenceChunk)
                .where(RepairReferenceChunk.document_id.in_(document_ids))
                .order_by(RepairReferenceChunk.document_id, RepairReferenceChunk.chunk_index)
            )
            return [RepairReferenceChunkModel.model_validate(chunk) for chunk in chunks.scalars().all()]


RepairCases = RepairCasesTable()
RepairSOPs = RepairSOPsTable()
RepairAuditLogs = RepairAuditLogsTable()
RepairReferences = RepairReferencesTable()
