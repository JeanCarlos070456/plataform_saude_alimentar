(() => {
    const chartDataElement = document.getElementById('chart-data');
    if (!chartDataElement || typeof Plotly === 'undefined') return;

    const data = JSON.parse(chartDataElement.textContent);
    const css = getComputedStyle(document.documentElement);
    const color = (name) => css.getPropertyValue(name).trim();

    const theme = {
        primary: color('--primary'),
        accent: color('--accent'),
        sand: color('--sand'),
        secondary: color('--secondary'),
        mist: color('--mist'),
        ink: color('--ink'),
        muted: color('--muted'),
        line: color('--line'),
        surface: color('--white'),
        low: color('--risk-low'),
        medium: color('--risk-medium'),
        high: color('--risk-high'),
    };

    const formatDecimal = (value, digits = 1) => Number(value).toFixed(digits).replace('.', ',');
    const config = {
        responsive: true,
        displaylogo: false,
        scrollZoom: false,
        modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d'],
        toImageButtonOptions: { format: 'png', filename: 'caafe_indicador', scale: 2 },
    };
    const base = {
        font: { family: 'Inter, Arial, sans-serif', color: theme.ink, size: 11 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        hoverlabel: { bgcolor: theme.surface, bordercolor: theme.line, font: { color: theme.ink } },
        margin: { l: 70, r: 32, t: 24, b: 62 },
    };

    const forest = [...data.forest].reverse();
    const significant = forest.map((item) => item.adjusted_low > 1 || item.adjusted_high < 1);
    const labels = forest.map((item) => `${item.category} vs. referência`);
    const forestCustom = forest.map((item) => [item.adjusted_low, item.adjusted_high, item.p_fmt || '—']);

    Plotly.newPlot('forest-chart', [{
        type: 'scatter',
        mode: 'markers',
        x: forest.map((item) => item.adjusted_rp),
        y: labels,
        marker: {
            size: 11,
            color: significant.map((value) => value ? theme.accent : theme.secondary),
            line: { color: theme.surface, width: 1.5 },
        },
        error_x: {
            type: 'data',
            symmetric: false,
            array: forest.map((item) => item.adjusted_high - item.adjusted_rp),
            arrayminus: forest.map((item) => item.adjusted_rp - item.adjusted_low),
            color: theme.primary,
            thickness: 1.6,
            width: 5,
        },
        customdata: forestCustom,
        hovertemplate: '<b>%{y}</b><br>RP ajustada: %{x:.2f}<br>IC95%: %{customdata[0]:.2f}–%{customdata[1]:.2f}<br>p: %{customdata[2]}<extra></extra>',
    }], {
        ...base,
        height: 540,
        margin: { l: 260, r: 38, t: 24, b: 66 },
        xaxis: {
            title: { text: 'Razão de prevalências ajustada (IC95%)', standoff: 14 },
            type: 'log',
            gridcolor: theme.line,
            zeroline: false,
            tickfont: { color: theme.muted },
        },
        yaxis: { automargin: true, tickfont: { size: 10, color: theme.ink } },
        shapes: [{
            type: 'line', x0: 1, x1: 1, y0: 0, y1: 1, yref: 'paper',
            line: { color: theme.accent, dash: 'dash', width: 1.7 },
        }],
    }, config);

    const income = data.income;
    Plotly.newPlot('income-chart', [{
        type: 'bar',
        x: income.map((item) => item.category),
        y: income.map((item) => item.prevalence),
        marker: {
            color: [theme.accent, theme.sand, theme.primary],
            line: { color: theme.surface, width: 1 },
        },
        text: income.map((item) => `${formatDecimal(item.prevalence)}%`),
        textposition: 'outside',
        textfont: { color: theme.ink, size: 12 },
        error_y: {
            type: 'data', symmetric: false,
            array: income.map((item) => item.ci_high - item.prevalence),
            arrayminus: income.map((item) => item.prevalence - item.ci_low),
            color: theme.ink, thickness: 1.5, width: 5,
        },
        customdata: income.map((item) => [item.n, item.cases, item.ci_low, item.ci_high]),
        hovertemplate: '<b>%{x}</b><br>Prevalência: %{y:.1f}%<br>IC95%: %{customdata[2]:.1f}–%{customdata[3]:.1f}%<br>Casos: %{customdata[1]} de %{customdata[0]}<extra></extra>',
    }], {
        ...base,
        height: 410,
        bargap: .32,
        yaxis: { title: 'Prevalência (%)', range: [0, 100], gridcolor: theme.line, zeroline: false },
        xaxis: { tickfont: { color: theme.ink } },
    }, config);

    const levels = data.levels;
    Plotly.newPlot('level-chart', [{
        type: 'bar',
        x: levels.map((item) => item.label),
        y: levels.map((item) => item.pct),
        marker: {
            color: [theme.low, theme.medium, theme.high],
            line: { color: theme.surface, width: 1 },
        },
        text: levels.map((item) => `${formatDecimal(item.pct)}%`),
        textposition: 'outside',
        textfont: { color: theme.ink, size: 12 },
        customdata: levels.map((item) => item.n),
        hovertemplate: '<b>%{x}</b><br>Prevalência: %{y:.1f}%<br>n: %{customdata}<extra></extra>',
    }], {
        ...base,
        height: 410,
        bargap: .28,
        yaxis: {
            title: 'Prevalência (%)',
            range: [0, Math.max(60, ...levels.map((item) => item.pct + 9))],
            gridcolor: theme.line,
            zeroline: false,
        },
        xaxis: { tickfont: { color: theme.ink } },
    }, config);

    const resizeCharts = () => ['forest-chart', 'income-chart', 'level-chart'].forEach((id) => {
        const element = document.getElementById(id);
        if (element) Plotly.Plots.resize(element);
    });
    window.addEventListener('resize', resizeCharts, { passive: true });
})();
