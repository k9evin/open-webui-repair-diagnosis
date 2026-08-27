import { WEBUI_BASE_URL } from '$lib/constants';

export type RepairQuery = {
	pn: string;
	sn: string;
	product_type: string;
	plant: string;
	failure_description: string;
	failure_type?: string;
};

export type RepairCase = {
	case_id: string;
	score: number;
	match_scope: string;
	pn: string;
	product_type: string;
	failure_type?: string;
	failure_description: string;
	repair_steps?: string;
	test_result?: string;
	replacement_part_pn?: string;
	final_result: string;
	source_count: number;
};

export type RepairSop = {
	id: string;
	name: string;
	version: string;
	content: string;
	product_type: string;
	failure_type?: string;
};

export type RepairReference = {
	id: string;
	document_type: 'work_requirement' | 'debug_guide';
	source_name: string;
	content: string;
	label: string;
};

export type RepairRetrieveResponse = {
	scope: 'exact_pn' | 'same_product_type_reference' | 'no_reliable_case';
	sop?: RepairSop | null;
	cases: RepairCase[];
	references?: RepairReference[];
	retrieval_context: string;
	limitations: string;
};

const request = async <T>(token: string, path: string, body: object): Promise<T> => {
	const response = await fetch(`${WEBUI_BASE_URL}/api/repair${path}`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify(body)
	});

	if (!response.ok) {
		const error = await response.json().catch(() => ({}));
		throw error.detail ?? '请求失败，请稍后重试。';
	}

	return response.json() as Promise<T>;
};

export const retrieveRepairDiagnosis = (token: string, query: RepairQuery) =>
	request<RepairRetrieveResponse>(token, '/retrieve', query);

export const submitRepairFeedback = (token: string, feedback: object) =>
	request<{ case_id: string; review_status: string }>(token, '/feedback', feedback);
