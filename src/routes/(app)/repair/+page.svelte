<script lang="ts">
	import { toast } from 'svelte-sonner';
	import Modal from '$lib/components/common/Modal.svelte';
	import {
		retrieveRepairDiagnosis,
		submitRepairFeedback,
		type RepairQuery,
		type RepairRetrieveResponse
	} from '$lib/apis/repair';

	let query: RepairQuery = {
		pn: '',
		sn: '',
		product_type: '',
		plant: '',
		failure_description: '',
		failure_type: ''
	};
	let result: RepairRetrieveResponse | null = null;
	let loading = false;
	let error = '';
	let showFeedback = false;
	let feedback = {
		measurement_status: 'not_measured',
		final_result: '',
		replacement_part_pn: '',
		repair_steps: '',
		test_result: ''
	};

	const requiredFields: (keyof RepairQuery)[] = [
		'pn',
		'sn',
		'product_type',
		'plant',
		'failure_description'
	];

	const maskSn = (sn: string) => (sn.length <= 4 ? '****' : `${sn.slice(0, 2)}****${sn.slice(-2)}`);

	const diagnose = async () => {
		if (requiredFields.some((field) => !query[field]?.trim())) {
			error = '请填写 PN、SN、产品类型、分厂和故障描述。';
			return;
		}

		loading = true;
		error = '';
		try {
			result = await retrieveRepairDiagnosis(localStorage.token, query);
		} catch (err) {
			error = `${err}`;
		} finally {
			loading = false;
		}
	};

	const submitFeedback = async () => {
		if (!feedback.final_result.trim()) {
			toast.error('请填写最终结果。');
			return;
		}

		try {
			await submitRepairFeedback(localStorage.token, { ...query, ...feedback });
			showFeedback = false;
			toast.success('反馈已提交，等待工程审核。');
		} catch (err) {
			toast.error(`${err}`);
		}
	};
</script>

<svelte:head><title>返修诊断</title></svelte:head>

<div class="mx-auto w-full max-w-7xl p-4 md:p-8">
	<div class="mb-6">
		<h1 class="text-xl font-semibold">返修诊断</h1>
		<p class="mt-1 text-sm text-gray-500">
			历史案例仅作参考；请遵循适用 SOP，并在不确定时升级工程师。
		</p>
	</div>

	<div class="grid gap-4 xl:grid-cols-[minmax(18rem,0.8fr)_minmax(20rem,1fr)_minmax(18rem,0.9fr)]">
		<form
			class="rounded-2xl border border-gray-100 bg-white p-4 dark:border-gray-850 dark:bg-gray-900"
			on:submit|preventDefault={diagnose}
		>
			<h2 class="mb-4 font-medium">故障信息</h2>
			<div class="space-y-3 text-sm">
				<label class="block"
					>PN <input
						bind:value={query.pn}
						required
						class="input-field mt-1 w-full"
						placeholder="例如 PCBA-001"
					/></label
				>
				<label class="block"
					>SN <input
						bind:value={query.sn}
						required
						class="input-field mt-1 w-full"
						placeholder="序列号"
					/></label
				>
				<label class="block"
					>产品类型 <input
						bind:value={query.product_type}
						required
						class="input-field mt-1 w-full"
						placeholder="例如 PCBA"
					/></label
				>
				<label class="block"
					>分厂 <input
						bind:value={query.plant}
						required
						class="input-field mt-1 w-full"
						placeholder="例如 SZ-A"
					/></label
				>
				<label class="block"
					>失效类型（可选）<input
						bind:value={query.failure_type}
						class="input-field mt-1 w-full"
					/></label
				>
				<label class="block"
					>故障描述 <textarea
						bind:value={query.failure_description}
						required
						rows="6"
						class="input-field mt-1 w-full"
						placeholder="请说明现象、测试条件及已确认信息。"
					></textarea></label
				>
			</div>
			{#if error}<p class="mt-3 text-sm text-red-600">{error}</p>{/if}
			<button
				class="mt-4 w-full rounded-xl bg-gray-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-white dark:text-gray-900"
				disabled={loading}
				type="submit">{loading ? '正在诊断…' : '开始诊断'}</button
			>
		</form>

		<section
			class="min-h-96 rounded-2xl border border-gray-100 bg-white p-4 dark:border-gray-850 dark:bg-gray-900"
		>
			<h2 class="font-medium">诊断建议</h2>
			{#if !result}
				<p class="mt-4 text-sm text-gray-500">填写信息后将按元数据范围检索已审核案例和辅助文档。</p>
			{:else}
				<div class="mt-4 rounded-xl bg-gray-50 p-3 text-sm dark:bg-gray-850">
					<div class="font-medium">查询 SN：{maskSn(query.sn)}</div>
					<div class="mt-1 text-gray-500">{result.limitations}</div>
				</div>
				{#if result.sop}
					<article class="mt-4 rounded-xl border border-blue-100 p-3 text-sm dark:border-blue-900">
						<div class="font-medium">
							SOP · {result.sop.name} <span class="text-gray-500">{result.sop.version}</span>
						</div>
						<p class="mt-2 whitespace-pre-wrap text-gray-700 dark:text-gray-300">
							{result.sop.content}
						</p>
					</article>
				{/if}
				{#if result.references?.length}
					<div class="mt-4 space-y-2">
						<h3 class="text-sm font-medium">辅助指引（非案例证据）</h3>
						{#each result.references as reference}
							<article class="rounded-xl border border-amber-100 p-3 text-sm dark:border-amber-900">
								<div class="font-medium">{reference.label} · {reference.source_name}</div>
								<p class="mt-1 whitespace-pre-wrap text-gray-600 dark:text-gray-300">
									{reference.content}
								</p>
							</article>
						{/each}
					</div>
				{/if}
			{/if}
		</section>

		<section
			class="rounded-2xl border border-gray-100 bg-white p-4 dark:border-gray-850 dark:bg-gray-900"
		>
			<h2 class="font-medium">历史案例</h2>
			{#if result?.cases?.length}
				<div class="mt-4 space-y-3">
					{#each result.cases as repairCase}
						<article class="rounded-xl border border-gray-100 p-3 text-sm dark:border-gray-850">
							<div class="flex items-center justify-between gap-2">
								<span class="font-medium">{repairCase.case_id}</span><span
									class="text-xs text-gray-500"
									>{repairCase.match_scope === 'exact_pn' ? '同 PN 已审核' : '同产品类型参考'}</span
								>
							</div>
							<dl class="mt-3 space-y-2 text-gray-600 dark:text-gray-300">
								<div>
									<dt class="text-xs text-gray-500">故障现象</dt>
									<dd>{repairCase.failure_description}</dd>
								</div>
								<div>
									<dt class="text-xs text-gray-500">检修步骤</dt>
									<dd>{repairCase.repair_steps ?? '未记录'}</dd>
								</div>
								<div>
									<dt class="text-xs text-gray-500">测试结果</dt>
									<dd>{repairCase.test_result ?? '未记录'}</dd>
								</div>
								<div>
									<dt class="text-xs text-gray-500">换件 PN / 最终结果</dt>
									<dd>{repairCase.replacement_part_pn ?? '未换件'} / {repairCase.final_result}</dd>
								</div>
							</dl>
						</article>
					{/each}
				</div>
			{:else if result}
				<p class="mt-4 text-sm text-gray-500">没有可用的已审核历史案例。</p>
			{/if}
			{#if result}<button
					class="mt-4 w-full rounded-xl border border-gray-200 px-4 py-2 text-sm dark:border-gray-700"
					on:click={() => (showFeedback = true)}>提交实际返修结果</button
				>{/if}
		</section>
	</div>
</div>

{#if showFeedback}
	<Modal bind:show={showFeedback} size="sm">
		<form class="p-5" on:submit|preventDefault={submitFeedback}>
			<h2 class="font-medium">提交返修反馈</h2>
			<p class="mt-1 text-sm text-gray-500">PN {query.pn} · SN {maskSn(query.sn)}</p>
			<div class="mt-4 space-y-3 text-sm">
				<label class="block"
					>测量状态 <select bind:value={feedback.measurement_status} class="input-field mt-1 w-full"
						><option value="measured">已测量</option><option value="not_measured">未测量</option
						><option value="not_applicable">不适用</option></select
					></label
				>
				<label class="block"
					>实际操作 <textarea
						bind:value={feedback.repair_steps}
						rows="3"
						class="input-field mt-1 w-full"
					></textarea></label
				>
				<label class="block"
					>测试结果 <textarea
						bind:value={feedback.test_result}
						rows="2"
						class="input-field mt-1 w-full"
					></textarea></label
				>
				<label class="block"
					>换件 PN（如有）<input
						bind:value={feedback.replacement_part_pn}
						class="input-field mt-1 w-full"
					/></label
				>
				<label class="block"
					>最终结果 <textarea
						bind:value={feedback.final_result}
						required
						rows="2"
						class="input-field mt-1 w-full"
					></textarea></label
				>
			</div>
			<div class="mt-5 flex justify-end gap-2">
				<button
					type="button"
					class="rounded-xl px-4 py-2 text-sm"
					on:click={() => (showFeedback = false)}>取消</button
				><button
					type="submit"
					class="rounded-xl bg-gray-900 px-4 py-2 text-sm text-white dark:bg-white dark:text-gray-900"
					>提交</button
				>
			</div>
		</form>
	</Modal>
{/if}
