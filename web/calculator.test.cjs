const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const { calculate, normalize } = require("./calculator.js");

test("Friedewald and Sampson-NIH known reference values (mg/dL)", () => {
  const r = calculate(200,50,150);
  assert.equal(r.friedewald.value,120);
  assert.equal(+r.sampson.value.toFixed(2),123.40);
  assert.equal(r.nonHdl,150);
  assert.equal(+calculate(250,35,500).sampson.value.toFixed(2),125.11);
});
test("Friedewald invalid at or above 400; Sampson invalid at or above 800", () => {
  assert.equal(calculate(250,50,399.99).friedewald.reason,null);
  assert.equal(calculate(250,50,400).friedewald.value,null);
  assert.equal(calculate(250,50,400).sampson.reason,null);
  assert.equal(calculate(250,50,800).sampson.value,null);
});
test("negative values, non-finite, and HDL above TC are invalid", () => {
  for (const values of [[-1,30,50],[200,NaN,10],[200,Infinity,10],[100,120,80],["",20,20]]) {
    assert.throws(() => calculate(...values),Error);
  }
  assert.equal(calculate(100,90,100).friedewald.value,null);
  assert.equal(calculate(100,90,100).sampson.value,null);
});
test("mmol/L conversion is consistent with mg/dL result", () => {
  const a=calculate(200,50,150);
  const b=calculate(200/38.67,50/38.67,150/88.57,"mmol/L");
  assert.ok(Math.abs(a.friedewald.value/38.67-b.friedewald.value)<1e-8);
  assert.ok(Math.abs(a.sampson.value/38.67-b.sampson.value)<1e-8);
});
test("HTML references local engine, and no fake audit console", () => {
  const html=fs.readFileSync(path.join(__dirname,"index.html"),"utf8");
  assert.match(html,/src="\.\/calculator\.js"/);
  assert.match(html,/id="lipid-form"/);
  assert.match(html,/id="csv-file"/);
  assert.doesNotMatch(html,/HMAC_SHA256_e83f9a72b941d6c381f9|Air-Gapped Active/);
});

test("inline browser interaction code parses without syntax errors", () => {
  const html=fs.readFileSync(path.join(__dirname,"index.html"),"utf8");
  const scripts=[...html.matchAll(/<script(?:\\s[^>]*)?>([\\s\\S]*?)<\\/script>/g)];
  assert.equal(scripts.length,1);
  new vm.Script(scripts[0][1], { filename:"web/index.html inline script" });
});
