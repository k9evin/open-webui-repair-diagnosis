<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { uploadFile } from '$lib/apis/files';
	import { importRepairCases, previewRepairCases } from '$lib/apis/repair/knowledge';

	let selected: File | null = null;
	let preview: any = null;
	let previewFileId = '';
	let loading = false;
	const selectFile = (event: Event) => {
		selected = (event.currentTarget as HTMLInputElement).files?.[0] ?? null;
		preview = null;
	};
	const runPreview = async () => {
		if (!selected) return;
		loading = true;
		try {
			const file = await uploadFile(
				localStorage.token,
				selected,
				{ repair_upload: true },
				false,
				false
			);
			previewFileId = file.id;
			preview = await previewRepairCases(localStorage.token, file.id);
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			loading = false;
		}
	};
	const runImport = async () => {
		if (!preview || !selected) return;
		loading = true;
		try {
			const result = await importRepairCases(localStorage.token, previewFileId);
			toast.success(`已导入 ${result.imported} 条，待管理员审核。`);
			preview = null;
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			loading = false;
		}
	};
</script>

<svelte:head><title>FA Knowledge Base</title></svelte:head>
<div class="mx-auto w-full max-w-5xl p-6">
	<h1 class="text-xl font-semibold">FA Knowledge Base</h1>
	<p class="mt-1 text-sm text-gray-500">
		返修案例与辅助文档独立上传区，不使用普通 Knowledge Base。
	</p>
	<div
		class="mt-6 rounded-2xl border border-gray-100 bg-white p-5 dark:border-gray-850 dark:bg-gray-900"
	>
		<h2 class="font-medium">导入返修案例 XLSX</h2>
		<input class="mt-4 block text-sm" type="file" accept=".xlsx" on:change={selectFile} />
		<p class="mt-2 text-xs text-gray-500">
			支持预览失败行；导入后案例默认为待审核，不会直接进入诊断。
		</p>
		<button
			class="mt-4 rounded-xl bg-gray-900 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-white dark:text-gray-900"
			on:click={runPreview}
			disabled={!selected || loading}>{loading ? '处理中…' : '预览导入'}</button
		>
		{#if preview}<div class="mt-5 rounded-xl bg-gray-50 p-4 text-sm dark:bg-gray-850">
				<div>文件：{preview.file_name}</div>
				<div class="mt-1">
					总行数 {preview.total_rows} · 可导入 {preview.valid_rows} · 失败 {preview.failed_rows}
				</div>
				<pre class="mt-3 max-h-52 overflow-auto text-xs">{JSON.stringify(
						preview.preview,
						null,
						2
					)}</pre>
				<button
					class="mt-3 rounded-xl border border-gray-300 px-4 py-2 text-sm dark:border-gray-700"
					on:click={runImport}
					disabled={loading}>确认导入</button
				>
			</div>{/if}
	</div>
</div>
