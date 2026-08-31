class ClimateReportCard extends HTMLElement {
  setConfig(config) {
    this.config = {
      entity: "sensor.climate_report_last_report",
      mode: "normal",
      navigation_path: "/app/9d838440_climate_report",
      ...config,
    };
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  getCardSize() { return this.config?.mode === "compact" ? 2 : this.config?.mode === "detailed" ? 5 : 3; }

  render() {
    if (!this.config || !this._hass) return;
    const state = this._hass.states[this.config.entity];
    const a = state?.attributes || {};
    const value = (v, unit, digits = 1) => v == null ? "—" : `${Number(v).toFixed(digits)} ${unit}`;
    const delta = (v, unit, digits = 1) => v == null ? "Sin comparativa" : `${Number(v) >= 0 ? "↗ +" : "↘ "}${Number(v).toFixed(digits)} ${unit}`;
    const warnings = Array.isArray(a.warnings) ? a.warnings.length : 0;
    const detailed = this.config.mode === "detailed";
    const compact = this.config.mode === "compact";
    this.innerHTML = `<ha-card tabindex="0">
      <style>
        ha-card{padding:18px;cursor:pointer;color:var(--primary-text-color);overflow:hidden}header{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.eyebrow{color:var(--primary-color);font-size:11px;font-weight:750;letter-spacing:.1em;text-transform:uppercase}.coverage{font-size:12px;color:var(--secondary-text-color)}h2{margin:5px 0 0;font:500 25px Georgia,serif}.period{margin-top:3px;color:var(--secondary-text-color);font-size:12px}.metrics{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:16px}.metric b{display:block;font:500 28px Georgia,serif}.metric span,.delta span{color:var(--secondary-text-color);font-size:11px}.comparisons{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:13px}.delta{padding:9px;border-radius:10px;background:color-mix(in srgb,var(--primary-color) 8%,transparent)}.delta b{display:block;font-size:13px}.details{margin-top:13px;padding-top:12px;border-top:1px solid var(--divider-color);font-size:12px;color:var(--secondary-text-color)}footer{display:flex;justify-content:space-between;margin-top:14px;color:var(--primary-color);font-size:12px;font-weight:700}.warning{color:var(--warning-color)}.compact .metrics{margin-top:10px}.compact .comparisons,.compact .details{display:none}
      </style>
      <div class="${compact ? "compact" : ""}"><header><div><div class="eyebrow">Climate Report</div><h2>Clima semanal</h2><div class="period">${a.period || "Informe aún no disponible"}</div></div><div class="coverage">${a.coverage == null ? "—" : `${Math.round(a.coverage * 100)} % datos`}</div></header>
      <div class="metrics"><div class="metric"><b>${value(a.mean_temperature,"°C")}</b><span>Temperatura media</span></div><div class="metric"><b>${value(a.mean_humidity,"%",0)}</b><span>Humedad media</span></div></div>
      <div class="comparisons"><div class="delta"><b>${delta(a.temperature_year_delta,"°C")}</b><span>Temperatura interanual</span></div><div class="delta"><b>${delta(a.humidity_year_delta,"pp",0)}</b><span>Humedad interanual</span></div></div>
      ${detailed ? `<div class="details">Mín. ${value(a.minimum_temperature,"°C")} · Máx. ${value(a.peak_temperature,"°C")}<br>${a.excluded_rooms?.length ? `Fuera del resumen: ${a.excluded_rooms.join(", ")}` : "Todos los espacios incluidos"}</div>` : ""}
      <footer><span class="${warnings ? "warning" : ""}">${warnings ? `${warnings} aviso${warnings === 1 ? "" : "s"}` : "Sin avisos"}</span><span>Ver informe →</span></footer></div>
    </ha-card>`;
    this.querySelector("ha-card").onclick = () => {
      history.pushState(null, "", this.config.navigation_path);
      window.dispatchEvent(new Event("location-changed"));
    };
  }

  static getStubConfig() { return { entity: "sensor.climate_report_last_report", mode: "normal" }; }
}

customElements.define("climate-report-card", ClimateReportCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "climate-report-card",
  name: "Climate Report",
  description: "Resumen semanal con comparación interanual y acceso al informe.",
  preview: true,
});
