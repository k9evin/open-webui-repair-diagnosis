<script lang="ts">
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import Switch from '$lib/components/common/Switch.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import SettingsSelect from '$lib/components/common/SettingsSelect.svelte';
	import AdminSettingField from './AdminSettingField.svelte';
	import AdminSettingRow from './AdminSettingRow.svelte';
	import AdminSettingSection from './AdminSettingSection.svelte';
	import {
		getFADocumentsConfig,
		rebuildFADocumentsIndex,
		updateFADocumentsConfig,
		type FADocumentsConfig
	} from '$lib/apis/repair/admin';

	type ConfigForm = Omit<FADocumentsConfig, 'index'>;
	let config: ConfigForm | null = null;
	let index: FADocumentsConfig['index'] | null = null;
	let loading = true;
	let saving = false;
	let rebuilding = false;

	const inputClass =
		'w-28 h-7 rounded-lg border border-gray-100/50 bg-gray-50/40 px-2 text-xs text-gray-700 outline-hidden focus:border-blue-400 dark:border-white/[0.04] dark:bg-white/[0.03] dark:text-gray-300 dark:focus:border-blue-500';

	const load = async () => {
		loading = true;
		try {
			const response = await getFADocumentsConfig(localStorage.token);
			const { index: nextIndex, ...nextConfig } = response;
			config = nextConfig;
			index = nextIndex;
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			loading = false;
		}
	};

	const save = async () => {
		if (!config) return;
		if (!config.full_text_enabled && !config.vector_enabled) {
			toast.error('至少启用全文检索或向量检索。');
			return;
		}
		if (config.chunk_overlap >= config.chunk_size) {
			toast.error('Chunk overlap 必须小于 chunk size。');
			return;
		}
		saving = true;
		try {
			const response = await updateFADocumentsConfig(localStorage.token, config);
			const { index: nextIndex, ...nextConfig } = response;
			config = nextConfig;
			index = nextIndex;
			toast.success('FA Documents 设置已保存，返修索引已标记为过期。');
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			saving = false;
		}
	};

	const rebuild = async () => {
		rebuilding = true;
		try {
			const response = await rebuildFADocumentsIndex(localStorage.token);
			index = response.index;
			toast.success(`返修专用索引已重建（${response.chunk_count} 个分块）。`);
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			rebuilding = false;
		}
	};

	onMount(load);
</script>

{#if loading || !config}
	<div class="flex min-h-48 items-center justify-center"><Spinner className="size-5" /></div>
{:else}
	<div class="space-y-5">
		<p class="text-sm text-gray-500">
			独立管理返修辅助文档。此处配置不会修改普通 Documents、知识库或 memory 向量。
		</p>

		<AdminSettingSection title="返修检索">
			<AdminSettingRow
				label="启用 FA Documents"
				description="关闭后诊断仅使用已审核案例和 SOP。"
				let:labelId
				><Switch bind:state={config.enabled} ariaLabelledbyId={labelId} /></AdminSettingRow
			>
			<AdminSettingRow
				label="全文检索"
				description="仅在 metadata 预筛出的返修辅助文档分块中执行。"
				let:labelId
				><Switch
					bind:state={config.full_text_enabled}
					ariaLabelledbyId={labelId}
				/></AdminSettingRow
			>
			<AdminSettingRow
				label="向量检索"
				description="使用专属 repair_documents collection，不触碰普通 RAG。"
				let:labelId
				><Switch bind:state={config.vector_enabled} ariaLabelledbyId={labelId} /></AdminSettingRow
			>
			<AdminSettingRow label="Reranking" description="只对混合检索的候选结果重新排序。" let:labelId
				><Switch bind:state={config.reranker_enabled} ariaLabelledbyId={labelId} /></AdminSettingRow
			>
		</AdminSettingSection>

		<AdminSettingSection title="提取与分块">
			<AdminSettingRow label="内容提取引擎"
				><SettingsSelect bind:value={config.content_extraction_engine}
					><option value="mineru">MinerU</option><option value="">默认 Loader</option
					></SettingsSelect
				></AdminSettingRow
			>
			<AdminSettingRow label="Chunk size"
				><input
					class={inputClass}
					type="number"
					min="100"
					max="8000"
					bind:value={config.chunk_size}
				/></AdminSettingRow
			>
			<AdminSettingRow label="Chunk overlap"
				><input
					class={inputClass}
					type="number"
					min="0"
					max="4000"
					bind:value={config.chunk_overlap}
				/></AdminSettingRow
			>
		</AdminSettingSection>

		<AdminSettingSection title="模型与融合">
			<AdminSettingField label="Embedding 引擎"
				><SettingsSelect bind:value={config.embedding_engine}
					><option value="openai">OpenAI-compatible</option><option value="ollama">Ollama</option
					><option value="azure_openai">Azure OpenAI</option></SettingsSelect
				></AdminSettingField
			>
			<AdminSettingField label="Embedding 模型"
				><input
					class="{inputClass} w-full"
					bind:value={config.embedding_model}
				/></AdminSettingField
			>
			<AdminSettingField label="Reranker 引擎"
				><SettingsSelect bind:value={config.reranking_engine}
					><option value="external">External</option><option value="">禁用外部调用</option
					></SettingsSelect
				></AdminSettingField
			>
			<AdminSettingField label="Reranker 模型"
				><input
					class="{inputClass} w-full"
					bind:value={config.reranking_model}
				/></AdminSettingField
			>
			<div class="grid grid-cols-3 gap-3">
				<AdminSettingField label="候选数"
					><input
						class="{inputClass} w-full"
						type="number"
						min="1"
						max="50"
						bind:value={config.candidate_limit}
					/></AdminSettingField
				><AdminSettingField label="返回数"
					><input
						class="{inputClass} w-full"
						type="number"
						min="1"
						max="20"
						bind:value={config.result_limit}
					/></AdminSettingField
				><AdminSettingField label="RRF k"
					><input
						class="{inputClass} w-full"
						type="number"
						min="1"
						max="200"
						bind:value={config.rrf_k}
					/></AdminSettingField
				>
			</div>
		</AdminSettingSection>

		<AdminSettingSection title="返修索引">
			<div
				class="rounded-lg bg-gray-50 px-3 py-2 text-xs text-gray-600 dark:bg-white/[0.03] dark:text-gray-400"
			>
				状态：<span class={index?.status === 'ready' ? 'text-emerald-600' : 'text-amber-600'}
					>{index?.status === 'ready' ? '就绪' : '过期，需重建'}</span
				>{#if index?.indexed_at}
					· 上次重建：{new Date(index.indexed_at * 1000).toLocaleString()}{/if}
			</div>
			<button
				class="mt-2 rounded-lg border border-gray-200 px-3 py-1.5 text-xs dark:border-gray-700 disabled:opacity-50"
				on:click={rebuild}
				disabled={rebuilding}>{rebuilding ? '正在重建…' : '仅重建返修索引'}</button
			>
		</AdminSettingSection>

		<div class="flex justify-end">
			<button
				class="rounded-lg bg-gray-900 px-4 py-2 text-xs font-medium text-white dark:bg-white dark:text-gray-900 disabled:opacity-50"
				on:click={save}
				disabled={saving}>{saving ? '正在保存…' : '保存 FA Documents 设置'}</button
			>
		</div>
	</div>
{/if}
