import React, { useState } from "react";

export default function WeatherVerificationCard({ weather, t }) {
  const [hoveredIdx, setHoveredIdx] = useState(null);

  if (!weather || weather.weather_available === false) {
    return (
      <div
        className="report-section conclusion-section"
        style={{
          marginTop: "24px",
          backgroundColor: "#f8fafc",
          border: "1px solid #e2e8f0",
          borderRadius: "10px",
          padding: "20px",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "10px",
            marginBottom: "10px",
          }}
        >
          <h2 style={{ margin: 0, fontSize: "16px", color: "#0f172a", fontWeight: 700 }}>
            {t("weatherVerification") || "Weather Verification"}
          </h2>
          <span
            style={{
              display: "inline-block",
              backgroundColor: "#f1f5f9",
              color: "#64748b",
              padding: "4px 12px",
              borderRadius: "14px",
              fontSize: "12px",
              fontWeight: 600,
              border: "1px solid #cbd5e1",
            }}
          >
            {t("weatherDataUnavailable") || "Weather data unavailable"}
          </span>
        </div>
        <p style={{ color: "#64748b", fontSize: "14px", margin: "4px 0 0", lineHeight: 1.5 }}>
          {weather?.weather_summary ||
            t("weatherUnavailableDesc") ||
            "Meteorological observations from ECMWF ERA5-Land are unavailable for this location or date range."}
        </p>
      </div>
    );
  }

  const {
    rainfall_mm = 0,
    historical_rainfall_mm = 0,
    rainfall_anomaly_pct = 0,
    temperature_c = 0,
    historical_temperature_c = 0,
    temperature_anomaly_c = 0,
    weather_consistency_score = 0,
    weather_summary = "",
    event_supported = null,
    daily_records = [],
  } = weather;

  // SVG Chart Dimensions
  const svgWidth = 620;
  const svgHeight = 220;
  const padLeft = 46;
  const padRight = 46;
  const padTop = 26;
  const padBottom = 38;
  const plotWidth = svgWidth - padLeft - padRight;
  const plotHeight = svgHeight - padTop - padBottom;

  const numDays = daily_records.length;
  const maxRain = Math.max(
    ...daily_records.map((d) => Number(d.rainfall_mm) || 0),
    10.0
  );
  const minTemp = Math.min(
    ...daily_records.map((d) => Number(d.temperature_c) || 0),
    10.0
  );
  const maxTemp = Math.max(
    ...daily_records.map((d) => Number(d.temperature_c) || 0),
    35.0
  );
  const tempSpan = Math.max(maxTemp - minTemp, 5.0);

  // Helper coordinate getters
  const getX = (idx) => padLeft + (idx + 0.5) * (plotWidth / Math.max(numDays, 1));
  const getBarX = (idx) => {
    const colW = plotWidth / Math.max(numDays, 1);
    const barW = Math.min(32, colW * 0.45);
    return getX(idx) - barW / 2;
  };
  const getBarW = () => {
    const colW = plotWidth / Math.max(numDays, 1);
    return Math.min(32, colW * 0.45);
  };
  const getRainY = (val) => padTop + plotHeight - (val / maxRain) * plotHeight;
  const getTempY = (val) =>
    padTop + plotHeight - ((val - minTemp) / tempSpan) * plotHeight;

  // Temperature line points
  const tempPoints = daily_records
    .map((d, i) => `${getX(i).toFixed(1)},${getTempY(Number(d.temperature_c)).toFixed(1)}`)
    .join(" ");

  return (
    <div
      className="report-section conclusion-section"
      style={{
        marginTop: "24px",
        backgroundColor: "#ffffff",
        border: "1px solid #e2e8f0",
        borderRadius: "12px",
        padding: "24px",
        boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "10px",
          marginBottom: "16px",
          borderBottom: "1px solid #f1f5f9",
          paddingBottom: "14px",
        }}
      >
        <div>
          <h2 style={{ margin: 0, fontSize: "16px", color: "#0f172a", fontWeight: 700 }}>
            {t("weatherVerification") || "Weather Verification"}
          </h2>
          <span style={{ fontSize: "12px", color: "#64748b" }}>
            {t("weatherVerificationDesc") ||
              "Google Earth Engine ERA5-Land meteorological analysis & baseline comparison"}
          </span>
        </div>

        {event_supported === true ? (
          <span
            style={{
              backgroundColor: "#f0fdf4",
              color: "#166534",
              padding: "4px 10px",
              borderRadius: "4px",
              fontSize: "12px",
              fontWeight: 600,
              border: "1px solid #bbf7d0",
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <span style={{ width: "7px", height: "7px", borderRadius: "50%", background: "#16a34a", display: "inline-block" }}></span>
            {t("eventSupported") || "Claim Supported by Weather"}
          </span>
        ) : event_supported === false ? (
          <span
            style={{
              backgroundColor: "#fffbeb",
              color: "#92400e",
              padding: "4px 10px",
              borderRadius: "4px",
              fontSize: "12px",
              fontWeight: 600,
              border: "1px solid #fde68a",
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <span style={{ width: "7px", height: "7px", borderRadius: "50%", background: "#d97706", display: "inline-block" }}></span>
            {t("eventNotSupported") || "Low Weather Correlation"}
          </span>
        ) : (
          <span
            style={{
              backgroundColor: "#f1f5f9",
              color: "#475569",
              padding: "4px 10px",
              borderRadius: "4px",
              fontSize: "12px",
              fontWeight: 600,
              border: "1px solid #cbd5e1",
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <span style={{ width: "7px", height: "7px", borderRadius: "50%", background: "#94a3b8", display: "inline-block" }}></span>
            {t("weatherInconclusive") || "Inconclusive"}
          </span>
        )}
      </div>

      {/* Metrics Row */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "14px",
          marginBottom: "18px",
        }}
      >
        {/* Rainfall Card */}
        <div
          style={{
            backgroundColor: "#f0f9ff",
            border: "1px solid #bae6fd",
            borderRadius: "6px",
            padding: "14px",
          }}
        >
          <span
            style={{
              fontSize: "12px",
              fontWeight: 600,
              color: "#0369a1",
              textTransform: "uppercase",
              letterSpacing: "0.5px",
            }}
          >
            {t("eventRainfall") || "Event Rainfall"}
          </span>
          <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginTop: "4px" }}>
            <strong style={{ fontSize: "22px", color: "#0c4a6e" }}>
              {rainfall_mm} <span style={{ fontSize: "14px", fontWeight: 500 }}>mm</span>
            </strong>
            <span
              style={{
                fontSize: "12px",
                fontWeight: 700,
                color: rainfall_anomaly_pct >= 0 ? "#0284c7" : "#d97706",
              }}
            >
              {rainfall_anomaly_pct > 0 ? `+${rainfall_anomaly_pct}%` : `${rainfall_anomaly_pct}%`}
            </span>
          </div>
          <div style={{ fontSize: "11px", color: "#64748b", marginTop: "4px" }}>
            {t("historicalAvg") || "Baseline"}: {historical_rainfall_mm} mm
          </div>
        </div>

        {/* Temperature Card */}
        <div
          style={{
            backgroundColor: "#fffbeb",
            border: "1px solid #fde68a",
            borderRadius: "6px",
            padding: "14px",
          }}
        >
          <span
            style={{
              fontSize: "12px",
              fontWeight: 600,
              color: "#b45309",
              textTransform: "uppercase",
              letterSpacing: "0.5px",
            }}
          >
            {t("eventTemperature") || "Mean Temperature"}
          </span>
          <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginTop: "4px" }}>
            <strong style={{ fontSize: "22px", color: "#78350f" }}>
              {temperature_c} <span style={{ fontSize: "14px", fontWeight: 500 }}>°C</span>
            </strong>
            <span
              style={{
                fontSize: "12px",
                fontWeight: 700,
                color: temperature_anomaly_c >= 0 ? "#ea580c" : "#0284c7",
              }}
            >
              {temperature_anomaly_c > 0 ? `+${temperature_anomaly_c}°C` : `${temperature_anomaly_c}°C`}
            </span>
          </div>
          <div style={{ fontSize: "11px", color: "#64748b", marginTop: "4px" }}>
            {t("historicalAvg") || "Baseline"}: {historical_temperature_c} °C
          </div>
        </div>

        {/* Consistency Score Card */}
        <div
          style={{
            backgroundColor: "#f0fdf4",
            border: "1px solid #bbf7d0",
            borderRadius: "6px",
            padding: "14px",
          }}
        >
          <span
            style={{
              fontSize: "12px",
              fontWeight: 600,
              color: "#15803d",
              textTransform: "uppercase",
              letterSpacing: "0.5px",
            }}
          >
            {t("weatherConsistencyScore") || "Consistency Score"}
          </span>
          <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginTop: "4px" }}>
            <strong style={{ fontSize: "22px", color: "#14532d" }}>
              {weather_consistency_score}{" "}
              <span style={{ fontSize: "14px", fontWeight: 500 }}>/ 100</span>
            </strong>
          </div>
          <div style={{ fontSize: "11px", color: "#64748b", marginTop: "4px" }}>
            {event_supported ? "High event plausibility" : "Independent reviewer triage"}
          </div>
        </div>
      </div>

      {/* Meteorological Summary Box */}
      {weather_summary && (
        <div
          style={{
            backgroundColor: "#f8fafc",
            borderLeft: "4px solid #0284c7",
            borderRadius: "6px",
            padding: "12px 16px",
            marginBottom: "20px",
          }}
        >
          <div style={{ fontSize: "13px", fontWeight: 700, color: "#0f172a", marginBottom: "4px" }}>
            {t("weatherSummary") || "Meteorological Summary"}
          </div>
          <p style={{ margin: 0, fontSize: "13.5px", color: "#334155", lineHeight: 1.5 }}>
            {weather_summary}
          </p>
        </div>
      )}

      {/* Daily Time-Series Chart */}
      {daily_records.length > 0 && (
        <div style={{ marginTop: "10px" }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "8px",
              marginBottom: "8px",
            }}
          >
            <span style={{ fontSize: "13px", fontWeight: 700, color: "#1e293b" }}>
              {t("weatherTimeSeries") || "Daily Rainfall & Temperature Profile"}
            </span>
            <div style={{ display: "flex", gap: "16px", fontSize: "12px" }}>
              <span style={{ display: "flex", alignItems: "center", gap: "5px", color: "#0284c7" }}>
                <span
                  style={{
                    display: "inline-block",
                    width: "12px",
                    height: "12px",
                    backgroundColor: "#38bdf8",
                    borderRadius: "2px",
                  }}
                />
                {t("dailyRainfall") || "Daily Rainfall (mm)"}
              </span>
              <span style={{ display: "flex", alignItems: "center", gap: "5px", color: "#ea580c" }}>
                <span
                  style={{
                    display: "inline-block",
                    width: "12px",
                    height: "3px",
                    backgroundColor: "#f97316",
                  }}
                />
                {t("dailyTemperature") || "Daily Temp (°C)"}
              </span>
            </div>
          </div>

          <div
            style={{
              overflowX: "auto",
              backgroundColor: "#fcfdfd",
              border: "1px solid #f1f5f9",
              borderRadius: "8px",
              padding: "10px 4px",
            }}
          >
            <svg
              viewBox={`0 0 ${svgWidth} ${svgHeight}`}
              style={{ width: "100%", height: "auto", minWidth: "480px", display: "block" }}
            >
              {/* Horizontal Gridlines */}
              {[0, 0.25, 0.5, 0.75, 1.0].map((frac, idx) => {
                const y = padTop + frac * plotHeight;
                const rainVal = (maxRain * (1.0 - frac)).toFixed(0);
                const tempVal = (minTemp + tempSpan * (1.0 - frac)).toFixed(0);
                return (
                  <g key={idx}>
                    <line
                      x1={padLeft}
                      y1={y}
                      x2={svgWidth - padRight}
                      y2={y}
                      stroke="#e2e8f0"
                      strokeDasharray="3 3"
                    />
                    <text
                      x={padLeft - 6}
                      y={y + 3}
                      fontSize="10"
                      fill="#64748b"
                      textAnchor="end"
                    >
                      {rainVal}
                    </text>
                    <text
                      x={svgWidth - padRight + 6}
                      y={y + 3}
                      fontSize="10"
                      fill="#ea580c"
                      textAnchor="start"
                    >
                      {tempVal}°
                    </text>
                  </g>
                );
              })}

              {/* Rainfall Bars */}
              {daily_records.map((d, i) => {
                const rain = Number(d.rainfall_mm) || 0;
                const barX = getBarX(i);
                const barW = getBarW();
                const barH = (rain / maxRain) * plotHeight;
                const barY = padTop + plotHeight - barH;
                const isHovered = hoveredIdx === i;

                return (
                  <rect
                    key={`bar-${i}`}
                    x={barX}
                    y={barY}
                    width={barW}
                    height={Math.max(barH, 1.5)}
                    rx="3"
                    fill={isHovered ? "#0284c7" : "#38bdf8"}
                    style={{ cursor: "pointer", transition: "fill 0.15s" }}
                    onMouseEnter={() => setHoveredIdx(i)}
                    onMouseLeave={() => setHoveredIdx(null)}
                  />
                );
              })}

              {/* Temperature Line */}
              {daily_records.length > 1 && (
                <polyline
                  fill="none"
                  stroke="#f97316"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  points={tempPoints}
                />
              )}

              {/* Temperature Dots & Tooltip Target */}
              {daily_records.map((d, i) => {
                const cx = getX(i);
                const cy = getTempY(Number(d.temperature_c) || 0);
                const isHovered = hoveredIdx === i;

                return (
                  <g key={`dot-${i}`}>
                    <circle
                      cx={cx}
                      cy={cy}
                      r={isHovered ? 5.5 : 3.5}
                      fill="#f97316"
                      stroke="#ffffff"
                      strokeWidth="1.5"
                      style={{ cursor: "pointer" }}
                      onMouseEnter={() => setHoveredIdx(i)}
                      onMouseLeave={() => setHoveredIdx(null)}
                    />
                    {/* X-axis Date Label */}
                    <text
                      x={cx}
                      y={svgHeight - 10}
                      fontSize="10"
                      fill={isHovered ? "#0f172a" : "#64748b"}
                      fontWeight={isHovered ? 700 : 400}
                      textAnchor="middle"
                    >
                      {String(d.date || "").slice(5)}
                    </text>
                  </g>
                );
              })}

              {/* Active Day Hover Tooltip Overlay */}
              {hoveredIdx !== null && daily_records[hoveredIdx] && (
                <g>
                  <rect
                    x={Math.min(Math.max(getX(hoveredIdx) - 60, 4), svgWidth - 124)}
                    y={10}
                    width="120"
                    height="42"
                    rx="6"
                    fill="#1e293b"
                    opacity="0.92"
                  />
                  <text
                    x={Math.min(Math.max(getX(hoveredIdx) - 60, 4) + 60, svgWidth - 64)}
                    y={25}
                    fontSize="10"
                    fill="#ffffff"
                    fontWeight="bold"
                    textAnchor="middle"
                  >
                    {daily_records[hoveredIdx].date}
                  </text>
                  <text
                    x={Math.min(Math.max(getX(hoveredIdx) - 60, 4) + 60, svgWidth - 64)}
                    y={39}
                    fontSize="9.5"
                    fill="#93c5fd"
                    textAnchor="middle"
                  >
                    Rain: {daily_records[hoveredIdx].rainfall_mm}mm | Temp:{" "}
                    {daily_records[hoveredIdx].temperature_c}°C
                  </text>
                </g>
              )}
            </svg>
          </div>
        </div>
      )}

      {/* Data Source Footnote */}
      <div
        style={{
          marginTop: "16px",
          paddingTop: "10px",
          borderTop: "1px dashed #e2e8f0",
          fontSize: "11.5px",
          color: "#94a3b8",
          lineHeight: 1.4,
        }}
      >
        {t("weatherSourceFootnote") ||
          "Data source: ECMWF ERA5-Land Hourly via Google Earth Engine. Baseline: Same calendar window in preceding 2 years."}
      </div>
    </div>
  );
}
