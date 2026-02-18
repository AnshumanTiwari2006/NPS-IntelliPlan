/* ============================================================
   NPS IntelliPlan — Complete Application Logic v2
   Features: 5 charts, animated counters, sliders, dark mode,
   share link, what-if, tax calc, AI advice, export, print
   ============================================================ */

const API = '/api';
let charts = { growth: null, dist: null, pie: null, alloc: null, inflation: null };

// ── Theme ────────────────────────────────────────────────────
const THEME_KEY = 'nps-theme';
function initTheme() {
    const saved = localStorage.getItem(THEME_KEY) || 'light';
    document.documentElement.setAttribute('data-theme', saved);
    updateThemeIcon(saved);
}
function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem(THEME_KEY, next);
    updateThemeIcon(next);
}
function updateThemeIcon(t) {
    const btn = document.getElementById('themeToggle');
    if (btn) btn.textContent = t === 'dark' ? '☀️' : '🌙';
}

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    bindSliders();
    loadFromURL();
    animateHeroCounters();

    const listen = (id, evt, fn) => {
        const el = document.getElementById(id);
        if (el) el.addEventListener(evt, fn);
    };

    listen('forecastForm', 'submit', handleForecast);
    listen('compareBtn', 'click', handleCompare);
    listen('whatIfBtn', 'click', handleWhatIf);
    listen('themeToggle', 'click', toggleTheme);
    listen('riskBtn', 'click', () => {
        const m = document.getElementById('riskModal');
        if (m) m.style.display = 'flex';
    });
    listen('closeRiskBtn', 'click', () => {
        const m = document.getElementById('riskModal');
        if (m) m.style.display = 'none';
    });
    listen('riskForm', 'submit', handleRiskAssessment);
    listen('applyRiskBtn', 'click', applyRiskRecommendation);
    listen('checkGapBtn', 'click', handleGoalGap);

    setupGlossary();
});

// ── Slider Binding ───────────────────────────────────────────
function bindSliders() {
    const pairs = [
        ['currentAgeSlider', 'currentAge'],
        ['retirementAgeSlider', 'retirementAge'],
        ['contributionSlider', 'monthlyContribution']
    ];
    pairs.forEach(([slider, input]) => {
        const s = document.getElementById(slider);
        const i = document.getElementById(input);
        if (!s || !i) return;
        s.addEventListener('input', () => { i.value = s.value; if (input === 'currentAge') applySmartDefaults(s.value); });
        i.addEventListener('input', () => { s.value = i.value; if (input === 'currentAge') applySmartDefaults(i.value); });
    });
}

// ── Share Link ───────────────────────────────────────────────
function copyShareLink() {
    const fd = getFormData();
    const params = new URLSearchParams({
        a: fd.currentAge, r: fd.retirementAge, c: fd.monthlyContribution,
        p: fd.riskProfile, i: fd.inflationRate, b: fd.initialBalance,
        s: fd.annualStepUp, e: fd.employerContribution
    });
    const url = `${window.location.origin}${window.location.pathname}?${params}`;

    // QR Code generation
    const qrDiv = document.getElementById('qrCode');
    if (qrDiv) {
        qrDiv.innerHTML = `<img src="https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${encodeURIComponent(url)}" alt="QR Code" style="width:100%; height:100%; border-radius:4px;">`;
    }

    navigator.clipboard.writeText(url).then(() => {
        const toast = document.getElementById('shareToast');
        toast.style.display = '';
        setTimeout(() => toast.style.display = 'none', 2500);
    }).catch(() => {
        window.prompt('Copy this link:', url);
    });
}

function loadFromURL() {
    const p = new URLSearchParams(window.location.search);
    if (!p.has('a')) return;
    setVal('currentAge', p.get('a'));
    setVal('retirementAge', p.get('r'));
    setVal('monthlyContribution', p.get('c'));
    if (p.get('p')) document.getElementById('riskProfile').value = p.get('p');
    setVal('inflationRate', p.get('i'));
    setVal('initialBalance', p.get('b'));
    setVal('annualStepUp', p.get('s'));
    setVal('employerContribution', p.get('e'));
    // sync sliders
    syncSlider('currentAgeSlider', 'currentAge');
    syncSlider('retirementAgeSlider', 'retirementAge');
    syncSlider('contributionSlider', 'monthlyContribution');
}
function setVal(id, v) { if (v != null) { const el = document.getElementById(id); if (el) el.value = v; } }
function syncSlider(s, i) { const sl = document.getElementById(s); const ip = document.getElementById(i); if (sl && ip) sl.value = ip.value; }
function setText(id, v) { const el = document.getElementById(id); if (el) el.textContent = v; }
function formatINR(v) { return '₹' + Math.round(v).toLocaleString('en-IN'); }

// ── Hero Counters ────────────────────────────────────────────
function animateHeroCounters() {
    document.querySelectorAll('.stat-number[data-count]').forEach(el => {
        const target = parseInt(el.dataset.count);
        animateCounter(el, 0, target, 1500);
    });
}

function animateCounter(el, start, end, duration) {
    const startTime = performance.now();
    const suffix = el.dataset.suffix || '';
    function update(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const ease = 1 - Math.pow(1 - progress, 3);
        const value = Math.round(start + (end - start) * ease);
        el.textContent = value.toLocaleString('en-IN') + suffix;
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

// ── Form Data ────────────────────────────────────────────────
function getFormData() {
    return {
        currentAge: parseInt(document.getElementById('currentAge').value),
        retirementAge: parseInt(document.getElementById('retirementAge').value),
        monthlyContribution: parseFloat(document.getElementById('monthlyContribution').value),
        riskProfile: document.getElementById('riskProfile').value,
        inflationRate: parseFloat(document.getElementById('inflationRate').value),
        initialBalance: parseFloat(document.getElementById('initialBalance').value) || 0,
        annualStepUp: parseFloat(document.getElementById('annualStepUp').value) || 0,
        employerContribution: parseFloat(document.getElementById('employerContribution').value) || 0,
        annuityProvider: document.getElementById('annuityProvider').value
    };
}

function validateForm(d) {
    if (d.retirementAge <= d.currentAge) { showError('Retirement age must be greater than current age.'); return false; }
    if (d.monthlyContribution < 500) { showError('Min ₹500/month as per PFRDA norms.'); return false; }
    return true;
}

// ── Forecast ─────────────────────────────────────────────────
async function handleForecast(e) {
    e.preventDefault();
    const fd = getFormData();
    if (!validateForm(fd)) return;
    setLoading(true); hideError();

    try {
        const res = await fetch(`${API}/forecast`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                current_age: fd.currentAge,
                retirement_age: fd.retirementAge,
                monthly_contribution: fd.monthlyContribution,
                risk_profile: fd.riskProfile,
                inflation_rate: fd.inflationRate,
                initial_balance: fd.initialBalance,
                annual_step_up: fd.annualStepUp,
                employer_contribution: fd.employerContribution,
                annuity_provider: fd.annuityProvider,
                use_monte_carlo: true
            })
        });
        if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `Error ${res.status}`);
        const data = await res.json();
        displayResults(data, fd);

        // Fire tax and peer comparison in parallel
        fetchTaxBenefits(fd);
        fetchPeerComparison(fd);
    } catch (err) {
        showError(err.message || 'Forecast failed. Is the backend running?');
        console.error(err);
    } finally { setLoading(false); }
}

// ── Display Results ──────────────────────────────────────────
function displayResults(api, fd) {
    document.getElementById('resultsContainer').style.display = '';
    document.getElementById('comparisonSection').style.display = 'none';
    document.getElementById('whatIfSection').style.display = 'none';

    const det = api.deterministic_projection;
    const sim = api.simulation_results;

    let medCorpus = det.nominal_corpus;
    let medPension = det.monthly_pension_nominal;

    if (sim) {
        medCorpus = sim.corpus_statistics.median;
        medPension = sim.pension_statistics.median_pension;
    }

    // Animated KPI cards
    animateKPI('corpusValue', medCorpus);
    animateKPI('pensionValue', medPension);
    animateKPI('realCorpusValue', det.real_corpus);

    if (sim && sim.all_outcomes) {
        const rate = successRate(sim.all_outcomes, medCorpus);
        setText('probabilityValue', rate + '%');
        setText('corpusSubtext',
            `10th–90th: ${formatINR(sim.corpus_statistics.percentile_10)} — ${formatINR(sim.corpus_statistics.percentile_90)}`);
    } else {
        setText('probabilityValue', '—');
        setText('corpusSubtext', 'Deterministic estimate');
    }

    // Breakdown
    setText('yearsValue', det.years_invested + ' years');
    setText('totalContributions', formatINR(det.total_contributions));
    setText('employeeContributions', formatINR(det.total_employee_contributions || det.total_contributions));
    setText('employerContributions', formatINR(det.total_employer_contributions || 0));
    setText('growthMultiplier', det.growth_multiplier.toFixed(2) + '×');
    setText('lumpsumValue', formatINR(det.lumpsum_withdrawal));
    setText('annuityValue', formatINR(det.annuity_purchase_amount));
    setText('returnRate', det.expected_return_rate.toFixed(1) + '% p.a.');
    setText('annuityProviderValue', det.annuity_provider + ' (' + det.annuity_rate_used + '%)');

    // Year-by-year table
    if (det.yearly_breakdown) buildYearlyTable(det.yearly_breakdown);

    // Charts
    drawGrowthChart(fd, det);
    if (sim) drawDistributionChart(sim);
    drawPieChart(det);
    drawAllocationChart(api.asset_allocation || {});
    drawInflationChart(fd);

    // AI narrative
    if (api.narrative) {
        document.getElementById('narrativePanel').style.display = '';
        setText('narrativeText', api.narrative);
    }

    // AI advice
    if (api.ai_advice && Array.isArray(api.ai_advice)) {
        document.getElementById('advicePanel').style.display = '';
        const ul = document.getElementById('adviceList');
        ul.innerHTML = '';
        api.ai_advice.forEach(a => {
            const li = document.createElement('li');
            li.textContent = a;
            ul.appendChild(li);
        });
    }

    document.getElementById('resultsContainer').scrollIntoView({ behavior: 'smooth' });
}

// ── Animated KPI ─────────────────────────────────────────────
function animateKPI(id, value) {
    const el = document.getElementById(id);
    const start = 0;
    const startTime = performance.now();
    const duration = 1200;
    function update(now) {
        const progress = Math.min((now - startTime) / duration, 1);
        const ease = 1 - Math.pow(1 - progress, 3);
        const current = start + (value - start) * ease;
        el.textContent = formatINR(current);
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

// ── Tax Benefits ─────────────────────────────────────────────
async function fetchTaxBenefits(fd) {
    try {
        const res = await fetch(`${API}/tax-benefits`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                annual_contribution: fd.monthlyContribution * 12,
                annual_employer_contribution: fd.employerContribution * 12,
                annual_salary: 0,
                tax_regime: 'old'
            })
        });
        if (!res.ok) return;
        const tax = await res.json();
        setText('tax80ccd1', formatINR(tax.sec_80ccd1));
        setText('tax80ccd1b', formatINR(tax.sec_80ccd1b));
        setText('tax80ccd2', formatINR(tax.sec_80ccd2));
        setText('taxTotalDeduction', formatINR(tax.total_deduction));
        setText('taxSaved', formatINR(tax.estimated_tax_saved));
    } catch (e) { console.warn('Tax calc failed:', e); }
}

// ── Compare ──────────────────────────────────────────────────
async function handleCompare() {
    const fd = getFormData();
    if (!validateForm(fd)) return;
    setLoading(true); hideError();

    try {
        const res = await fetch(`${API}/compare`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                current_age: fd.currentAge, retirement_age: fd.retirementAge,
                monthly_contribution: fd.monthlyContribution,
                inflation_rate: fd.inflationRate, initial_balance: fd.initialBalance,
                annual_step_up: fd.annualStepUp, employer_contribution: fd.employerContribution,
                use_monte_carlo: true
            })
        });
        if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `Error ${res.status}`);
        const data = await res.json();
        displayComparison(data.scenarios);
    } catch (err) {
        showError(err.message);
    } finally { setLoading(false); }
}

function displayComparison(sc) {
    document.getElementById('resultsContainer').style.display = '';
    document.getElementById('comparisonSection').style.display = '';
    const tbody = document.getElementById('comparisonTableBody');
    tbody.innerHTML = '';

    const rows = [
        { l: 'Median Corpus', c: sc.conservative.corpus_statistics.median, m: sc.moderate.corpus_statistics.median, a: sc.aggressive.corpus_statistics.median },
        { l: 'Monthly Pension', c: sc.conservative.pension_statistics.median_pension, m: sc.moderate.pension_statistics.median_pension, a: sc.aggressive.pension_statistics.median_pension },
        { l: 'Best Case (90th)', c: sc.conservative.corpus_statistics.percentile_90, m: sc.moderate.corpus_statistics.percentile_90, a: sc.aggressive.corpus_statistics.percentile_90 },
        { l: 'Worst Case (10th)', c: sc.conservative.corpus_statistics.percentile_10, m: sc.moderate.corpus_statistics.percentile_10, a: sc.aggressive.corpus_statistics.percentile_10 }
    ];
    rows.forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td><strong>${r.l}</strong></td><td class="col-con">${formatINR(r.c)}</td><td class="col-mod">${formatINR(r.m)}</td><td class="col-agg">${formatINR(r.a)}</td>`;
        tbody.appendChild(tr);
    });
    document.getElementById('comparisonSection').scrollIntoView({ behavior: 'smooth' });
}

// ── What-If ──────────────────────────────────────────────────
async function handleWhatIf() {
    const fd = getFormData();
    if (!validateForm(fd)) return;
    setLoading(true); hideError();

    try {
        const res = await fetch(`${API}/what-if`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                current_age: fd.currentAge, retirement_age: fd.retirementAge,
                monthly_contribution: fd.monthlyContribution, risk_profile: fd.riskProfile,
                inflation_rate: fd.inflationRate, initial_balance: fd.initialBalance,
                annual_step_up: fd.annualStepUp, employer_contribution: fd.employerContribution
            })
        });
        if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `Error ${res.status}`);
        const data = await res.json();
        displayWhatIf(data);
    } catch (err) {
        showError(err.message);
    } finally { setLoading(false); }
}

function displayWhatIf(data) {
    document.getElementById('resultsContainer').style.display = '';
    const section = document.getElementById('whatIfSection');
    section.style.display = '';
    const grid = document.getElementById('whatIfGrid');
    grid.innerHTML = '';

    const base = data.base_projection;
    for (const [key, sc] of Object.entries(data.scenarios)) {
        const card = document.createElement('div');
        card.className = 'whatif-card';
        const changeClass = sc.corpus_change_pct >= 0 ? 'positive' : 'negative';
        const arrow = sc.corpus_change_pct >= 0 ? '↑' : '↓';
        card.innerHTML = `
            <h4>${sc.label}</h4>
            <div class="whatif-values">
                <div class="whatif-value"><span class="whatif-label">Corpus</span><span class="whatif-num">${formatINR(sc.corpus)}</span></div>
                <div class="whatif-value"><span class="whatif-label">Pension</span><span class="whatif-num">${formatINR(sc.pension)}</span></div>
            </div>
            <p class="whatif-change ${changeClass}">${arrow} ${Math.abs(sc.corpus_change_pct)}% vs current plan</p>`;
        grid.appendChild(card);
    }
    section.scrollIntoView({ behavior: 'smooth' });
}

// ── Year-by-Year ─────────────────────────────────────────────
function buildYearlyTable(breakdown) {
    const tbody = document.getElementById('yearlyTableBody');
    tbody.innerHTML = '';
    breakdown.forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${row.year}</td>
            <td>${row.age}</td>
            <td>${formatINR(row.monthly_contribution)}</td>
            <td>${formatINR(row.employee_contribution)}</td>
            <td>${formatINR(row.growth)}</td>
            <td><strong>${formatINR(row.end_corpus)}</strong></td>`;
        tbody.appendChild(tr);
    });
}

// ── Export CSV ────────────────────────────────────────────────
let lastYearlyBreakdown = [];
function exportCSV() {
    const tbody = document.getElementById('yearlyTableBody');
    const rows = tbody.querySelectorAll('tr');
    if (!rows.length) { showError('Run a forecast first to export data.'); return; }

    let csv = 'Year,Age,Monthly Contribution,Year Contribution,Growth,Corpus\n';
    rows.forEach(tr => {
        const cells = tr.querySelectorAll('td');
        csv += Array.from(cells).map(c => c.textContent.replace(/,/g, '')).join(',') + '\n';
    });

    const blob = new Blob([csv], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'nps_intelliplan_forecast.csv';
    a.click();
    URL.revokeObjectURL(a.href);
}

// ── Charts ───────────────────────────────────────────────────
const isDark = () => document.documentElement.getAttribute('data-theme') === 'dark';
const gridColor = () => isDark() ? 'rgba(255,255,255,.06)' : 'rgba(0,0,0,.04)';
const fontColor = () => isDark() ? '#9ca3af' : '#6b7280';

const COLORS = {
    blue: { bg: 'rgba(59,130,246,.12)', border: '#3b82f6' },
    green: { bg: 'rgba(34,197,94,.12)', border: '#22c55e' },
    purple: { bg: 'rgba(168,85,247,.4)', border: '#a855f7' },
    amber: { bg: 'rgba(245,158,11,.12)', border: '#f59e0b' },
    red: { bg: 'rgba(239,68,68,.12)', border: '#ef4444' }
};

function chartFont() { return { family: "'Inter', sans-serif", size: 11, color: fontColor() }; }

function drawGrowthChart(fd, det, sim) {
    const breakdown = det.yearly_breakdown || [];
    const labels = breakdown.map(r => `Age ${r.age}`);
    const data = breakdown.map(r => r.end_corpus);
    const contributions = [];
    let cum = fd.initialBalance;
    breakdown.forEach(r => { cum += r.employee_contribution + (r.employer_contribution || 0); contributions.push(cum); });

    const datasets = [
        {
            label: 'Deterministic Projection',
            data,
            borderColor: COLORS.blue.border,
            backgroundColor: COLORS.blue.bg,
            fill: false, tension: .35, pointRadius: 0, borderWidth: 2.5, z: 10
        },
        {
            label: 'Total Invested',
            data: contributions,
            borderColor: COLORS.amber.border,
            backgroundColor: 'transparent',
            borderDash: [6, 3],
            fill: false, tension: 0, pointRadius: 0, borderWidth: 1.5
        }
    ];

    // Add Monte Carlo Bands if available
    if (sim && sim.yearly_bands) {
        datasets.unshift(
            {
                label: '90th Percentile (Optimistic)',
                data: sim.yearly_bands.p90,
                borderColor: 'transparent',
                backgroundColor: 'rgba(59,130,246,0.05)',
                fill: '+1', tension: .35, pointRadius: 0, borderWidth: 0
            },
            {
                label: 'Median Path (Probabilistic)',
                data: sim.yearly_bands.p50,
                borderColor: COLORS.purple.border,
                backgroundColor: 'rgba(168,85,247,0.1)',
                fill: false, tension: .35, pointRadius: 0, borderWidth: 2
            },
            {
                label: '10th Percentile (Conservative)',
                data: sim.yearly_bands.p10,
                borderColor: 'transparent',
                backgroundColor: 'rgba(59,130,246,0.05)',
                fill: false, tension: .35, pointRadius: 0, borderWidth: 0
            }
        );
    }

    const ctx = document.getElementById('growthChart').getContext('2d');
    if (charts.growth) charts.growth.destroy();

    charts.growth = new Chart(ctx, {
        type: 'line',
        data: { labels, datasets },
        options: {
            responsive: true, maintainAspectRatio: true,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { labels: { font: chartFont(), usePointStyle: true, pointStyle: 'circle' } },
                tooltip: { callbacks: { label: c => '  ' + c.dataset.label + ': ' + formatINR(c.parsed.y) } }
            },
            scales: {
                y: { beginAtZero: true, grid: { color: gridColor() }, ticks: { font: chartFont(), callback: v => formatCompact(v) } },
                x: { grid: { display: false }, ticks: { font: chartFont(), maxTicksLimit: 10 } }
            }
        }
    });
}

function drawDistributionChart(sim) {
    const d = sim.distribution;
    const labels = d.bins.slice(0, -1).map((b, i) => formatCompact((b + d.bins[i + 1]) / 2));
    const ctx = document.getElementById('distributionChart').getContext('2d');
    if (charts.dist) charts.dist.destroy();

    charts.dist = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Probability',
                data: d.probabilities,
                backgroundColor: COLORS.purple.bg,
                borderColor: COLORS.purple.border,
                borderWidth: 1, borderRadius: 3
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: true,
            plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => ' ' + c.parsed.y.toFixed(2) + '%' } } },
            scales: {
                y: { beginAtZero: true, grid: { color: gridColor() }, title: { display: true, text: 'Probability (%)', font: chartFont() }, ticks: { font: chartFont() } },
                x: { grid: { display: false }, title: { display: true, text: 'Corpus Value', font: chartFont() }, ticks: { font: chartFont(), maxTicksLimit: 12 } }
            }
        }
    });
}

function drawPieChart(det) {
    const totalContrib = det.total_contributions;
    const growth = det.nominal_corpus - totalContrib - (det.initial_balance || 0);
    const ctx = document.getElementById('pieChart').getContext('2d');
    if (charts.pie) charts.pie.destroy();

    const labels = ['Contributions', 'Growth'];
    const data = [Math.max(0, totalContrib), Math.max(0, growth)];

    // If there's employer contribution, split it out
    if (det.total_employer_contributions && det.total_employer_contributions > 0) {
        labels[0] = 'Employee';
        labels.splice(1, 0, 'Employer');
        data[0] = det.total_employee_contributions;
        data.splice(1, 0, det.total_employer_contributions);
    }

    charts.pie = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: [COLORS.blue.border, COLORS.amber.border, COLORS.green.border].slice(0, labels.length),
                borderWidth: 0, hoverOffset: 8
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: true,
            cutout: '55%',
            plugins: {
                legend: { position: 'bottom', labels: { font: chartFont(), padding: 16, usePointStyle: true } },
                tooltip: { callbacks: { label: c => ' ' + c.label + ': ' + formatINR(c.parsed) } }
            }
        }
    });
}

function drawAllocationChart(alloc) {
    const labels = Object.keys(alloc).map(k => k.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()));
    const data = Object.values(alloc);
    if (!data.length) return;

    const ctx = document.getElementById('allocationChart').getContext('2d');
    if (charts.alloc) charts.alloc.destroy();

    charts.alloc = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: [COLORS.blue.border, COLORS.green.border, COLORS.amber.border],
                borderWidth: 0, hoverOffset: 8
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: true,
            cutout: '55%',
            plugins: {
                legend: { position: 'bottom', labels: { font: chartFont(), padding: 16, usePointStyle: true } },
                tooltip: { callbacks: { label: c => ' ' + c.label + ': ' + c.parsed + '%' } }
            }
        }
    });
}

function drawInflationChart(fd) {
    const years = fd.retirementAge - fd.currentAge;
    const rate = fd.inflationRate / 100;
    const labels = [];
    const data = [];
    for (let y = 0; y <= years; y += Math.max(1, Math.floor(years / 15))) {
        labels.push(`Year ${y}`);
        data.push(Math.round(100000 / Math.pow(1 + rate, y)));
    }
    // Ensure last year is included
    if (labels[labels.length - 1] !== `Year ${years}`) {
        labels.push(`Year ${years}`);
        data.push(Math.round(100000 / Math.pow(1 + rate, years)));
    }

    const ctx = document.getElementById('inflationChart').getContext('2d');
    if (charts.inflation) charts.inflation.destroy();

    charts.inflation = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Real Value of ₹1,00,000',
                data,
                borderColor: COLORS.red.border,
                backgroundColor: COLORS.red.bg,
                fill: true, tension: .3, pointRadius: 3, borderWidth: 2,
                pointBackgroundColor: COLORS.red.border
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: c => '  ₹' + c.parsed.y.toLocaleString('en-IN') } }
            },
            scales: {
                y: { beginAtZero: false, grid: { color: gridColor() }, ticks: { font: chartFont(), callback: v => '₹' + formatCompact(v) } },
                x: { grid: { display: false }, ticks: { font: chartFont() } }
            }
        }
    });
}

// ── Helpers ──────────────────────────────────────────────────
function setText(id, v) { const el = document.getElementById(id); if (el) el.textContent = v; }

function formatINR(n) {
    if (n == null) return '—';
    n = Number(n);
    if (n >= 1e7) return '₹' + (n / 1e7).toFixed(2) + ' Cr';
    if (n >= 1e5) return '₹' + (n / 1e5).toFixed(2) + ' L';
    if (n >= 1e3) return '₹' + (n / 1e3).toFixed(1) + ' K';
    return '₹' + n.toLocaleString('en-IN');
}

function formatCompact(n) {
    if (n >= 1e7) return '₹' + (n / 1e7).toFixed(1) + 'Cr';
    if (n >= 1e5) return '₹' + (n / 1e5).toFixed(0) + 'L';
    if (n >= 1e3) return '₹' + (n / 1e3).toFixed(0) + 'K';
    return '₹' + Math.round(n);
}

// ── Risk Profiler ────────────────────────────────────────────
async function handleRiskAssessment(e) {
    e.preventDefault();
    const fd = new FormData(e.target);
    const answers = {
        age: parseInt(document.getElementById('currentAge').value),
        investment_horizon: parseInt(document.getElementById('retirementAge').value) - parseInt(document.getElementById('currentAge').value),
        income_stability: fd.get('stability'),
        risk_tolerance: fd.get('horizon'),
        existing_savings: "moderate", // Default
        dependents: 1 // Default
    };

    try {
        const res = await fetch(`${API}/risk-assessment`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(answers)
        });
        if (!res.ok) throw new Error((await res.json()).detail || "Error");
        const data = await res.json();

        document.getElementById('riskResult').style.display = 'block';
        setText('recProfileText', data.recommended_profile.charAt(0).toUpperCase() + data.recommended_profile.slice(1));
        setText('recDescText', data.reasoning);
        setText('recAiInsight', data.ai_insight || "");

        // Store for application
        window.lastRecProfile = data.recommended_profile;
    } catch (err) {
        console.error('Risk assessment failed', err);
    }
}

function applyRiskRecommendation() {
    if (window.lastRecProfile) {
        document.getElementById('riskProfile').value = window.lastRecProfile;
        document.getElementById('riskModal').style.display = 'none';
        // Show a small toast
        showToast(`Risk profile set to ${window.lastRecProfile}.`);
    }
}

// ── Goal Gap Analysis ────────────────────────────────────────
async function handleGoalGap() {
    const fd = getFormData();
    const targetEl = document.getElementById('targetPension');
    if (!targetEl) return;
    const target = parseFloat(targetEl.value);
    console.log('Checking Goal Gap for target:', target, fd);

    try {
        const res = await fetch(`${API}/goal-gap`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                current_age: fd.currentAge,
                retirement_age: fd.retirementAge,
                monthly_contribution: fd.monthlyContribution,
                risk_profile: fd.riskProfile,
                inflation_rate: fd.inflationRate,
                initial_balance: fd.initialBalance,
                annual_step_up: fd.annualStepUp,
                employer_contribution: fd.employerContribution,
                target_monthly_pension: target
            })
        });
        if (!res.ok) throw new Error((await res.json()).detail || "Error");
        const data = await res.json();
        console.log('Goal Gap API response:', data);

        // Show result panel
        const resultPanel = document.getElementById('goalGapResult');
        if (!resultPanel) return;
        resultPanel.style.display = 'block';
        resultPanel.style.opacity = '1';
        resultPanel.style.visibility = 'visible';
        resultPanel.style.borderColor = data.status === 'on_track' ? 'var(--green-500)' :
            data.status === 'close' ? 'var(--blue-500)' : 'var(--red-500)';

        setText('goalGapMessage', data.message);
        const list = document.getElementById('goalGapRecList');
        list.innerHTML = '';
        (data.recommendations || []).forEach(rec => {
            const li = document.createElement('li');
            li.textContent = rec;
            list.appendChild(li);
        });

        // Add a status tag
        const btn = document.getElementById('checkGapBtn');
        const existing = document.getElementById('gapResultTag');
        if (existing) existing.remove();
        const tag = document.createElement('span');
        tag.id = 'gapResultTag';
        tag.className = 'gap-tag ' + (data.status === 'on_track' ? 'success' : 'fail');
        tag.textContent = data.status === 'on_track' ? 'Status: On Track' : `Gap Identified: ${formatINR(data.gap_amount)}`;
        btn.parentNode.appendChild(tag);

    } catch (err) {
        console.error('Goal gap check failed', err);
        showError('Goal gap analysis failed');
    }
}

function showToast(msg) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function successRate(outcomes, target) {
    if (!outcomes || !outcomes.length) return 0;
    return Math.round((outcomes.filter(v => v >= target * 0.9).length / outcomes.length) * 100);
}

function applySmartDefaults(age) {
    age = parseInt(age);
    const contrib = document.getElementById('monthlyContribution');
    const risk = document.getElementById('riskProfile');

    // Smart Defaults by age bracket
    if (age < 30) {
        if (contrib.value == 500) contrib.value = 5000;
        risk.value = 'aggressive';
    } else if (age < 45) {
        if (contrib.value == 5000) contrib.value = 15000;
        risk.value = 'moderate';
    } else {
        if (contrib.value == 15000) contrib.value = 25000;
        risk.value = 'conservative';
    }
    syncSlider('contributionSlider', 'monthlyContribution');
}

async function fetchPeerComparison(fd) {
    try {
        const res = await fetch(`${API}/peer-comparison`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                current_age: fd.currentAge,
                retirement_age: fd.retirementAge,
                monthly_contribution: fd.monthlyContribution,
                risk_profile: fd.riskProfile,
                inflation_rate: fd.inflationRate,
                initial_balance: fd.initialBalance
            })
        });
        if (!res.ok) return;
        const data = await res.json();

        document.getElementById('peerPanel').style.display = 'block';
        setText('peerAvgContrib', formatINR(data.peer_average_contribution));
        setText('userPercentile', data.user_percentile + '%');
        setText('cohortDesc', data.cohort_description);
        setText('peerAiContext', data.ai_context);
    } catch (e) { console.warn('Peer comparison failed:', e); }
}

function setLoading(on) {
    document.getElementById('loadingIndicator').style.display = on ? '' : 'none';
    document.getElementById('calculateBtn').disabled = on;
    document.getElementById('btnText').style.display = on ? 'none' : '';
    document.getElementById('btnLoader').style.display = on ? 'inline-flex' : 'none';
}

function showError(msg) {
    const el = document.getElementById('errorMessage');
    document.getElementById('errorText').textContent = msg;
    el.style.display = '';
}

function hideError() {
    document.getElementById('errorMessage').style.display = 'none';
}
function setupGlossary() {
    const modal = document.getElementById('glossaryModal');
    const btn = document.getElementById('glossaryBtn');
    const closeBtn = document.getElementById('closeGlossaryBtn');
    const gotItBtn = document.getElementById('gotItBtn');

    if (btn) btn.onclick = () => modal.style.display = 'flex';
    if (closeBtn) closeBtn.onclick = () => { if (modal) modal.style.display = 'none'; };
    if (gotItBtn) gotItBtn.onclick = () => { if (modal) modal.style.display = 'none'; };

    window.onclick = (event) => {
        if (event.target == modal) modal.style.display = 'none';
    }
}
