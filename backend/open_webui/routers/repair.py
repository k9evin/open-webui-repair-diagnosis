import asyncio
import hashlib
import json
import re
import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from langchain_core.documents import Document
from open_webui.config import RAG_EMBEDDING_CONTENT_PREFIX, RAG_EMBEDDING_QUERY_PREFIX
from open_webui.constants import ERROR_MESSAGES
from open_webui.models.config import Config
from open_webui.models.files import Files
from open_webui.models.repair import (
    RepairAuditLogs,
    RepairCaseForm,
    RepairCaseModel,
    RepairCases,
    RepairReferenceChunkModel,
    RepairReferenceDocumentForm,
    RepairReferences,
    RepairSOPForm,
    RepairSOPs,
)
from open_webui.retrieval.loaders.main import Loader
from open_webui.retrieval.utils import get_embedding_function, get_loader_config, get_reranking_function
from open_webui.retrieval.vector.async_client import ASYNC_VECTOR_DB_CLIENT
from open_webui.utils.auth import get_admin_user, get_verified_user
from pydantic import BaseModel, Field

router = APIRouter()
admin_router = APIRouter()
fa_documents_router = APIRouter()

FA_DOCUMENTS_CONFIG_KEY = 'repair.fa_documents.config'
FA_DOCUMENTS_COLLECTION = 'repair_documents'
DEFAULT_FA_DOCUMENTS_CONFIG = {
    'enabled': True,
    'full_text_enabled': True,
    'vector_enabled': True,
    'reranker_enabled': True,
    'content_extraction_engine': 'mineru',
    'chunk_size': 1200,
    'chunk_overlap': 120,
    'embedding_engine': 'openai',
    'embedding_model': 'Qwen/Qwen3-Embedding-8B',
    'reranking_engine': 'external',
    'reranking_model': 'Qwen/Qwen3-Reranker-4B',
    'candidate_limit': 20,
    'result_limit': 5,
    'rrf_k': 60,
}
FA_CONFIG_SNAPSHOT_KEYS = (
    'content_extraction_engine',
    'chunk_size',
    'chunk_overlap',
    'embedding_engine',
    'embedding_model',
    'reranking_engine',
    'reranking_model',
)


class RetrieveForm(BaseModel):
    pn: str
    sn: str
    product_type: str
    product_family: str | None = None
    plant: str
    failure_description: str
    failure_type: str | None = None


class ReviewForm(BaseModel):
    case_quality: str | None = None
    root_cause: str | None = None


class FADocumentsConfigForm(BaseModel):
    enabled: bool = True
    full_text_enabled: bool = True
    vector_enabled: bool = True
    reranker_enabled: bool = True
    content_extraction_engine: str = 'mineru'
    chunk_size: int = Field(default=1200, ge=200, le=8000)
    chunk_overlap: int = Field(default=120, ge=0, le=2000)
    embedding_engine: str = 'openai'
    embedding_model: str = 'Qwen/Qwen3-Embedding-8B'
    reranking_engine: str = 'external'
    reranking_model: str = 'Qwen/Qwen3-Reranker-4B'
    candidate_limit: int = Field(default=20, ge=1, le=100)
    result_limit: int = Field(default=5, ge=1, le=20)
    rrf_k: int = Field(default=60, ge=1, le=200)


async def _fa_documents_config() -> dict:
    saved = await Config.get(FA_DOCUMENTS_CONFIG_KEY, {})
    return {**DEFAULT_FA_DOCUMENTS_CONFIG, **(saved if isinstance(saved, dict) else {})}


async def _fa_embedding_function(request: Request, config: dict):
    settings = await Config.get_many(
        'rag.openai.api_base_url',
        'rag.openai.api_key',
        'rag.ollama.base_url',
        'rag.ollama.api_key',
        'rag.azure_openai.base_url',
        'rag.azure_openai.api_key',
        'rag.azure_openai.api_version',
        'rag.embedding_batch_size',
        'rag.enable_async_embedding',
        'rag.embedding_concurrent_requests',
    )
    engine = config['embedding_engine']
    if engine == 'openai':
        url, key = settings.get('rag.openai.api_base_url'), settings.get('rag.openai.api_key')
    elif engine == 'ollama':
        url, key = settings.get('rag.ollama.base_url'), settings.get('rag.ollama.api_key')
    elif engine == 'azure_openai':
        url, key = settings.get('rag.azure_openai.base_url'), settings.get('rag.azure_openai.api_key')
    else:
        url, key = '', ''
    return get_embedding_function(
        engine,
        config['embedding_model'],
        embedding_function=getattr(request.app.state, 'ef', None),
        url=url,
        key=key,
        embedding_batch_size=settings.get('rag.embedding_batch_size') or 1,
        azure_api_version=settings.get('rag.azure_openai.api_version'),
        enable_async=settings.get('rag.enable_async_embedding', True),
        concurrent_requests=settings.get('rag.embedding_concurrent_requests') or 0,
    )


async def _fa_reranking_function(request: Request, config: dict):
    settings = await Config.get_many(
        'rag.external_reranker_url', 'rag.external_reranker_api_key', 'rag.external_reranker_timeout'
    )
    if config['reranking_engine'] == 'external' and not settings.get('rag.external_reranker_url'):
        return None
    cache_key = (
        config['reranking_engine'],
        config['reranking_model'],
        settings.get('rag.external_reranker_url'),
        settings.get('rag.external_reranker_api_key'),
        settings.get('rag.external_reranker_timeout'),
    )
    if getattr(request.app.state, 'FA_RERANKING_KEY', None) != cache_key:
        from open_webui.routers.retrieval import get_rf

        request.app.state.FA_RERANKING_FUNCTION = get_reranking_function(
            config['reranking_engine'],
            config['reranking_model'],
            get_rf(*cache_key),
        )
        request.app.state.FA_RERANKING_KEY = cache_key
    return getattr(request.app.state, 'FA_RERANKING_FUNCTION', None)


def _config_hash(config: dict) -> str:
    return hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()


def _extraction_snapshot(config: dict) -> dict:
    return {key: config[key] for key in FA_CONFIG_SNAPSHOT_KEYS}


def _reference_response(chunk: RepairReferenceChunkModel, score: float) -> dict:
    metadata = chunk.chunk_metadata
    return {
        'reference_id': chunk.id,
        'document_id': chunk.document_id,
        'document_type': metadata.get('document_type'),
        'version': metadata.get('version'),
        'source_name': metadata.get('source_name'),
        'content': chunk.content,
        'score': round(score, 5),
        'label': '辅助指引',
        'disclaimer': '仅作 Work Requirements/debug 辅助指引，不构成已验证案例、根因或换件依据。',
    }


def _rrf_rank(
    full_text: list[RepairReferenceChunkModel],
    vectors: list[RepairReferenceChunkModel],
    rrf_k: int,
) -> list[tuple[RepairReferenceChunkModel, float]]:
    scores: dict[str, float] = {}
    chunks: dict[str, RepairReferenceChunkModel] = {}
    for result_set in (full_text, vectors):
        for rank, chunk in enumerate(result_set, start=1):
            chunks[chunk.id] = chunk
            scores[chunk.id] = scores.get(chunk.id, 0) + 1 / (rrf_k + rank)
    return sorted(
        ((chunks[chunk_id], score) for chunk_id, score in scores.items()),
        key=lambda item: item[1],
        reverse=True,
    )


async def _vector_reference_chunks(
    request: Request,
    user,
    candidate_chunks: list[RepairReferenceChunkModel],
    query: str,
    limit: int,
    config: dict,
) -> list[RepairReferenceChunkModel]:
    if not candidate_chunks:
        return []
    try:
        embedding = await (await _fa_embedding_function(request, config))(
            query, prefix=RAG_EMBEDDING_QUERY_PREFIX, user=user
        )
        result = await ASYNC_VECTOR_DB_CLIENT.search(
            collection_name=FA_DOCUMENTS_COLLECTION,
            vectors=[embedding],
            filter={'reference_chunk_id': {'$in': [chunk.id for chunk in candidate_chunks]}},
            limit=limit,
        )
        candidate_by_id = {chunk.id: chunk for chunk in candidate_chunks}
        ids = result.ids[0] if result and result.ids else []
        return [candidate_by_id[chunk_id] for chunk_id in ids if chunk_id in candidate_by_id]
    except Exception:
        # Vector configuration may deliberately be unavailable in an offline local setup.
        return []


async def _rerank_references(
    request: Request, user, query: str, ranked: list[tuple[RepairReferenceChunkModel, float]], config: dict
):
    if not ranked:
        return ranked
    try:
        reranker = await _fa_reranking_function(request, config)
        if not reranker:
            return ranked
        documents = [Document(page_content=chunk.content, metadata={'chunk_id': chunk.id}) for chunk, _ in ranked]
        scores = await asyncio.to_thread(reranker, query, documents, user=user)
        score_values = scores.tolist() if hasattr(scores, 'tolist') else scores
        reranked = sorted(zip(ranked, score_values), key=lambda item: item[1], reverse=True)
        return [(chunk, float(score)) for ((chunk, _), score) in reranked]
    except Exception:
        return ranked


async def retrieve_reference_guidance(request: Request, form_data: RetrieveForm, user) -> list[dict]:
    config = await _fa_documents_config()
    if not config['enabled']:
        return []
    # This is deliberately before FTS/vector calls; candidates are the only permitted search scope.
    candidates = await RepairReferences.get_metadata_candidates(
        form_data.pn,
        form_data.product_family,
        form_data.product_type,
        form_data.failure_type,
        form_data.plant,
    )
    if not candidates:
        return []
    full_text = (
        await RepairReferences.search_full_text(
            [chunk.id for chunk in candidates], form_data.failure_description, config['candidate_limit']
        )
        if config['full_text_enabled']
        else []
    )
    vectors = (
        await _vector_reference_chunks(
            request, user, candidates, form_data.failure_description, config['candidate_limit'], config
        )
        if config['vector_enabled']
        else []
    )
    ranked = _rrf_rank(full_text, vectors, config['rrf_k'])
    if config['reranker_enabled']:
        ranked = await _rerank_references(request, user, form_data.failure_description, ranked, config)
    return [_reference_response(chunk, score) for chunk, score in ranked[: config['result_limit']]]


def _keywords(value: str) -> set[str]:
    return {word for word in re.split(r'\W+', value.lower()) if len(word) > 1}


def _score_case(case: RepairCaseModel, form_data: RetrieveForm) -> float:
    query_terms = _keywords(form_data.failure_description)
    case_terms = _keywords(' '.join(filter(None, [case.failure_description_raw, case.repair_steps_normalized])))
    overlap = len(query_terms & case_terms)
    plant_bonus = 0.1 if case.plant and case.plant == form_data.plant else 0
    return round(overlap + plant_bonus, 3)


def _case_response(case: RepairCaseModel, score: float, match_scope: str) -> dict:
    return {
        'case_id': case.id,
        'score': score,
        'match_scope': match_scope,
        'pn': case.pn_raw,
        'product_type': case.product_type,
        'failure_type': case.failure_type,
        'failure_description': case.failure_description_raw,
        'repair_steps': case.repair_steps_normalized or case.repair_steps_raw,
        'test_result': case.test_result_raw,
        'replacement_part_pn': case.replacement_part_pn,
        'final_result': case.final_result or '未记录',
        'source_count': 1,
        'review_status': case.review_status,
    }


def _retrieval_context(cases: list[dict]) -> str:
    return '\n\n'.join(
        '\n'.join(
            [
                f"# 返修案例：{case['case_id']}",
                f"匹配范围：{case['match_scope']}",
                f"故障现象：{case['failure_description']}",
                f"检修步骤：{case['repair_steps'] or '未记录'}",
                f"测试结果：{case['test_result'] or '未记录'}",
                f"替换元器件：{case['replacement_part_pn'] or '未记录'}",
                f"最终结果：{case['final_result']}",
            ]
        )
        for case in cases
    )


@router.post('/retrieve')
async def retrieve_repair_cases(request: Request, form_data: RetrieveForm, user=Depends(get_verified_user)):
    # Metadata filtering is the trust boundary: all later scoring uses only these candidates.
    scope, candidates = await RepairCases.get_approved_candidates(
        form_data.pn, form_data.product_type, form_data.failure_type
    )
    ranked = sorted(
        (_case_response(case, _score_case(case, form_data), scope) for case in candidates),
        key=lambda case: case['score'],
        reverse=True,
    )
    sop = await RepairSOPs.find_for_retrieval(form_data.product_type, form_data.failure_type)
    references = await retrieve_reference_guidance(request, form_data, user)
    await RepairAuditLogs.record(
        user.id,
        'retrieve',
        payload={
            'scope': scope,
            'pn': form_data.pn,
            'product_type': form_data.product_type,
            'candidate_case_ids': [case['case_id'] for case in ranked],
            'reference_ids': [reference['reference_id'] for reference in references],
        },
    )
    if scope == 'exact_pn':
        limitations = '仅返回同 PN 已审核案例。'
    elif scope == 'same_product_type_reference':
        limitations = '仅作为同产品类型参考案例。'
    else:
        limitations = '没有可靠历史案例；请依 SOP 执行并升级工程师。'
    return {
        'scope': scope,
        'sop': sop.model_dump() if sop else None,
        'cases': ranked,
        'references': references,
        'retrieval_context': _retrieval_context(ranked),
        'limitations': limitations,
    }


@router.post('/feedback')
async def submit_repair_feedback(form_data: RepairCaseForm, user=Depends(get_verified_user)):
    case = await RepairCases.create_case(form_data, user.id)
    await RepairAuditLogs.record(user.id, 'feedback_submitted', case.id)
    return {'case_id': case.id, 'review_status': case.review_status}


@router.get('/sops/{product_type}')
async def get_repair_sop(product_type: str, failure_type: str | None = None, user=Depends(get_verified_user)):
    sop = await RepairSOPs.find_for_retrieval(product_type, failure_type)
    if not sop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ERROR_MESSAGES.NOT_FOUND)
    return sop


async def _index_reference_chunks(
    request: Request, user, chunks: list[RepairReferenceChunkModel], config: dict
) -> None:
    if not chunks:
        return
    embedding_function = await _fa_embedding_function(request, config)
    embeddings = await embedding_function(
        [chunk.content for chunk in chunks], prefix=RAG_EMBEDDING_CONTENT_PREFIX, user=user
    )
    if not isinstance(embeddings, list) or len(embeddings) != len(chunks):
        raise ValueError('Embedding 服务未返回每个返修辅助文档分块的向量。')
    await ASYNC_VECTOR_DB_CLIENT.upsert(
        collection_name=FA_DOCUMENTS_COLLECTION,
        items=[
            {
                'id': chunk.id,
                'text': chunk.content,
                'vector': embedding,
                'metadata': {
                    **chunk.chunk_metadata,
                    'reference_chunk_id': chunk.id,
                    'document_id': chunk.document_id,
                },
            }
            for chunk, embedding in zip(chunks, embeddings)
        ],
    )


def _index_status_response(index) -> dict:
    return {
        'status': index.status if index else 'stale',
        'config_hash': index.config_hash if index else None,
        'indexed_at': index.indexed_at if index else None,
    }


@fa_documents_router.get('/config')
async def get_fa_documents_config(user=Depends(get_admin_user)):
    return {**await _fa_documents_config(), 'index': _index_status_response(await RepairReferences.get_index_status())}


@fa_documents_router.put('/config')
async def update_fa_documents_config(form_data: FADocumentsConfigForm, user=Depends(get_admin_user)):
    config = form_data.model_dump()
    if not config['full_text_enabled'] and not config['vector_enabled']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='至少启用全文检索或向量检索。')
    if config['chunk_overlap'] >= config['chunk_size']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='chunk overlap 必须小于 chunk size。')
    await Config.upsert({FA_DOCUMENTS_CONFIG_KEY: config})
    index = await RepairReferences.set_index_status(_config_hash(config), 'stale')
    await RepairAuditLogs.record(user.id, 'fa_documents_config_updated', payload={'config_hash': index.config_hash})
    return {**config, 'index': _index_status_response(index)}


@fa_documents_router.get('/references')
async def list_fa_reference_documents(user=Depends(get_admin_user)):
    return {'items': [document.model_dump() for document in await RepairReferences.list_documents()]}


@fa_documents_router.post('/references')
async def import_fa_reference_document(
    request: Request, form_data: RepairReferenceDocumentForm, user=Depends(get_admin_user)
):
    if form_data.document_type not in {'work_requirement', 'debug_guide'}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='document_type 必须是 work_requirement 或 debug_guide。',
        )
    file = await Files.get_file_by_id(form_data.file_id)
    if not file or not file.path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ERROR_MESSAGES.NOT_FOUND)
    extension = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if extension not in {'pdf', 'docx', 'md', 'markdown', 'txt'}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='仅支持 PDF、DOCX、Markdown 或文本文件。')
    config = await _fa_documents_config()
    loader_config = await get_loader_config()
    loader = Loader(engine=config['content_extraction_engine'], **loader_config)
    try:
        documents = await loader.aload(file.filename, (file.meta or {}).get('content_type', ''), file.path)
        content = '\n\n'.join(document.page_content.strip() for document in documents if document.page_content.strip())
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f'文档提取失败：{exc}') from exc
    if not content:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='文档没有可提取的文本内容。')
    extraction_config = _extraction_snapshot(config)
    try:
        document, chunks = await RepairReferences.create_document(
            form_data,
            file.filename,
            content,
            user.id,
            extraction_config,
            config['chunk_size'],
            config['chunk_overlap'],
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'该文件无法重复导入：{exc}') from exc
    index = await RepairReferences.set_index_status(_config_hash(config), 'stale')
    vector_error = None
    if config['vector_enabled']:
        try:
            await _index_reference_chunks(request, user, chunks, config)
            index = await RepairReferences.set_index_status(
                _config_hash(config), 'ready', indexed_at=document.updated_at
            )
        except Exception as exc:
            # Keep the extracted, auditable document and let the admin rebuild after configuring the model.
            vector_error = str(exc)
    await RepairAuditLogs.record(
        user.id,
        'fa_reference_imported',
        payload={'document_id': document.id, 'document_type': document.document_type, 'chunk_count': len(chunks)},
    )
    return {
        'document': document.model_dump(),
        'chunk_count': len(chunks),
        'index': _index_status_response(index),
        'vector_error': vector_error,
    }


@fa_documents_router.post('/rebuild')
async def rebuild_fa_documents_index(request: Request, user=Depends(get_admin_user)):
    config = await _fa_documents_config()
    try:
        chunks = await RepairReferences.rebuild_chunks(
            config['chunk_size'], config['chunk_overlap'], _extraction_snapshot(config)
        )
        if config['vector_enabled']:
            if await ASYNC_VECTOR_DB_CLIENT.has_collection(FA_DOCUMENTS_COLLECTION):
                await ASYNC_VECTOR_DB_CLIENT.delete_collection(FA_DOCUMENTS_COLLECTION)
            await _index_reference_chunks(request, user, chunks, config)
        index = await RepairReferences.set_index_status(_config_hash(config), 'ready', indexed_at=int(time.time()))
    except Exception as exc:
        index = await RepairReferences.set_index_status(_config_hash(config), 'stale')
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f'返修索引重建失败：{exc}'
        ) from exc
    await RepairAuditLogs.record(user.id, 'fa_documents_rebuilt', payload={'chunk_count': len(chunks)})
    return {'collection': FA_DOCUMENTS_COLLECTION, 'chunk_count': len(chunks), 'index': _index_status_response(index)}


@admin_router.get('')
async def list_repair_cases(review_status: str | None = None, user=Depends(get_admin_user)):
    return {'items': [case.model_dump() for case in await RepairCases.list_cases(review_status)]}


async def _review_case(case_id: str, review_status: str, form_data: ReviewForm, user) -> RepairCaseModel:
    case = await RepairCases.review_case(
        case_id,
        review_status,
        user.id,
        case_quality=form_data.case_quality,
        root_cause=form_data.root_cause,
    )
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ERROR_MESSAGES.NOT_FOUND)
    await RepairAuditLogs.record(user.id, f'case_{review_status}', case_id)
    return case


@admin_router.post('/{case_id}/approve')
async def approve_repair_case(case_id: str, form_data: ReviewForm, user=Depends(get_admin_user)):
    return await _review_case(case_id, 'approved', form_data, user)


@admin_router.post('/{case_id}/reject')
async def reject_repair_case(case_id: str, form_data: ReviewForm, user=Depends(get_admin_user)):
    return await _review_case(case_id, 'rejected', form_data, user)


@admin_router.post('/sops')
async def create_repair_sop(form_data: RepairSOPForm, user=Depends(get_admin_user)):
    sop = await RepairSOPs.create(form_data)
    await RepairAuditLogs.record(user.id, 'sop_created', payload={'sop_id': sop.id})
    return sop


@admin_router.post('/{case_id}/reindex')
async def reindex_repair_case(case_id: str, user=Depends(get_admin_user)):
    case = await RepairCases.get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ERROR_MESSAGES.NOT_FOUND)
    await RepairAuditLogs.record(user.id, 'reindex_requested', case_id)
    return {'case_id': case_id, 'status': 'queued'}
