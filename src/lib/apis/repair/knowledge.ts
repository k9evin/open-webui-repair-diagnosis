import { WEBUI_BASE_URL } from '$lib/constants';

const request = async (token: string, path: string, body: object) => {
	const response = await fetch(`${WEBUI_BASE_URL}/api/admin/fa-documents${path}`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify(body)
	});
	if (!response.ok) throw (await response.json().catch(() => ({}))).detail ?? '请求失败';
	return response.json();
};
export const previewRepairCases = (token: string, file_id: string) =>
	request(token, '/cases/preview', { file_id });
export const importRepairCases = (token: string, file_id: string) =>
	request(token, '/cases/import', { file_id });
