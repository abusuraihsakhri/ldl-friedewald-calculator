/* Pure, offline LDL-C calculation engine. All internal concentrations use mg/dL. */
(function (root) {
  "use strict";
  const CHOLESTEROL_FACTOR = 38.67;
  const TRIGLYCERIDE_FACTOR = 88.57;
  function normalize(tc, hdl, tg, unit) {
    const inputs = [tc, hdl, tg].map(Number);
    if ([tc, hdl, tg].some(v => v === "" || v === null || v === undefined) ||
        inputs.some(v => !Number.isFinite(v) || v < 0)) {
      throw new Error("All three measurements must be finite, non-negative numbers.");
    }
    if (unit !== "mg/dL" && unit !== "mmol/L") {
      throw new Error("Choose mg/dL or mmol/L.");
    }
    const [c, h, t] = unit === "mmol/L"
      ? [inputs[0] * CHOLESTEROL_FACTOR, inputs[1] * CHOLESTEROL_FACTOR, inputs[2] * TRIGLYCERIDE_FACTOR]
      : inputs;
    if (h > c) throw new Error("HDL cholesterol cannot exceed total cholesterol.");
    return { tc: c, hdl: h, tg: t, nonHdl: c - h };
  }
  function calculate(tc, hdl, tg, unit = "mg/dL") {
    const x = normalize(tc, hdl, tg, unit);
    const fried = x.nonHdl - x.tg / 5;
    const nih = x.tc / 0.948 - x.hdl / 0.971 -
      (x.tg / 8.56 + x.tg * x.nonHdl / 2140 - x.tg * x.tg / 16100) - 9.44;
    function estimate(raw, upper, name) {
      const reason = x.tg >= upper
        ? name + " cannot be reported for triglycerides ≥" + upper + " mg/dL."
        : raw < 0 ? "Equation yields a negative estimate; do not report as zero." : null;
      return { value: reason ? null : raw / (unit === "mmol/L" ? CHOLESTEROL_FACTOR : 1), reason };
    }
    return {
      unit,
      nonHdl: x.nonHdl / (unit === "mmol/L" ? CHOLESTEROL_FACTOR : 1),
      friedewald: estimate(fried, 400, "Friedewald"),
      sampson: estimate(nih, 800, "Sampson-NIH"),
    };
  }
  const api = Object.freeze({ calculate, normalize });
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.LDLCalculator = api;
})(typeof window !== "undefined" ? window : null);
