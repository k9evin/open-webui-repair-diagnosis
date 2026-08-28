<script lang="ts">
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { listRepairCases, reviewRepairCase } from '$lib/apis/repair/adminCases';
	import Badge from '$lib/components/common/Badge.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	let items: any[] = [];
	let status = 'pending';
	let loading = true;
	const load = async () => {
		loading = true;
		try {
			items = (await listRepairCases(localStorage.token, status)).items ?? [];
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			loading = false;
		}
	};
	const review = async (id: string, action: 'approve' | 'reject') => {
		try {
			await reviewRepairCase(localStorage.token, id, action);
			toast.success(action === 'approve' ? '案例已批准。' : '案例已拒绝。');
			await load();
		} catch (error) {
			toast.error(`${error}`);
		}
	};
	onMount(load);
</script>

<svelte:head><title>返修案例审核</title></svelte:head>
<div class="mx-auto w-full max-w-6xl p-6">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-xl font-semibold">返修案例审核</h1>
			<p class="mt-1 text-sm text-gray-500">
				只有批准案例会进入诊断检索；原始字段和来源行号始终保留。
			</p>
		</div>
		<select bind:value={status} on:change={load} class="input-field"
			><option value="pending">待审核</option><option value="approved">已批准</option><option
				value="rejected">已拒绝</option
			></select
		>
	</div>
	{#if loading}<div class="mt-8"><Spinner className="size-5" /></div>{:else if !items.length}<p
			class="mt-8 rounded-xl border border-dashed p-8 text-center text-sm text-gray-500"
		>
			暂无案例。
		</p>{:else}<div class="mt-5 space-y-3">
			{#each items as item}<article
					class="rounded-2xl border border-gray-100 bg-white p-4 dark:border-gray-850 dark:bg-gray-900"
				>
					<div class="flex justify-between">
						<div class="flex items-center gap-2 font-medium">
							{item.id} · {item.pn_raw}<Badge
								type={status === 'approved'
									? 'success'
									: status === 'rejected'
										? 'error'
										: 'warning'}
								content={status}
							/>
						</div>
						<span class="text-xs text-gray-500"
							>源文件 {item.source_file ?? '未记录'} / 第 {item.source_row_id ?? '?'} 行</span
						>
					</div>
					<p class="mt-2 text-sm">{item.failure_description_raw}</p>
					<div class="mt-2 text-xs text-gray-500">
						产品 {item.product_type} · 失效 {item.failure_type ?? '未填写'} · 质量 {item.case_quality}
					</div>
					{#if status === 'pending'}<div class="mt-3 flex gap-2">
							<button
								class="rounded-lg bg-gray-900 px-3 py-1.5 text-xs text-white dark:bg-white dark:text-gray-900"
								on:click={() => review(item.id, 'approve')}>批准</button
							><button
								class="rounded-lg border px-3 py-1.5 text-xs"
								on:click={() => review(item.id, 'reject')}>拒绝</button
							>
						</div>{/if}
				</article>{/each}
		</div>{/if}
</div>
