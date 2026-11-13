
"use strict";

const $ = (id) => document.getElementById(id);

const COLORS = {
    Low: "#48d7a0",
    Medium: "#f3d66c",
    High: "#ffad66",
    Critical: "#ff657d"
};

const CATEGORIES = ["Low", "Medium", "High", "Critical"];

let riskChart = null;
let satelliteChart = null;
let activeRecords = [];
let loading = false;

async function getJSON(url) {
    const response = await fetch(url, {
        headers: { Accept: "application/json" }
    });

    if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
    }

    return response.json();
}

function formatNumber(value) {
    const number = Number(value);
    return Number.isFinite(number)
        ? number.toLocaleString("en-IN")
        : "—";
}

function safeText(value) {
    if (value === null || value === undefined || value === "") {
        return "—";
    }

    if (Array.isArray(value)) {
        return value.map(item => String(item)).join(", ");
    }

    if (typeof value === "object") {
        return JSON.stringify(value);
    }

    return String(value);
}

function makeCell(value) {
    const td = document.createElement("td");
    td.textContent = safeText(value);
    return td;
}

function makeRiskBadge(category) {
    const name = safeText(category);
    const normalized = name.toLowerCase();

    const span = document.createElement("span");
    span.className = "risk " + (
        ["critical", "high", "medium", "low"].includes(normalized)
            ? `risk-${normalized}`
            : "risk-unknown"
    );
    span.textContent = name;

    return span;
}

function renderRows(records, target, columns) {
    const body = $(target);
    const fragment = document.createDocumentFragment();

    body.replaceChildren();

    if (!Array.isArray(records) || records.length === 0) {
        const tr = document.createElement("tr");
        const td = document.createElement("td");

        td.colSpan = columns.length;
        td.className = "empty-state";
        td.textContent = "No records found.";

        tr.appendChild(td);
        body.appendChild(tr);
        return;
    }

    for (const record of records) {
        const tr = document.createElement("tr");

        for (const column of columns) {
            const td = makeCell(record[column]);

            if (column === "risk_category") {
                td.replaceChildren(makeRiskBadge(record[column]));
            }

            tr.appendChild(td);
        }

        fragment.appendChild(tr);
    }

    body.appendChild(fragment);
}

function setError(message) {
    $("errorMessage").textContent = message;
    $("errorBanner").hidden = false;
}

function clearError() {
    $("errorBanner").hidden = true;
}

function setRefreshing(value) {
    loading = value;

    $("refreshButton").disabled = value;
    $("refreshIcon").textContent = value ? "…" : "↻";
    $("refreshButton").style.opacity = value ? "0.65" : "1";
}

function renderRiskLegend(categories) {
    const legend = $("riskLegend");
    legend.replaceChildren();

    for (const category of CATEGORIES) {
        const item = document.createElement("div");
        item.className = "legend-item";

        const swatch = document.createElement("span");
        swatch.className = "legend-swatch";
        swatch.style.backgroundColor = COLORS[category];

        const label = document.createElement("span");
        label.textContent = category;

        const count = document.createElement("strong");
        count.textContent = formatNumber(categories[category] || 0);

        item.append(swatch, label, count);
        legend.appendChild(item);
    }
}

function renderRiskChart(data) {
    const categories = data.categories || {};
    const values = CATEGORIES.map(name => Number(categories[name]) || 0);

    if (riskChart) riskChart.destroy();

    riskChart = new Chart($("riskChart"), {
        type: "doughnut",
        data: {
            labels: CATEGORIES,
            datasets: [{
                data: values,
                backgroundColor: CATEGORIES.map(name => COLORS[name]),
                borderColor: "#0b1423",
                borderWidth: 5,
                hoverOffset: 7,
                borderRadius: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "76%",
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "#17263b",
                    titleColor: "#ffffff",
                    bodyColor: "#dce8fa",
                    borderColor: "#344b6c",
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label(context) {
                            const total = context.dataset.data.reduce(
                                (sum, value) => sum + Number(value || 0), 0
                            );
                            const value = Number(context.raw) || 0;
                            const percent = total
                                ? ((value / total) * 100).toFixed(1)
                                : "0.0";

                            return ` ${context.label}: ${formatNumber(value)} (${percent}%)`;
                        }
                    }
                }
            }
        }
    });

    $("chartTotal").textContent = formatNumber(data.total);
    renderRiskLegend(categories);
}

function renderSatelliteChart(data) {
    const counts = data.satellite_counts || {};
    const satellites = Object.keys(counts).sort();
    const values = satellites.map(name => Number(counts[name]) || 0);

    if (satelliteChart) satelliteChart.destroy();

    satelliteChart = new Chart($("satelliteChart"), {
        type: "bar",
        data: {
            labels: satellites,
            datasets: [{
                label: "Telemetry Records",
                data: values,
                backgroundColor: satellites.map(
                    (_, index) => index % 2 === 0 ? "#6c9fff" : "#56d8ec"
                ),
                borderRadius: 5,
                borderSkipped: false,
                maxBarThickness: 48
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "#17263b",
                    titleColor: "#ffffff",
                    bodyColor: "#dce8fa",
                    borderColor: "#344b6c",
                    borderWidth: 1,
                    padding: 11
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: "#94a7c3", font: { size: 10 } },
                    border: { display: false }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: "#8295b1",
                        precision: 0,
                        font: { size: 10 }
                    },
                    grid: { color: "#26354a" },
                    border: { display: false }
                }
            }
        }
    });

    const select = $("satellite");
    const previous = select.value;

    select.replaceChildren(new Option("All Satellites", ""));

    for (const satellite of satellites) {
        select.add(new Option(satellite, satellite));
    }

    select.value = satellites.includes(previous) ? previous : "";
}

async function loadSummary() {
    const data = await getJSON("/api/summary");

    $("total").textContent = formatNumber(data.total);
    $("critical").textContent = formatNumber(data.critical);
    $("high").textContent = formatNumber(data.high);
    $("satellites").textContent = formatNumber(data.satellites);

    $("average").textContent =
        `${formatNumber(data.average_score)} / 100`;

    renderRiskChart(data);
    renderSatelliteChart(data);
}

async function loadRecords() {
    const params = new URLSearchParams({
        search: $("search").value.trim(),
        category: $("category").value,
        satellite: $("satellite").value
    });

    $("recordCount").textContent = "Loading assessment records...";

    const data = await getJSON(`/api/records?${params.toString()}`);

    activeRecords = Array.isArray(data.records) ? data.records : [];

    $("recordCount").textContent =
        `${formatNumber(data.total)} matching records (showing up to 500)`;

    renderRows(activeRecords, "recordBody", [
        "record_id",
        "satellite_id",
        "debris_distance_km",
        "risk_score",
        "risk_category",
        "risk_reasons"
    ]);
}

async function loadHighRisk() {
    const data = await getJSON("/api/high-risk");
    const records = Array.isArray(data.records) ? data.records : [];

    $("alertCount").textContent = formatNumber(records.length);

    renderRows(records, "highRiskBody", [
        "record_id",
        "satellite_id",
        "risk_score",
        "risk_category",
        "risk_reasons"
    ]);
}

async function refreshDashboard() {
    if (loading) return;

    setRefreshing(true);
    clearError();

    try {
        await Promise.all([
            loadSummary(),
            loadRecords(),
            loadHighRisk()
        ]);

        $("lastUpdated").textContent =
            `Last updated ${new Date().toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit"
            })}`;
    } catch (error) {
        console.error("Dashboard loading error:", error);

        setError(
            `${error.message}. Ensure Flask is running and its API endpoints are available.`
        );
    } finally {
        setRefreshing(false);
    }
}

async function applyFilters() {
    clearError();

    try {
        await loadRecords();
    } catch (error) {
        console.error("Filter error:", error);
        setError(`Unable to load filtered records: ${error.message}`);
    }
}

$("apply").addEventListener("click", applyFilters);

$("search").addEventListener("keydown", event => {
    if (event.key === "Enter") applyFilters();
});

$("category").addEventListener("change", applyFilters);
$("satellite").addEventListener("change", applyFilters);

$("refreshButton").addEventListener("click", refreshDashboard);
$("retryButton").addEventListener("click", refreshDashboard);

$("menuToggle").addEventListener("click", () => {
    const sidebar = $("sidebar");
    const isOpen = sidebar.classList.toggle("open");

    $("menuToggle").setAttribute("aria-expanded", String(isOpen));
});

document.querySelectorAll(".nav-link").forEach(link => {
    link.addEventListener("click", () => {
        document.querySelectorAll(".nav-link").forEach(item => {
            item.classList.remove("active");
        });

        link.classList.add("active");
        $("sidebar").classList.remove("open");
        $("menuToggle").setAttribute("aria-expanded", "false");
    });
});

refreshDashboard();
