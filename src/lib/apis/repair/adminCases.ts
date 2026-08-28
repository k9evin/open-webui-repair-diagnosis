import { WEBUI_BASE_URL } from '$lib/constants';
const call = async (token: string, path: string, body?: object) => {
	const response = await fetch(`${WEBUI_BASE_URL}/api/admin/repair-cases${path}`, {
		method: body ? 'POST' : 'GET',
		headers: {
			Accept: 'application/json',
			...(body ? { 'Content-Type': 'application/json' } : {}),
			authorization: `Bearer ${token}`
		},
		...(body ? { body: JSON.stringify(body) } : {})
	});
	if (!response.ok) throw (await response.json().catch(() => ({}))).detail ?? '请求失败';
	return response.json();
};
export const listRepairCases = (token: string, status = 'pending') =>
	call(token, `?review_status=${status}`);
export const reviewRepairCase = (token: string, id: string, action: 'approve' | 'reject') =>
	call(token, `/${id}/${action}`, { case_quality: action === 'approve' ? 'A' : 'D' });
