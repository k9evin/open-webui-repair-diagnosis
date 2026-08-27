import { WEBUI_BASE_URL } from '$lib/constants';

export type FADocumentsConfig = {
	enabled: boolean;
	full_text_enabled: boolean;
	vector_enabled: boolean;
	reranker_enabled: boolean;
	content_extraction_engine: string;
	chunk_size: number;
	chunk_overlap: number;
	embedding_engine: string;
	embedding_model: string;
	reranking_engine: string;
	reranking_model: string;
	candidate_limit: number;
	result_limit: number;
	rrf_k: number;
	index: { status: 'ready' | 'stale'; config_hash?: string | null; indexed_at?: number | null };
};

const request = async <T>(token: string, path: string, options: RequestInit = {}): Promise<T> => {
	const response = await fetch(`${WEBUI_BASE_URL}/api/admin/fa-documents${path}`, {
		...options,
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`,
			...options.headers
		}
	});
	if (!response.ok) {
		const error = await response.json().catch(() => ({}));
		throw error.detail ?? '请求失败，请稍后重试。';
	}
	return response.json() as Promise<T>;
};

export const getFADocumentsConfig = (token: string) => request<FADocumentsConfig>(token, '/config');

export const updateFADocumentsConfig = (token: string, config: Omit<FADocumentsConfig, 'index'>) =>
	request<FADocumentsConfig>(token, '/config', { method: 'PUT', body: JSON.stringify(config) });

export const rebuildFADocumentsIndex = (token: string) =>
	request<{ collection: string; chunk_count: number; index: FADocumentsConfig['index'] }>(
		token,
		'/rebuild',
		{ method: 'POST' }
	);
