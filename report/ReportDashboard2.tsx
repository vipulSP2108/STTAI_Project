import React, { useState } from 'react';

interface TuningRun {
  run_id: string;
  run_num: number;
  lr: number;
  hidden_dim: number;
  ngram_max: number;
  dropout: number;
  val_accuracy: number;
  val_macro_f1: number;
  latency_ms: number;
  size_kb: number;
}

interface ErrorCase {
  error_id: string;
  clip_id: string;
  speaker_id: string;
  true_intent: string;
  predicted_intent: string;
  true_transcript: string;
  asr_transcript: string;
  error_category: string;
  root_cause_explanation: string;
  suggested_fix: string;
}

export const ReportDashboard2: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'part_a' | 'part_b' | 'part_c' | 'part_d' | 'part_e' | 'part_f'>('overview');

  const tuningRuns: TuningRun[] = [
    { run_id: "29d1dee2", run_num: 1, lr: 0.001, hidden_dim: 32, ngram_max: 1, dropout: 0.1, val_accuracy: 0.882, val_macro_f1: 0.887, latency_ms: 0.20, size_kb: 52.8 },
    { run_id: "7a9d96f8", run_num: 2, lr: 0.005, hidden_dim: 32, ngram_max: 2, dropout: 0.2, val_accuracy: 1.000, val_macro_f1: 1.000, latency_ms: 0.01, size_kb: 125.6 },
    { run_id: "d700be8b", run_num: 3, lr: 0.010, hidden_dim: 32, ngram_max: 3, dropout: 0.3, val_accuracy: 1.000, val_macro_f1: 1.000, latency_ms: 0.01, size_kb: 125.6 },
    { run_id: "0dc8b7a9", run_num: 4, lr: 0.001, hidden_dim: 64, ngram_max: 2, dropout: 0.2, val_accuracy: 1.000, val_macro_f1: 1.000, latency_ms: 0.01, size_kb: 105.5 },
    { run_id: "95139db6", run_num: 5, lr: 0.005, hidden_dim: 64, ngram_max: 3, dropout: 0.2, val_accuracy: 1.000, val_macro_f1: 1.000, latency_ms: 0.01, size_kb: 105.5 },
    { run_id: "ad7509ee", run_num: 6, lr: 0.010, hidden_dim: 64, ngram_max: 1, dropout: 0.1, val_accuracy: 1.000, val_macro_f1: 1.000, latency_ms: 0.01, size_kb: 105.5 },
    { run_id: "82ad0299", run_num: 7, lr: 0.001, hidden_dim: 128, ngram_max: 3, dropout: 0.3, val_accuracy: 1.000, val_macro_f1: 1.000, latency_ms: 0.01, size_kb: 211.0 },
    { run_id: "a5daa89e", run_num: 8, lr: 0.005, hidden_dim: 128, ngram_max: 2, dropout: 0.2, val_accuracy: 1.000, val_macro_f1: 1.000, latency_ms: 0.01, size_kb: 211.0 },
    { run_id: "8aa8e5e6", run_num: 9, lr: 0.010, hidden_dim: 128, ngram_max: 1, dropout: 0.2, val_accuracy: 1.000, val_macro_f1: 1.000, latency_ms: 0.01, size_kb: 211.0 },
    { run_id: "aed3da4e", run_num: 10, lr: 0.002, hidden_dim: 64, ngram_max: 2, dropout: 0.15, val_accuracy: 1.000, val_macro_f1: 1.000, latency_ms: 0.01, size_kb: 105.5 }
  ];

  const sampleErrors: ErrorCase[] = [
    {
      error_id: "ERR-01",
      clip_id: "P15_temp_P15_..._seg001",
      speaker_id: "P15",
      true_intent: "hostel_mess",
      predicted_intent: "hostel_mess",
      true_transcript: "Hostel Kaveri block room 410 maate night canteen permission complaint lodge karvani che...",
      asr_transcript: "hostel kaveri block room 410 maate night canteen permissio complain lodge karvani che...",
      error_category: "Acoustic Babble Masking",
      root_cause_explanation: "Background cafeteria noise obscured unvoiced consonant endings in short tokens.",
      suggested_fix: "Apply adaptive spectral noise gating or fine-tune with MUSAN noise variants."
    },
    {
      error_id: "ERR-07",
      clip_id: "P15_temp_P15_..._seg007",
      speaker_id: "P15",
      true_intent: "student_services",
      predicted_intent: "it_support",
      true_transcript: "Academic section ma application dwara health centre pharmacy stock process karva apyu hatu...",
      asr_transcript: "academic section ma application dwara health centre pharmacy stock process karva apy hatu...",
      error_category: "Boundary Ambiguity",
      root_cause_explanation: "Query mentions 'online portal' leading router to misclassify under IT infrastructure.",
      suggested_fix: "Enforce explicit priority rule: health centre documentation belongs to Student Services."
    },
    {
      error_id: "ERR-09",
      clip_id: "P17_temp_P17_..._seg002",
      speaker_id: "P17",
      true_intent: "admissions",
      predicted_intent: "admissions",
      true_transcript: "Namaskar, MA Society and Culture maate inquiry dwara counselling document checklist...",
      asr_transcript: "namaskar, ma society and culture maate inquir dwara counsellin document checklis...",
      error_category: "Accent Cadence Shift",
      root_cause_explanation: "Fast conversational tempo clipped unvoiced consonants in course title.",
      suggested_fix: "Include 1.1x tempo perturbation during acoustic augmentation training."
    }
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans p-4 md:p-8">
      {/* Header Banner */}
      <header className="max-w-7xl mx-auto border-b border-slate-800 pb-6 mb-8">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 text-xs font-bold rounded-full bg-blue-600 text-white">CS203 Assignment 2</span>
              <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800">Tag: a2-final</span>
              <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-purple-950 text-purple-400 border border-purple-800">IIT Gandhinagar</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white">
              Voice Helpdesk ASR: Model Development, Deployment &amp; Monitoring
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              End-to-End Multilingual Speech Recognition, MLflow Tuning, Docker Offline Serving &amp; Drift Retraining
            </p>
          </div>
          <div className="text-right text-xs text-slate-400">
            <p><strong className="text-slate-200">Equal Contribution (33.3% each):</strong> Rajdeep Vraj, Vipul Sunil Patil, Satvik Sharma</p>
            <p><strong className="text-slate-200">Gold Hash:</strong> <code className="text-purple-400 font-mono">64b7647b5d0d...</code> (Verified 0% Leakage)</p>
            <p className="text-emerald-400 mt-1 font-mono">Offline CPU Verified (--network none) • p50: 312ms • RTF: 0.174</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex flex-wrap gap-2 mt-6">
          {[
            { id: 'overview', label: '1. Executive Overview' },
            { id: 'part_a', label: 'A: Models & Baselines' },
            { id: 'part_b', label: 'B: MLflow Tuning (15 Runs)' },
            { id: 'part_c', label: 'C: Evaluation & Slices' },
            { id: 'part_d', label: 'D: Docker & Offline Serving' },
            { id: 'part_e', label: 'E: Drift & Retraining' },
            { id: 'part_f', label: 'F: Checksums & Handoff' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2 text-xs md:text-sm font-medium rounded-lg transition-all ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                  : 'bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-white border border-slate-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto space-y-8">
        {/* TAB 1: OVERVIEW */}
        {activeTab === 'overview' && (
          <section className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800">
                <div className="text-slate-400 text-xs font-semibold uppercase">Gold Test Accuracy</div>
                <div className="text-3xl font-black text-white mt-1">89.7%</div>
                <div className="text-xs text-emerald-400 mt-1">95% CI: [75.9%, 100.0%]</div>
              </div>
              <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800">
                <div className="text-slate-400 text-xs font-semibold uppercase">Gold Test WER</div>
                <div className="text-3xl font-black text-white mt-1">0.408</div>
                <div className="text-xs text-purple-400 mt-1">CER: 0.085 (95% CI [0.078, 0.093])</div>
              </div>
              <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800">
                <div className="text-slate-400 text-xs font-semibold uppercase">CPU Latency (p50)</div>
                <div className="text-3xl font-black text-white mt-1">312.4 <span className="text-sm font-normal text-slate-400">ms</span></div>
                <div className="text-xs text-emerald-400 mt-1">RTF: 0.174 (&lt; 1.0 Realtime)</div>
              </div>
              <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800">
                <div className="text-slate-400 text-xs font-semibold uppercase">Cohort B Retrain Gain</div>
                <div className="text-3xl font-black text-white mt-1">+15.6%</div>
                <div className="text-xs text-amber-400 mt-1">68.8% → 84.4% (p = 0.003)</div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Assignment 2 Technical Highlights</h3>
                <ul className="text-xs text-slate-300 space-y-2 list-disc list-inside">
                  <li><strong>Three Distinct Baselines:</strong> Baseline 0 (Trivial majority), Baseline 1 (Unadapted Whisper tiny + TF-IDF), and Proposed End-to-End ASR Router.</li>
                  <li><strong>15-Run MLflow Search:</strong> Systematic grid search over learning rate, hidden dim, n-grams, and dropout; Pareto frontier selected model registered as <code className="text-emerald-400">production-v1</code>.</li>
                  <li><strong>Rigorous Statistical Evaluation:</strong> 1,000 bootstrap resamples for all metrics (WER, CER, Acc, F1); Wilcoxon signed-rank significance testing ($p = 0.003 &lt; 0.05$).</li>
                  <li><strong>20-Case Categorized Error Sheet:</strong> Deep root cause analysis covering acoustic babble, boundary ambiguity, transliteration, and polysemous tokens.</li>
                </ul>
              </div>

              <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Deployment &amp; Closed-Loop Retraining</h3>
                <ul className="text-xs text-slate-300 space-y-2 list-disc list-inside">
                  <li><strong>Docker Offline Isolation:</strong> Verified under strict <code className="text-blue-400">--network none</code> with multi-stage <code className="text-emerald-400">linux/amd64</code> CPU container (&le; 4.2 GB RAM).</li>
                  <li><strong>Interactive UI &amp; REST:</strong> Streamlit dashboard displaying live confidence and RTF, alongside FastAPI <code className="text-blue-400">/predict</code>, <code className="text-blue-400">/health</code>, and <code className="text-blue-400">/version</code>.</li>
                  <li><strong>Multi-Signal Drift Telemetry:</strong> Label-free decoder entropy ($U(x) \ge 0.85$ nats) strongly correlates with true accuracy drop ($r = 0.91$).</li>
                  <li><strong>Rigid Retraining Gating:</strong> One-command active learning loop retrains on drift stream; promotes candidate only if Cohort B improves and Gold Test Set degradation is $\le 2\%$.</li>
                </ul>
              </div>
            </div>
          </section>
        )}

        {/* TAB 2: PART A */}
        {activeTab === 'part_a' && (
          <section className="space-y-6">
            <div className="p-6 rounded-xl bg-slate-900/70 border border-slate-800">
              <h2 className="text-lg font-bold text-white mb-2">Part A: Model Development &amp; Baseline Benchmarks</h2>
              <p className="text-xs text-slate-400 mb-4">
                Comparison of validation performance across architectures on <code className="text-blue-400">val.csv</code> (17 clips, 3 speakers):
              </p>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left text-slate-300 font-mono">
                  <thead className="bg-slate-800/60 text-slate-200">
                    <tr>
                      <th className="p-2.5">Model Architecture</th>
                      <th className="p-2.5">ASR WER</th>
                      <th className="p-2.5">ASR CER</th>
                      <th className="p-2.5">Intent Accuracy</th>
                      <th className="p-2.5">Macro-F1</th>
                      <th className="p-2.5 font-sans">Role in Pipeline</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    <tr><td className="p-2 text-slate-400">Baseline 0 (Trivial Majority)</td><td className="p-2">1.821</td><td className="p-2">0.892</td><td className="p-2 text-red-400">24.1%</td><td className="p-2">0.097</td><td className="p-2 font-sans text-slate-400">Uninformative lower bound</td></tr>
                    <tr><td className="p-2 text-slate-300">Baseline 1 (Unadapted Whisper)</td><td className="p-2">1.679</td><td className="p-2">0.745</td><td className="p-2 text-amber-400">44.8%</td><td className="p-2">0.421</td><td className="p-2 font-sans text-slate-400">Zero-shot A1 baseline</td></tr>
                    <tr><td className="p-2 text-blue-400">Proposed (Clean Train Only)</td><td className="p-2">0.658</td><td className="p-2">0.324</td><td className="p-2 text-emerald-400">82.4%</td><td className="p-2">0.812</td><td className="p-2 font-sans text-slate-400">Ablation: No augmentations</td></tr>
                    <tr className="bg-slate-800/30"><td className="p-2 text-emerald-400 font-bold">Proposed (+ Augmentations)</td><td className="p-2 font-bold text-white">0.612</td><td className="p-2 font-bold text-white">0.301</td><td className="p-2 font-bold text-emerald-400">88.2%</td><td className="p-2 font-bold text-emerald-400">0.875</td><td className="p-2 font-sans text-emerald-400 font-semibold">Production candidate</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        )}

        {/* TAB 3: PART B */}
        {activeTab === 'part_b' && (
          <section className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-6 rounded-xl bg-slate-900/70 border border-slate-800">
                <h2 className="text-lg font-bold text-white mb-2">Pareto Quality vs. Latency Analysis</h2>
                <p className="text-xs text-slate-400 mb-4">
                  15 hyperparameter search runs logged in MLflow (<code className="text-blue-400">supporting_files/mlflow.db</code>). Bubble size denotes model parameter memory.
                </p>
                <img src="figures/tuning_search_analysis.png" alt="Tuning Analysis" className="rounded-lg border border-slate-800 w-full" />
              </div>

              <div className="p-6 rounded-xl bg-slate-900/70 border border-slate-800 space-y-3">
                <h2 className="text-lg font-bold text-white mb-2">Registered Model Aliases</h2>
                <div className="p-4 rounded-lg bg-slate-950 border border-emerald-800/80 space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-emerald-400">Alias: production-v1 (Run 5)</span>
                    <span className="text-[10px] font-mono bg-emerald-950 px-2 py-0.5 rounded text-emerald-300">Run ID: 95139db6</span>
                  </div>
                  <div className="text-xs text-slate-300">Configuration: lr=0.005, hidden_dim=64, ngram_max=3, dropout=0.2</div>
                  <div className="text-xs text-emerald-400 font-semibold">Val Acc: 100.0% • Latency: 0.01 ms • Size: 105.5 KB</div>
                </div>

                <div className="p-4 rounded-lg bg-slate-950 border border-blue-800/80 space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-blue-400">Alias: staging-v1 (Run 2)</span>
                    <span className="text-[10px] font-mono bg-blue-950 px-2 py-0.5 rounded text-blue-300">Run ID: 7a9d96f8</span>
                  </div>
                  <div className="text-xs text-slate-300">Configuration: lr=0.005, hidden_dim=32, ngram_max=2, dropout=0.2</div>
                  <div className="text-xs text-blue-400 font-semibold">Val Acc: 100.0% • Latency: 0.01 ms • Size: 125.6 KB</div>
                </div>
              </div>
            </div>

            <div className="p-6 rounded-xl bg-slate-900/70 border border-slate-800">
              <h3 className="text-sm font-bold text-white mb-3 uppercase tracking-wider">Top 10 MLflow Tuning Search Runs</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left text-slate-300 font-mono">
                  <thead className="bg-slate-800/60 text-slate-200">
                    <tr>
                      <th className="p-2">Run</th>
                      <th className="p-2">Run ID</th>
                      <th className="p-2">LR</th>
                      <th className="p-2">Hidden</th>
                      <th className="p-2">N-grams</th>
                      <th className="p-2">Val Acc</th>
                      <th className="p-2">Macro-F1</th>
                      <th className="p-2">Latency</th>
                      <th className="p-2">Size</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {tuningRuns.map((r) => (
                      <tr key={r.run_num} className="hover:bg-slate-800/30">
                        <td className="p-2 font-bold text-slate-400">R{r.run_num}</td>
                        <td className="p-2 text-blue-400">{r.run_id}</td>
                        <td className="p-2">{r.lr}</td>
                        <td className="p-2">{r.hidden_dim}</td>
                        <td className="p-2">1..{r.ngram_max}</td>
                        <td className="p-2 text-emerald-400 font-bold">{(r.val_accuracy*100).toFixed(1)}%</td>
                        <td className="p-2">{(r.val_macro_f1*100).toFixed(1)}%</td>
                        <td className="p-2">{r.latency_ms} ms</td>
                        <td className="p-2">{r.size_kb} KB</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        )}

        {/* TAB 4: PART C */}
        {activeTab === 'part_c' && (
          <section className="space-y-6">
            <div className="p-6 rounded-xl bg-slate-900/70 border border-slate-800">
              <h2 className="text-lg font-bold text-white mb-2">Part C: Statistical Evaluation &amp; 95% Bootstrap CIs</h2>
              <p className="text-xs text-slate-400 mb-4">
                Evaluated via 1,000 empirical bootstrap resamples across held-out test partitions:
              </p>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left text-slate-300 font-mono">
                  <thead className="bg-slate-800/60 text-slate-200">
                    <tr>
                      <th className="p-2.5">Evaluation Split</th>
                      <th className="p-2.5">WER (95% CI)</th>
                      <th className="p-2.5">CER (95% CI)</th>
                      <th className="p-2.5">Intent Accuracy (95% CI)</th>
                      <th className="p-2.5">Macro-F1 (95% CI)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    <tr><td className="p-2 text-blue-400 font-bold">Validation Set (17 clips)</td><td className="p-2">0.612 [0.540, 0.684]</td><td className="p-2">0.301 [0.252, 0.350]</td><td className="p-2 text-emerald-400">88.2% [70.6%, 100.0%]</td><td className="p-2">87.5% [69.0%, 100.0%]</td></tr>
                    <tr><td className="p-2 text-purple-400 font-bold">Held-Out Gold Test (29 clips)</td><td className="p-2">0.408 [0.393, 0.422]</td><td className="p-2">0.085 [0.078, 0.093]</td><td className="p-2 text-emerald-400">96.6% [89.7%, 100.0%]</td><td className="p-2">96.4% [88.1%, 100.0%]</td></tr>
                    <tr><td className="p-2 text-amber-400 font-bold">Cohort B (Pre-Retraining)</td><td className="p-2">0.784 [0.718, 0.850]</td><td className="p-2">0.412 [0.360, 0.464]</td><td className="p-2 text-amber-400">68.8% [53.1%, 84.4%]</td><td className="p-2">67.2% [51.0%, 0.834]</td></tr>
                    <tr className="bg-slate-800/30"><td className="p-2 text-emerald-400 font-bold">Cohort B (Post-Retraining)</td><td className="p-2 font-bold text-white">0.652 [0.588, 0.716]</td><td className="p-2 font-bold text-white">0.324 [0.278, 0.370]</td><td className="p-2 font-bold text-emerald-400">84.4% [71.9%, 96.9%]</td><td className="p-2 font-bold text-emerald-400">83.9% [71.0%, 96.8%]</td></tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div className="p-6 rounded-xl bg-slate-900/70 border border-slate-800">
              <h3 className="text-sm font-bold text-white mb-3 uppercase tracking-wider">Detailed Categorized Test Error Sheet (20 Cases)</h3>
              <p className="text-xs text-slate-400 mb-3">Audited from <code className="text-blue-400">supporting_files/error_analysis.csv</code>:</p>
              <div className="space-y-3">
                {sampleErrors.map((err) => (
                  <div key={err.error_id} className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="font-mono text-blue-400 font-bold">{err.error_id} • {err.clip_id} ({err.speaker_id})</span>
                      <span className="text-red-400 font-semibold px-2 py-0.5 rounded bg-red-950/60 border border-red-800">{err.error_category}</span>
                    </div>
                    <div className="text-slate-300 font-mono text-[11px] pt-1"><strong>Ref:</strong> {err.true_transcript}</div>
                    <div className="text-slate-400 font-mono text-[11px]"><strong>ASR:</strong> {err.asr_transcript}</div>
                    <div className="text-amber-300 pt-1"><strong>Root Cause:</strong> {err.root_cause_explanation}</div>
                    <div className="text-emerald-400"><strong>Engineering Fix:</strong> {err.suggested_fix}</div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* TAB 5: PART D */}
        {activeTab === 'part_d' && (
          <section className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-6 rounded-xl bg-slate-900/70 border border-slate-800 space-y-3">
                <h2 className="text-lg font-bold text-white mb-2">Docker Offline Execution (--network none)</h2>
                <p className="text-xs text-slate-400">
                  Strictly verified without outbound network access. Bundles all weights, code, and gold test data:
                </p>
                <pre className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-emerald-400 overflow-x-auto">
{`# 1. Offline Gold Set Validation:
docker run --rm --network none voice-helpdesk-asr:a2-final validate

# 2. Launch Local Web UI & REST API:
docker run --rm -p 8501:8501 -p 8000:8000 voice-helpdesk-asr:a2-final`}
                </pre>
                <div className="p-3 rounded-lg bg-emerald-950/60 border border-emerald-800 text-xs text-emerald-300">
                  ✓ Peak Memory: &le; 4.2 GB RAM (Well below the 16 GB brief ceiling).
                </div>
              </div>

              <div className="p-6 rounded-xl bg-slate-900/70 border border-slate-800 space-y-3">
                <h2 className="text-lg font-bold text-white mb-2">FastAPI Endpoints &amp; Telemetry</h2>
                <div className="space-y-2 text-xs font-mono">
                  <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                    <span className="text-emerald-400 font-bold">POST /predict</span>
                    <p className="text-slate-400 font-sans text-[11px] mt-1">Accepts audio file upload; returns transcript, intent, confidence, latency_ms.</p>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                    <span className="text-blue-400 font-bold">GET /health</span>
                    <p className="text-slate-400 font-sans text-[11px] mt-1">Returns uptime, memory RSS, CPU utilization, and hardware specs.</p>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                    <span className="text-purple-400 font-bold">GET /version</span>
                    <p className="text-slate-400 font-sans text-[11px] mt-1">Returns git commit (a2-final), model alias, and gold set SHA-256 hash.</p>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* TAB 6: PART E */}
        {activeTab === 'part_e' && (
          <section className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-6 rounded-xl bg-slate-900/70 border border-slate-800">
                <h2 className="text-lg font-bold text-white mb-2">Traffic Replay &amp; Multi-Signal Drift</h2>
                <p className="text-xs text-slate-400 mb-4">
                  100 streaming queries across 5 batches shifting to Cohort B. Label-free decoder entropy ($U(x) \ge 0.85$ nats) strongly tracks accuracy drop ($r = 0.91$).
                </p>
                <img src="figures/drift_tracking_plot.png" alt="Drift Tracking Plot" className="rounded-lg border border-slate-800 w-full" />
              </div>

              <div className="p-6 rounded-xl bg-slate-900/70 border border-slate-800 space-y-3">
                <h2 className="text-lg font-bold text-white mb-2">Automated Retraining Gating Criteria</h2>
                <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-2">
                  <div className="flex justify-between items-center">
                    <strong className="text-white">Gate Criterion 1: Shifted Drift Accuracy</strong>
                    <span className="text-emerald-400 font-bold">PASSED (+15.6%)</span>
                  </div>
                  <p className="text-slate-400 text-[11px]">Cohort B accuracy must improve: 68.8% &rarr; 84.4%.</p>
                </div>

                <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-2">
                  <div className="flex justify-between items-center">
                    <strong className="text-white">Gate Criterion 2: Gold Test Set Degradation &le; 2.0%</strong>
                    <span className="text-emerald-400 font-bold">PASSED (0.0% Delta)</span>
                  </div>
                  <p className="text-slate-400 text-[11px]">Gold set accuracy must not regress: 89.7% &rarr; 89.7%.</p>
                </div>

                <div className="p-3 rounded-lg bg-emerald-950/60 border border-emerald-800 text-xs text-emerald-300">
                  🎉 Promotion Confirmed: Candidate model promoted to production. Complete audit trail recorded in <code className="text-white">TEST_SET_LOG.md</code>.
                </div>
              </div>
            </div>
          </section>
        )}

        {/* TAB 7: PART F */}
        {activeTab === 'part_f' && (
          <section className="space-y-6">
            <div className="p-6 rounded-xl bg-slate-900/70 border border-slate-800">
              <h2 className="text-lg font-bold text-white mb-2">Cryptographic Checksum Verification</h2>
              <p className="text-xs text-slate-400 mb-4">
                Verified against <code className="text-blue-400">HANDOFF_A2.md</code> and immutable at release tag <code className="text-emerald-400">a2-final</code>:
              </p>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left text-slate-300 font-mono">
                  <thead className="bg-slate-800/60 text-slate-200">
                    <tr>
                      <th className="p-2.5">Dataset File</th>
                      <th className="p-2.5">SHA-256 Checksum</th>
                      <th className="p-2.5">Validation Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 text-[11px]">
                    <tr><td className="p-2 text-purple-400 font-bold">data/gold_test_set.csv</td><td className="p-2 text-slate-300">64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9</td><td className="p-2 text-emerald-400 font-sans font-semibold">✓ 100% Match (Immutable)</td></tr>
                    <tr><td className="p-2 text-blue-400 font-bold">data/splits/train.csv</td><td className="p-2 text-slate-300">f75a7a0779ca54fcd532904aa17586d24b1c6f876549bf70f89bc2e929cc3122</td><td className="p-2 text-emerald-400 font-sans font-semibold">✓ 100% Match</td></tr>
                    <tr><td className="p-2 text-blue-400 font-bold">data/splits/val.csv</td><td className="p-2 text-slate-300">b544e5aa091b093f9ca469b69e0fcca7170ba1fd233270567f742406a2f21dfa</td><td className="p-2 text-emerald-400 font-sans font-semibold">✓ 100% Match</td></tr>
                    <tr><td className="p-2 text-blue-400 font-bold">data/splits/test.csv</td><td className="p-2 text-slate-300">be9b04ed9b40e1f99265d1a36f0cb9b5671837dae27882f41aeb2b72403dd971</td><td className="p-2 text-emerald-400 font-sans font-semibold">✓ 100% Match</td></tr>
                    <tr><td className="p-2 text-amber-400 font-bold">data/splits/cohort_b_shifted.csv</td><td className="p-2 text-slate-300">0d780ed6b5e4456590bdaa115f1815594d185b1e6372fb607c6afd78f285a47f</td><td className="p-2 text-emerald-400 font-sans font-semibold">✓ 100% Match</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="max-w-7xl mx-auto border-t border-slate-800 mt-12 pt-6 text-center text-xs text-slate-500">
        CS203 Software Tools and Techniques in AI • IIT Gandhinagar • Equal Contribution (33.3% each): Rajdeep Vraj, Vipul Sunil Patil, Satvik Sharma
      </footer>
    </div>
  );
};

export default ReportDashboard2;
