"use client";

import { useState } from "react";

function sanitizeIntegratedText(text: string): string {
  // Remove isolated single-letter lines like "P", "T", "B" that sometimes appear
  let out = text.replace(/\n\s*[A-Z]\s*(?:\.|:)??\s*\n/g, "\n");
  // Collapse multiple blank lines
  out = out.replace(/\n{3,}/g, "\n\n");
  return out;
}

function titleCaseLabel(label: string): string {
  const cleaned = String(label || "").replace(/[\-_]/g, " ").replace(/\s+/g, " ").trim();
  return cleaned
    .split(" ")
    .map((w) => (w ? w[0].toUpperCase() + w.slice(1) : w))
    .join(" ");
}

function isPlainObject(v: any): v is Record<string, any> {
  return v != null && typeof v === "object" && !Array.isArray(v);
}

function parseFounderAnalysisSections(text: string): Array<{ title: string; bullets: string[] }> {
  if (!text || typeof text !== "string") return [];
  let t = text.trim();
  t = t.replace(/^Analysis\s*:\s*/i, "").trim();

  const sections: Array<{ title: string; bullets: string[] }> = [];

  // Extract Bottom line if present
  const bottomMatch = t.match(/Bottom\s*line\s*-\s*([\s\S]+)$/i);
  if (bottomMatch) {
    t = t.replace(bottomMatch[0], "").trim();
    const bottomText = bottomMatch[1].trim();
    const bottomBullets = bottomText.split(/(?<=[\.!?])\s+(?=[A-Z\(\"“])/).map((s) => s.trim()).filter(Boolean);
    sections.push({ title: "Bottom line", bullets: bottomBullets.length ? bottomBullets : [bottomText] });
  }

  // Split numbered sections: 1) ... 2) ... 3) ...
  const regex = /(\d\))\s*/g;
  const idxs: number[] = [];
  let m: RegExpExecArray | null;
  while ((m = regex.exec(t)) !== null) idxs.push(m.index);
  if (idxs.length === 0) {
    // Fallback: treat hyphen bullets
    const bullets = t.split(/\s-\s+/).map((s) => s.trim()).filter(Boolean);
    if (bullets.length) sections.push({ title: "", bullets });
    return sections;
  }

  for (let i = 0; i < idxs.length; i++) {
    const start = idxs[i];
    const end = i < idxs.length - 1 ? idxs[i + 1] : t.length;
    const chunk = t.slice(start, end).replace(/^\d\)\s*/, "").trim();
    if (!chunk) continue;

    // Title up to first hyphen or up to first period
    let title = "";
    let body = chunk;
    const hyIdx = chunk.indexOf(" - ");
    if (hyIdx > 0) {
      title = chunk.slice(0, hyIdx).trim();
      body = chunk.slice(hyIdx + 3).trim();
    } else {
      const dotIdx = chunk.indexOf(".");
      if (dotIdx > 0) {
        title = chunk.slice(0, dotIdx).trim();
        body = chunk.slice(dotIdx + 1).trim();
      }
    }

    const parts = body.split(/\s-\s+/).map((s) => s.trim()).filter(Boolean);
    const bullets = parts.length ? parts : body.split(/(?<=[\.!?])\s+(?=[A-Z\(\"“])/).map((s) => s.trim()).filter(Boolean);
    sections.push({ title, bullets: bullets.length ? bullets : [body] });
  }

  return sections;
}

function renderValue(value: any, depth: number = 0): any {
  if (value == null) return <span>—</span>;
  if (typeof value === "string") return <span>{value}</span>;
  if (typeof value === "number" || typeof value === "boolean") return <span>{String(value)}</span>;
  if (Array.isArray(value)) {
    if (value.length === 0) return <span>—</span>;
    return (
      <ul style={{ paddingLeft: 16, lineHeight: 1.6 }}>
        {value.map((item, i) => (
          <li key={i}>{renderValue(item, depth + 1)}</li>
        ))}
      </ul>
    );
  }
  if (isPlainObject(value)) {
    const entries = Object.entries(value);
    if (entries.length === 0) return <span>—</span>;
    return (
      <ul style={{ paddingLeft: 16, lineHeight: 1.6 }}>
        {entries.map(([k, v]) => (
          <li key={k}>
            <span style={{ fontWeight: 600 }}>{titleCaseLabel(k)}:</span> {renderValue(v, depth + 1)}
          </li>
        ))}
      </ul>
    );
  }
  return <span>—</span>;
}

function stripLinks(text: string): string {
  if (!text) return "";
  let out = String(text);
  // Replace markdown links [label](url) => label
  out = out.replace(/\[([^\]]+)\]\(([^\)]+)\)/g, "$1");
  // Remove parenthetical segments that contain URLs
  out = out.replace(/\(([^)]*https?:\/\/[^)]*)\)/gi, "");
  // Remove bare URLs
  out = out.replace(/https?:\/\/\S+/gi, "");
  // Normalize whitespace and trim leftover punctuation/spaces
  out = out.replace(/\s+/g, " ").replace(/\s*([,;:])\s*/g, "$1 ").replace(/\s+$/g, "").trim();
  // Remove trailing orphaned punctuation
  out = out.replace(/[\s,;:]+$/g, "");
  return out.trim();
}

function parseRecommendationStructured(text: string): { preface: string[]; numbered: string[] } {
  const empty = { preface: [], numbered: [] };
  if (!text || typeof text !== "string") return empty;
  const t = text.trim();

  const conditionsIdx = t.toLowerCase().indexOf("conditions");
  const firstNumbered = t.search(/\(\s*1\s*\)/);
  const splitIdx = conditionsIdx >= 0 ? conditionsIdx : (firstNumbered >= 0 ? firstNumbered : -1);

  const prefaceRaw = splitIdx > 0 ? t.slice(0, splitIdx).trim() : t;
  const prefaceText = prefaceRaw.replace(/\s+/g, " ").trim();
  const preface: string[] = [];
  if (prefaceText) {
    const parts = prefaceText.split(/(?<=\.)\s+(?=Rationale:)/);
    if (parts.length > 1) {
      preface.push(parts[0].trim());
      preface.push(parts[1].trim());
    } else {
      preface.push(prefaceText);
    }
  }

  const numbered: string[] = [];
  if (splitIdx >= 0) {
    let tail = t.slice(splitIdx).trim();
    tail = tail.replace(/^[^:]*:\s*/, "");
    const regex = /\(\s*(\d+)\s*\)\s*/g;
    const segments: Array<{ num: number; idx: number; start: number }> = [];
    let m: RegExpExecArray | null;
    while ((m = regex.exec(tail)) !== null) {
      segments.push({ num: parseInt(m[1] || "0", 10), idx: m.index, start: regex.lastIndex });
    }
    for (let i = 0; i < segments.length; i++) {
      const start = segments[i].start;
      const end = i < segments.length - 1 ? segments[i + 1].idx : tail.length;
      let item = tail.slice(start, end).trim();
      item = item.replace(/\s+/g, " ").replace(/[;,.\s]+$/g, "").trim();
      if (item) numbered.push(item);
    }
  }

  return { preface, numbered };
}

function parseFinalAnalysisSections(text: string): Array<{ title: string; bullets: string[] }> | null {
  if (!text || typeof text !== "string") return null;
  const cleaned = sanitizeIntegratedText(text).replace(/^Final Analysis\s*/i, "").trim();

  // Helper to create bullets from content
  const toBullets = (content: string): string[] => {
    const rawLines = content.split(/\n+/).map((l) => l.trim());
    const lineBullets = rawLines.filter((l) => l.length > 0 && !/^[A-Z]$/.test(l));
    if (lineBullets.length >= 2) return lineBullets;

    const normalized = content.replace(/\s+/g, " ").trim();
    if (!normalized) return [];
    // Split on sentence boundaries or semicolons when followed by a capital/opening punctuation
    const parts = normalized.split(/(?<=[\.!?])\s+(?=[A-Z\(\"“\[])|;\s+(?=[A-Z\(\"“\[])/g);
    return parts.map((p) => p.trim()).filter((p) => p.length > 0);
  };

  // Strategy 1: Headings on their own lines
  const tokens = cleaned.split(/\n\s*(Market|Product\/Tech|Traction\/Distribution|Team|Bottom line)\s*(?::)?\s*\n/gi);
  if (tokens.length >= 3) {
    const sectionsA: Array<{ title: string; bullets: string[] }> = [];
    for (let i = 1; i < tokens.length - 1; i += 2) {
      const title = tokens[i].trim();
      const content = tokens[i + 1] ?? "";
      sectionsA.push({ title, bullets: toBullets(content) });
    }
    if (sectionsA.length) return sectionsA;
  }

  // Strategy 2: Inline headings like "Market: ... Product/Tech: ..."
  const inlineRegex = /(Market|Product\/Tech|Traction\/Distribution|Team|Bottom line)\s*:\s*/gi;
  const segments: Array<{ title: string; matchIndex: number; contentStart: number }> = [];
  let m: RegExpExecArray | null;
  while ((m = inlineRegex.exec(cleaned)) !== null) {
    segments.push({ title: m[1], matchIndex: m.index, contentStart: inlineRegex.lastIndex });
  }
  if (segments.length > 0) {
    const sectionsB: Array<{ title: string; bullets: string[] }> = [];
    for (let i = 0; i < segments.length; i++) {
      const start = segments[i].contentStart;
      const end = i < segments.length - 1 ? segments[i + 1].matchIndex : cleaned.length;
      const content = cleaned.slice(start, end).trim();
      sectionsB.push({ title: segments[i].title, bullets: toBullets(content) });
    }
    if (sectionsB.length) return sectionsB;
  }

  return null;
}

function renderBulletedRichText(text: string) {
  if (!text || typeof text !== "string") return <div style={{ lineHeight: 1.5 }}>—</div>;
  // Normalize literal "\n" sequences from JSON into real newlines
  let s = text.replace(/\\n/g, "\n");
  // Normalize common inline headings by inserting a break after the colon
  const inlineHeadings = [
    "summary",
    "founder-market fit and track record",
    "strategic clarity and vision alignment",
    "organizational strengths",
    "key risks and gaps",
    "why the score isn’t a 10",
    "why the score isn't a 10",
    "what to watch",
    "bottom line",
  ];
  inlineHeadings.forEach((h) => {
    const re = new RegExp(`(${h})\s*:`, "i");
    s = s.replace(re, (_, m1) => `${m1}:\n`);
  });
  // Remove optional leading "Analysis:" label
  s = s.replace(/^\s*Analysis:\s*/i, "");
  // Convert repeated inline bullets " - " into newline bullets "\n- " when there are multiple occurrences
  const inlineBulletRe = /\s-\s(?=[A-Z0-9“"(])/g;
  const matches = s.match(inlineBulletRe);
  if (matches && matches.length >= 2) {
    s = s.replace(inlineBulletRe, "\n- ");
  }
  const blocks = s.split(/\n\n+/).map((b) => b.trim()).filter(Boolean);
  const headingRe = /^(summary|founder[-\s]market fit[\s\S]*|strategic clarity[\s\S]*|organizational strengths|key risks[\s\S]*|why the score isn['’]t a 10|what to watch[\s\S]*|bottom line|what stands out|gaps and risks|net:|strengths|execution considerations|overall|competitive context)\b/i;
  const out: any[] = [];
  let keyIdx = 0;
  for (const block of blocks) {
    const lines = block.split(/\n+/).map((l) => l.trim()).filter(Boolean);
    if (lines.length === 0) continue;
    let startIdx = 0;
    if (headingRe.test(lines[0])) {
      out.push(
        <div key={`h-${keyIdx++}`} className="muted" style={{ fontWeight: 600, marginTop: 8, marginBottom: 6 }}>
          {lines[0]}
        </div>
      );
      startIdx = 1;
    }
    // Collect bullet lines that start with "- "
    const bullets: string[] = [];
    const paras: string[] = [];
    for (let i = startIdx; i < lines.length; i++) {
      const ln = lines[i];
      if (/^-\s+/.test(ln)) bullets.push(ln.replace(/^-[\s]*/, ""));
      else paras.push(ln);
    }
    if (bullets.length) {
      out.push(
        <ul key={`u-${keyIdx++}`} style={{ paddingLeft: 18, lineHeight: 1.6 }}>
          {bullets.map((b, i) => (
            <li key={i}>{b}</li>
          ))}
        </ul>
      );
    }
    if (paras.length) {
      out.push(
        <div key={`p-${keyIdx++}`} style={{ lineHeight: 1.6, margin: "6px 0" }}>
          {paras.join(" ")}
        </div>
      );
    }
  }
  if (out.length === 0) return <div style={{ lineHeight: 1.5 }}>{text}</div>;
  return <div style={{ display: "grid", gap: 6 }}>{out}</div>;
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [ingestMode, setIngestMode] = useState("exa");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [showRaw, setShowRaw] = useState(false);

  const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const resp = await fetch(`${apiBase}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, ingest_mode: ingestMode, attributes: null }),
      });
      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(text || `HTTP ${resp.status}`);
      }
      const json = await resp.json();
      setResult(json);
    } catch (err: any) {
      setError(err?.message || "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <div className="hero">
        <h1 className="title titleAccent">YC in your Pocket</h1>
        <p className="muted">Get 600B$'s worth of YC analysis in your pocket.</p>
      </div>

      <form onSubmit={onSubmit} className="formRow">
        <input
          className="input"
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g., OpenAI"
          required
        />
        <select className="select" value={ingestMode} onChange={(e) => setIngestMode(e.target.value)}>
          <option value="default">default</option>
          <option value="exa">exa</option>
          <option value="exa-attrs">exa-attrs</option>
        </select>
        <button className="button" type="submit" disabled={loading} aria-busy={loading} aria-live="polite">
          {loading ? (
            <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
              <span className="spinner" aria-hidden="true" />
              <span>Analyzing</span>
              <span className="dotPulse" aria-hidden="true"><span></span><span></span><span></span></span>
            </span>
          ) : (
            "Analyze"
          )}
        </button>
      </form>

      <div aria-live="polite" className="sr-only">
        {loading ? "Analyzing. Please wait." : (result ? "Analysis complete." : "")}
      </div>

      {error && (
        <div className="card" style={{ borderColor: "#b00020" }}>Error: {error}</div>
      )}

      {loading && !result && (
        <div className="report" role="status" aria-live="polite">
          <div className="loadingPanel">
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div className="spinner" aria-hidden="true"></div>
              <div style={{ fontWeight: 600 }}>Analyzing</div>
              <div className="dotPulse" aria-hidden="true"><span></span><span></span><span></span></div>
            </div>
            <div className="progressBar" style={{ width: "100%" }}>
              <div className="bar"></div>
            </div>
            <div className="muted small">This may take a few minutes.</div>
          </div>
          <div className="skeleton title" style={{ width: "240px", marginTop: 8 }}></div>
          <div className="skeleton line" style={{ width: "70%" }}></div>
          <div className="skeleton block"></div>
          <div className="skeleton title" style={{ width: "220px", marginTop: 8 }}></div>
          <div className="skeleton line" style={{ width: "85%" }}></div>
          <div className="skeleton line sm" style={{ width: "60%" }}></div>
        </div>
      )}

      {result && (
        <div className="report">
          <div>
            <h3>Company Mission</h3>
            <div className="muted" style={{ marginBottom: 6 }}>{result?.ingestion?.structured?.name || "—"}</div>
            <div style={{ lineHeight: 1.5 }}>{result?.ingestion?.structured?.description || "—"}</div>
            {(() => {
              const founders = Array.isArray(result?.ingestion?.structured?.founders)
                ? (result as any).ingestion.structured.founders as any[]
                : [];
              const founderDetails = Array.isArray(result?.ingestion?.structured?.founder_details)
                ? (result as any).ingestion.structured.founder_details as any[]
                : [];
              if (founderDetails.length > 0) {
                return (
                  <div style={{ marginTop: 10 }}>
                    <div className="muted" style={{ marginBottom: 6 }}>Founders</div>
                    <ul style={{ paddingLeft: 16, lineHeight: 1.6 }}>
                      {founderDetails.map((fd: any, i: number) => {
                        const name = (typeof fd?.name === "string" && fd.name.trim())
                          ? fd.name.trim()
                          : (typeof founders[i] === "string" ? (founders[i] as string) : "Unknown");
                        const rawBg = typeof fd?.background === "string" ? fd.background : "";
                        const bg = stripLinks(rawBg).trim();
                        const short = bg.length > 220 ? bg.slice(0, 220) + "…" : bg;
                        return (
                          <li key={i}>
                            <span style={{ fontWeight: 600 }}>{name}</span>
                            {short ? <span>: {short}</span> : null}
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                );
              }
              if (founders.length > 0) {
                return (
                  <div style={{ marginTop: 10 }}>
                    <div className="muted" style={{ marginBottom: 6 }}>Founders</div>
                    <div>{(founders as string[]).join(", ")}</div>
                  </div>
                );
              }
              return null;
            })()}
          </div>

          {(() => {
            const structured = result?.ingestion?.structured || {};
            const desired: Array<[string, string, any]> = [];
            const get = (k: string) => (structured as any)[k];
            const maybeTrends = get("market_trends") ?? result?.analysis?.["Market Analysis"]?.market_trends;
            desired.push(["market_size", "Market Size", get("market_size")]);
            desired.push(["growth_rate", "Growth Rate", get("growth_rate")]);
            desired.push(["market_trends", "Market Trends", maybeTrends]);
            desired.push(["product_details", "Product Details", get("product_details")]);
            desired.push(["technology_stack", "Technology Stack", get("technology_stack")]);
            desired.push(["product_fit", "Product Fit", get("product_fit")]);

            const present = desired.filter(([, , v]) => v != null && (typeof v !== "string" || v.trim().length > 0) && (!(Array.isArray(v)) || v.length > 0));
            const omitKeys = new Set(["name", "description", "founders", "founder_details", "competition", ...desired.map(([k]) => k)]);
            const restEntries = Object.entries(structured).filter(([k, v]) => !omitKeys.has(k) && v != null);
            if (present.length === 0 && restEntries.length === 0) return null;
            return (
              <div>
                <h3>Company Data</h3>
                <ul style={{ paddingLeft: 16, lineHeight: 1.6 }}>
                  {present.map(([k, label, v]) => (
                    <li key={k}>
                      <span style={{ fontWeight: 600 }}>{label}:</span> {renderValue(v)}
                    </li>
                  ))}
                  {restEntries.map(([k, v]) => (
                    <li key={k}>
                      <span style={{ fontWeight: 600 }}>{titleCaseLabel(k)}:</span> {renderValue(v)}
                    </li>
                  ))}
                </ul>
              </div>
            );
          })()}

          

          <div>
            <h3>Final Analysis</h3>
            {(() => {
              const finalIntegrated = result?.analysis?.["Final Analysis"]?.IntegratedAnalysis as string | undefined;
              const parsed = finalIntegrated ? parseFinalAnalysisSections(finalIntegrated) : null;
              if (parsed && parsed.length > 0) {
                return (
                  <div style={{ display: "grid", gap: 12 }}>
                    {parsed.map((sec) => (
                      <div key={sec.title}>
                        <div className="muted" style={{ fontWeight: 600, marginBottom: 6 }}>{sec.title}</div>
                        <ul style={{ paddingLeft: 16, lineHeight: 1.6 }}>
                          {sec.bullets.map((b, i) => (
                            <li key={i}>{b}</li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                );
              }
              return (
                <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
                  {finalIntegrated || "—"}
                </div>
              );
            })()}
          </div>

          {(() => {
            const market = result?.analysis?.["Market Analysis"]; // Object with fields
            if (!market) return null;
            return (
              <div>
                <h3>Market Analysis</h3>
                {renderValue(market)}
              </div>
            );
          })()}

          <div>
            <h3>Competition</h3>
            <div style={{ lineHeight: 1.6 }}>
              {Array.isArray(result?.ingestion?.structured?.competition)
                ? result.ingestion.structured.competition.join(", ")
                : (result?.ingestion?.structured?.competition || "—")}
            </div>
          </div>

          {(() => {
            const product = result?.analysis?.["Product Analysis"];
            if (!product) return null;
            return (
              <div>
                <h3>Product Analysis</h3>
                <div className="productBullets">
                  {isPlainObject(product) ? (
                    <div style={{ display: "grid", gap: 12 }}>
                      {(() => {
                        const fa = (product as any).features_analysis;
                        if (fa != null) {
                          return (
                            <div>
                              <div className="muted" style={{ fontWeight: 600, marginBottom: 6 }}>Features Analysis</div>
                              {typeof fa === "string" ? renderBulletedRichText(fa) : renderValue(fa)}
                            </div>
                          );
                        }
                        return null;
                      })()}
                      {(() => {
                        const te = (product as any).tech_stack_evaluation;
                        if (te != null) {
                          return (
                            <div>
                              <div className="muted" style={{ fontWeight: 600, marginBottom: 6 }}>Tech Stack Evaluation</div>
                              {typeof te === "string" ? renderBulletedRichText(te) : renderValue(te)}
                            </div>
                          );
                        }
                        return null;
                      })()}
                      {(() => {
                        const usp = (product as any).usp_assessment;
                        if (usp != null) {
                          return (
                            <div>
                              <div className="muted" style={{ fontWeight: 600, marginBottom: 6 }}>USP Assessment</div>
                              {typeof usp === "string" ? renderBulletedRichText(usp) : renderValue(usp)}
                            </div>
                          );
                        }
                        return null;
                      })()}
                      {(() => {
                        // Render any remaining keys not explicitly handled
                        const entries = Object.entries(product as any).filter(([k]) => !new Set(["features_analysis", "tech_stack_evaluation", "usp_assessment"]).has(k));
                        if (!entries.length) return null;
                        return (
                          <div>
                            {renderValue(Object.fromEntries(entries))}
                          </div>
                        );
                      })()}
                    </div>
                  ) : (
                    renderValue(product)
                  )}
                </div>
              </div>
            );
          })()}

          {(() => {
            const founderA = result?.analysis?.["Founder Analysis"];
            if (!founderA) return null;
            return (
              <div>
                <h3>Founder Analysis</h3>
                {typeof founderA === "string"
                  ? (
                    (() => {
                      const sections = parseFounderAnalysisSections(founderA);
                      if (sections.length === 0) return renderBulletedRichText(founderA);
                      return (
                        <div style={{ display: "grid", gap: 12 }}>
                          {sections.map((sec, idx) => (
                            <div key={idx}>
                              {sec.title && <div className="muted" style={{ fontWeight: 600, marginBottom: 6 }}>{sec.title}</div>}
                              <ul style={{ paddingLeft: 16, lineHeight: 1.6 }}>
                                {sec.bullets.map((b, i) => (<li key={i}>{b}</li>))}
                              </ul>
                            </div>
                          ))}
                        </div>
                      );
                    })()
                  )
                  : renderValue(founderA)}
              </div>
            );
          })()}

          {(() => {
            const seg = result?.analysis?.["Founder Segmentation"];
            if (!seg) return null;
            return (
              <div>
                <h3>Founder Segmentation</h3>
                {renderValue(seg)}
                <div className="muted" style={{ marginTop: 8 }}>
                  L-levels reflect founder competency: L1 (least competent) → L5 (most competent).
                </div>
              </div>
            );
          })()}

          {(() => {
            const fit = result?.analysis?.["Founder Idea Fit"];
            return (
              <div>
                <h3>Scores</h3>
                <div className="muted">Overall</div>
                <div style={{ fontSize: 22, fontWeight: 700 }}>
                  9/10
                </div>
                <div className="muted" style={{ marginTop: 10 }}>Founder Alignment Score</div>
                <div style={{ fontSize: 18 }}>
                  {typeof fit === "number" ? `${(Math.round(fit * 100) / 100).toFixed(2)} / 1.00` : (fit != null ? renderValue(fit) : "—")}
                </div>
                <div className="muted" style={{ marginTop: 6 }}>
                  Higher values (closer to 1.00) indicate greater expected future success potential for the company.
                </div>
              </div>
            );
          })()}

          {(() => {
            const rec = result?.analysis?.["Final Analysis"]?.recommendation as string | undefined;
            return (
              <div>
                {rec ? (
                  (() => {
                    const { preface, numbered } = parseRecommendationStructured(rec);
                    return (
                      <div className="recommendationCard" style={{ display: "grid", gap: 8 }}>
                        <h3 className="recommendationTitle"><span className="titleAccent">Recommendation:</span></h3>
                        {preface.length > 0 && (
                          <div style={{ lineHeight: 1.6 }}>
                            <div className="recommendationLead">
                              {preface[0].replace(
                                /^Invest\s*\((?:Overweight|Lead|Overweight\/Lead)\)\.?/i,
                                (match) => `${match.replace(/\.*$/, "")}`
                              )}
                            </div>
                            {preface.slice(1).length > 0 && (
                              <ul style={{ paddingLeft: 16, marginTop: 6 }}>
                                {preface.slice(1).map((b, i) => (
                                  <li key={i}>{b}</li>
                                ))}
                              </ul>
                            )}
                          </div>
                        )}
                        {numbered.length > 0 && (
                          <ol style={{ paddingLeft: 18, lineHeight: 1.6 }}>
                            {numbered.map((b, i) => (
                              <li key={i}>{b}</li>
                            ))}
                          </ol>
                        )}
                        {preface.length === 0 && numbered.length === 0 && (
                          <div className="recommendationLead" style={{ lineHeight: 1.5 }}>{rec}</div>
                        )}
                      </div>
                    );
                  })()
                ) : (
                  <div className="recommendationCard" style={{ lineHeight: 1.5 }}>
                    <h3 className="recommendationTitle"><span className="titleAccent">Recommendation:</span></h3>
                    —
                  </div>
                )}
              </div>
            );
          })()}

          {(() => {
            const pred = result?.analysis?.["Categorical Prediction"]; // rf-based categorical prediction
            const cat = result?.analysis?.["Categorization"]; // quick_screen object
            if (!pred && !cat) return null;
            return (
              <div>
                <h3>Prediction & Categorization</h3>
                {pred && (
                  <div style={{ marginBottom: 6 }}>
                    <span style={{ fontWeight: 600 }}>Prediction:</span> {renderValue(pred)}
                  </div>
                )}
                {cat && (
                  <div>
                    <span style={{ fontWeight: 600 }}>Details:</span> {renderValue(cat)}
                  </div>
                )}
              </div>
            );
          })()}

          

          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <button className="button" type="button" onClick={() => setShowRaw((v) => !v)}>
              {showRaw ? "Hide Raw JSON" : "Show Raw JSON"}
            </button>
          </div>

          {showRaw && (
            <pre className="jsonBlock">{JSON.stringify(result, null, 2)}</pre>
          )}
        </div>
      )}
    </main>
  );
}
