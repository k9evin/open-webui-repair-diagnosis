import re

from fastapi import APIRouter, Depends, HTTPException, status
from open_webui.constants import ERROR_MESSAGES
from open_webui.models.repair import (
    RepairAuditLogs,
    RepairCaseForm,
    RepairCaseModel,
    RepairCases,
    RepairSOPForm,
    RepairSOPs,
)
from open_webui.utils.auth import get_admin_user, get_verified_user
from pydantic import BaseModel

router = APIRouter()
admin_router = APIRouter()


class RetrieveForm(BaseModel):
    pn: str
    sn: str
    product_type: str
    plant: str
    failure_description: str
    failure_type: str | None = None


class ReviewForm(BaseModel):
    case_quality: str | None = None
    root_cause: str | None = None


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
async def retrieve_repair_cases(form_data: RetrieveForm, user=Depends(get_verified_user)):
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
    await RepairAuditLogs.record(
        user.id,
        'retrieve',
        payload={
            'scope': scope,
            'pn': form_data.pn,
            'product_type': form_data.product_type,
            'candidate_case_ids': [case['case_id'] for case in ranked],
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
