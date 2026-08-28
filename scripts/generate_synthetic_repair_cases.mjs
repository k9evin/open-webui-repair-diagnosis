import fs from 'node:fs/promises';
import { SpreadsheetFile, Workbook } from '@oai/artifact-tool';

const outputPath = process.argv[2];
if (!outputPath) throw new Error('Usage: node generate_synthetic_repair_cases.mjs <output.xlsx>');

let state = 20260827;
const random = () => {
	state = (state * 1664525 + 1013904223) >>> 0;
	return state / 2 ** 32;
};
const choose = (values) => values[Math.floor(random() * values.length)];
const maybe = (value, chance) => (random() < chance ? '' : value);

const headers = [
	'模拟标识',
	'源行号',
	'PN',
	'SN',
	'产品类型',
	'产品族',
	'分厂',
	'失效类型',
	'故障描述（原始）',
	'维修步骤（原始）',
	'测试结果（原始）',
	'测量状态',
	'原件 PN',
	'替换件 PN',
	'替换件描述（原始）',
	'最终结果',
	'复测结果',
	'根因（原始）',
	'质量提示'
];

const productTypes = ['PCBA', 'Module', 'Assembly'];
const failureKinds = ['VOA', '无输出', '过流', '通信异常', '间歇性故障', '温升异常'];
const descriptions = [
	'上电后无输出，指示灯灭',
	'客户报偶发掉线，复现不稳定',
	'ATE 报电流异常，未记录测试点',
	'通电 3 分钟后温升偏高',
	'功能正常但老化后失效',
	'输入有电，输出为 0V',
	'偶现红灯，重启后恢复',
	'不良，详见附件'
];
const steps = [
	'目检后测量 VIN/VOUT，更换 U12 并复测。',
	'查焊点，补焊 J3；正常。',
	'先换件，后测。',
	'未做测量，按经验更换驱动 IC。',
	'检查连接器与线束，重新插拔后通过。',
	'测 TP3=0.2V，拆下可疑电容。',
	'返工焊盘，步骤记录不完整。',
	''
];
const tests = ['VOUT=12.01V，负载正常', '复测 OK', '电流 0.32A', '未记录', 'ATE PASS', '', 'OK?', '与标准不一致'];
const roots = ['虚焊', '驱动 IC 损坏', '连接器接触不良', '电容漏电', '待工程确认', '', '疑似软件', '原因不明'];

const rows = Array.from({ length: 370 }, (_, index) => {
	const rowNumber = index + 2;
	const productType = choose(productTypes);
	const pnBase = `${productType === 'PCBA' ? 'PCBA' : productType === 'Module' ? 'MOD' : 'ASM'}-${String((index % 37) + 1).padStart(3, '0')}`;
	const pn = choose([pnBase, pnBase.replace('-', ' '), `${pnBase}-R${(index % 3) + 1}`]);
	const failure = maybe(choose(failureKinds), 0.18);
	const replacement = maybe(`U${String((index % 48) + 1).padStart(2, '0')}-DRV`, 0.42);
	const finalResult = choose(['修复成功', '待复测', '报废', '客户退回', 'OK', '']);
	return [
		'SYNTHETIC_FA_CASE',
		rowNumber,
		pn,
		maybe(`SN${String(100000 + index).slice(-6)}`, 0.08),
		productType,
		choose(['Power', 'Control', 'IO', '']),
		choose(['SZ-A', 'SZ-B', 'WH-1', '']),
		failure,
		maybe(choose(descriptions), 0.06),
		choose(steps),
		choose(tests),
		choose(['measured', 'not_measured', 'not_applicable', 'not_recorded', '']),
		maybe(`C${String((index % 120) + 1).padStart(3, '0')}`, 0.35),
		replacement,
		replacement ? choose(['更换驱动 IC', '替换料号不清楚', '拆机件', '']) : '',
		finalResult,
		maybe(choose(['PASS', 'FAIL', '未复测', '']), 0.28),
		choose(roots),
		choose(['信息完整', '步骤过短', '缺失失效类型', '测量缺失', '疑似矛盾记录', '重复维修模式'])
	];
});

const workbook = Workbook.create();
const sheet = workbook.worksheets.add('返修案例');
sheet.showGridLines = false;
sheet.getRange(`A1:S${rows.length + 1}`).values = [headers, ...rows];
sheet.getRange('A1:S1').format = {
	fill: '#1F4E78',
	font: { bold: true, color: '#FFFFFF' },
	horizontalAlignment: 'center',
	verticalAlignment: 'center',
	wrapText: true
};
sheet.getRange(`A2:S${rows.length + 1}`).format.verticalAlignment = 'top';
sheet.getRange(`I2:K${rows.length + 1}`).format.wrapText = true;
sheet.getRange(`A1:S${rows.length + 1}`).format.borders = {
	preset: 'insideHorizontal',
	style: 'thin',
	color: '#E5E7EB'
};
sheet.getRange('A:S').format.columnWidth = 14;
sheet.getRange('A:A').format.columnWidth = 22;
sheet.getRange('B:B').format.columnWidth = 10;
sheet.getRange('I:K').format.columnWidth = 28;
sheet.getRange('P:Q').format.columnWidth = 16;
sheet.getRange(`A2:B${rows.length + 1}`).format.numberFormat = '@';
sheet.getRange('1:1').format.rowHeight = 28;
sheet.freezePanes.freezeRows(1);
sheet.tables.add(`A1:S${rows.length + 1}`, true, 'SyntheticRepairCases');

const notes = workbook.worksheets.add('说明');
notes.showGridLines = false;
notes.getRange('A1:B5').values = [
	['项目', '说明'],
	['数据性质', 'SYNTHETIC：仅供开发、上传 API 与回归测试，禁止作为生产返修依据。'],
	['生成方式', '固定种子 20260827；恰好 370 条人工填写风格模拟案例。'],
	['覆盖缺陷', '短/长描述、字段缺失、术语不一致、无测量值、换件/复测缺失、重复和矛盾记录。'],
	['来源追溯', '源行号对应本工作簿“返修案例”工作表行号。']
];
notes.getRange('A1:B1').format = { fill: '#1F4E78', font: { bold: true, color: '#FFFFFF' } };
notes.getRange('A1:B5').format.wrapText = true;
notes.getRange('A:A').format.columnWidth = 16;
notes.getRange('B:B').format.columnWidth = 72;

const output = await SpreadsheetFile.exportXlsx(workbook);
await fs.mkdir(new URL('.', `file://${outputPath}`).pathname, { recursive: true });
await output.save(outputPath);

const check = await workbook.inspect({
	kind: 'table',
	range: '返修案例!A1:S5',
	include: 'values',
	tableMaxRows: 5,
	tableMaxCols: 19
});
if (!check.ndjson || rows.length !== 370) throw new Error('Synthetic workbook verification failed');

if (process.env.REPAIR_XLSX_PREVIEW) {
	const preview = await workbook.render({
		sheetName: '返修案例',
		range: 'A1:S12',
		scale: 1,
		format: 'png'
	});
	await fs.writeFile(process.env.REPAIR_XLSX_PREVIEW, new Uint8Array(await preview.arrayBuffer()));
}
