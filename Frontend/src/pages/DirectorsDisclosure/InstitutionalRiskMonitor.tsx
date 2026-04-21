import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Highcharts from "highcharts";
import HighchartsReact from "highcharts-react-official";
import Drilldown from "highcharts/modules/drilldown";
import VariablePie from "highcharts/modules/variable-pie";

// Initialize Modules safely for TypeScript
if (typeof Drilldown === 'function') (Drilldown as any)(Highcharts);
if (typeof VariablePie === 'function') (VariablePie as any)(Highcharts);

import {
  AlertTriangle, Building2, TrendingUp, Shield,
  ChevronRight, Loader2, X, CheckCircle,
  Activity, DollarSign, Layers, Info, Users
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

// ─── Palette (Lighter, non-dark professional colors) ──────────
const AEGIS_BLUE = "#38BDF8"; // Sky Blue
const AEGIS_AMBER = "#FBBF24"; // Amber
const AEGIS_RED = "#F87171"; // Soft Red
const AEGIS_GREEN = "#4ADE80"; // Bright Green
const AEGIS_INDIGO = "#818CF8"; // Indigo/Lavender

const SECTOR_COLORS = [
  "#38BDF8", "#4ADE80", "#FBBF24", "#F87171", "#818CF8",
  "#2DD4BF", "#A78BFA", "#F472B6", "#FB7185"
];

// ─── Types ─────────────────────────────────────────────────────
interface Summary {
  total_companies: number;
  ecosystem_leverage: number;
  charge_records: number;
  total_paid_capital: number;
  statutory_health_pct: number;
  filed_agm_count: number;
  status_breakdown: { status: string; count: number; state_breakdown: { name: string; y: number }[] }[];
  listing_breakdown: { list_status: string; count: number }[];
}
interface RedFlags { dormant_with_directors: any[]; stale_filings: any[]; high_leverage: any[]; }
interface SectorData { sectors: { sector: string; count: number; total_capital: number }[]; states: { state: string; count: number }[]; }
interface EntityDetail { company: any; board: any[]; charges: any[]; total_charge: number; }

// ─── Formatting Utils ──────────────────────────────────────────
const parseAmount = (val: any) => {
  if (val == null) return 0;
  if (typeof val === 'number') return val;
  const clean = String(val).replace(/[^0-9.]/g, '');
  return parseFloat(clean) || 0;
};

const fmtCr = (v?: number) => {
  if (v == null || v === 0) return "₹0 Cr";
  const inCr = v / 1e7;
  return `₹${inCr.toLocaleString(undefined, { maximumFractionDigits: 1 })} Cr`;
};

const fmtLakh = (v?: number) => {
  if (v == null || v === 0) return "₹0 L";
  const inLakh = v / 1e5;
  return `₹${inLakh.toLocaleString(undefined, { maximumFractionDigits: 1 })} L`;
};

// ─── Highcharts Pie Component (Exploded Style) ────────────────
const AegisHighPie = ({ data, total, label, colors, drilldownData }: any) => {
  const options: Highcharts.Options = {
    chart: { type: 'pie', height: 280, backgroundColor: 'transparent' },
    title: { text: '' },
    tooltip: {
      backgroundColor: '#ffffff', borderWidth: 0, borderRadius: 12, shadow: true,
      headerFormat: '', pointFormat: '<span style="color:{point.color}">●</span> <b>{point.name}</b>: {point.y}'
    },
    plotOptions: {
      pie: {
        allowPointSelect: true,
        cursor: 'pointer',
        innerSize: '0%', // Full Pie
        borderWidth: 2,
        borderColor: '#ffffff',
        colors: colors,
        dataLabels: {
          enabled: true,
          format: '<b>{point.percentage:.1f}%</b>',
          distance: -40, // Move labels inside
          style: {
            fontSize: '14px',
            fontWeight: '900',
            color: 'white',
            textOutline: 'none'
          }
        },
        showInLegend: true
      }
    },
    legend: {
      itemStyle: { fontSize: '10px', fontWeight: '700', color: '#6B7280' },
      align: 'right', verticalAlign: 'middle', layout: 'vertical'
    },
    series: [{
      type: 'pie',
      name: label,
      data: data.map((d: any, i: number) => ({
        name: d.name,
        y: d.y,
        drilldown: d.drilldown,
        sliced: i === 0, // Explode the first/primary slice
        selected: i === 0
      }))
    }],
    drilldown: {
      series: drilldownData || [],
      activeDataLabelStyle: { textDecoration: 'none', color: '#111827' }
    },
    credits: { enabled: false }
  };
  return <HighchartsReact highcharts={Highcharts} options={options} />;
};

// ─── KPI Card ──────────────────────────────────────────────────
const KPICard = ({ icon: Icon, label, value, sub, accent, tooltip }: any) => (
  <TooltipProvider>
    <div className="bg-white rounded-2xl border border-gray-100/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] transition-shadow p-6 flex flex-col gap-3 relative group">
      <div className="flex justify-between items-start">
        <div className="w-9 h-9 rounded-xl flex items-center justify-center transition-transform group-hover:scale-110" style={{ background: `${accent}15` }}>
          <Icon size={17} style={{ color: accent }} />
        </div>
        <Tooltip delayDuration={0}>
          <TooltipTrigger>
            <Info size={14} className="text-gray-400 hover:text-gray-600 cursor-help transition-colors" />
          </TooltipTrigger>
          <TooltipContent
            side="top"
            className="bg-white text-gray-800 border-gray-100 shadow-2xl rounded-xl p-3 max-w-[200px]"
          >
            <p className="text-[11px] font-medium leading-relaxed">
              {tooltip}
            </p>
          </TooltipContent>
        </Tooltip>
      </div>
      <div>
        <p className="text-[10px] font-bold text-gray-500 mb-1">{label}</p>
        <p className="text-2xl font-black text-gray-900 leading-none">{value ?? "–"}</p>
        {sub && <p className="text-[10px] font-medium text-gray-500 mt-1.5">{sub}</p>}
      </div>
    </div>
  </TooltipProvider>
);

// ─── Red-Flag Row ──────────────────────────────────────────────
const RedFlagRow = ({ item, onClick, type }: { item: any; onClick: () => void; type: string }) => {
  const isNewIncorp = type === "stale" && (!item.last_agm || item.last_agm === "") && (item.cin?.includes("2024") || item.cin?.includes("2025") || item.cin?.includes("2026"));

  const badge =
    type === "dormant" ? { label: item.status || "Unknown", cls: "bg-red-50 text-red-600 border border-red-100" }
      : type === "stale" ? {
        label: isNewIncorp ? "New incorporation" : "No AGM filed",
        cls: isNewIncorp ? "bg-blue-50 text-blue-700 border border-blue-100" : "bg-amber-50 text-amber-700 border border-amber-100"
      }
        : { label: `₹${Number(item.total_charge_amount || 0).toLocaleString()}`, cls: "bg-purple-50 text-purple-700 border border-purple-100" };

  return (
    <motion.tr initial={{ opacity: 0 }} animate={{ opacity: 1 }}
      className="border-b border-gray-50 hover:bg-gray-50/70 cursor-pointer transition-colors group"
      onClick={onClick}>
      <td className="py-4 pl-6 pr-3 text-left">
        <p className="font-black text-gray-800 text-sm group-hover:text-[#0B74B0] transition-colors truncate max-w-[220px]">{item.company_name || item.name || "–"}</p>
        <p className="text-[10px] text-gray-400 font-mono mt-0.5">{item.cin}</p>
      </td>
      <td className="py-4 px-3 text-left">
        <span className={`inline-block px-3 py-1 rounded-full text-[10px] font-bold ${badge.cls}`}>
          {badge.label}
        </span>
      </td>
      <td className="py-4 px-3 text-sm font-medium text-gray-500 text-left">{item.state || "–"}</td>
      <td className="py-4 px-3 text-sm font-bold text-gray-700 text-center">
        {item.director_count ?? item.active_charges ?? "–"}
      </td>
      <td className="py-4 pr-6 pl-3 text-right">
        <ChevronRight size={15} className="text-gray-300 group-hover:text-[#0B74B0] transition-colors ml-auto" />
      </td>
    </motion.tr>
  );
};

// ─── Entity Pedigree Modal ─────────────────────────────────────
const EntityModal = ({ cin, open, onClose }: { cin: string; open: boolean; onClose: () => void }) => {
  const [data, setData] = useState<EntityDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open || !cin) return;
    setLoading(true);
    fetch(`/api/institutional-risk/entity/${cin}`)
      .then(r => r.json()).then(setData).catch(console.error).finally(() => setLoading(false));
  }, [open, cin]);

  const c = data?.company;
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-[780px] rounded-[2rem] p-0 overflow-hidden border border-gray-100 shadow-xl">
        <div className="bg-gray-50 border-b border-gray-100 p-8">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-white rounded-2xl border border-gray-100 shrink-0">
              <Building2 className="text-[#0B74B0]" size={22} />
            </div>
            <div className="flex-1 min-w-0">
              <DialogHeader>
                <DialogTitle className="text-xl font-black text-gray-900 truncate">{c?.name || "Loading…"}</DialogTitle>
                <DialogDescription className="text-gray-400 text-[10px] font-bold uppercase tracking-widest mt-1">
                  Entity Pedigree | CIN: {cin}
                </DialogDescription>
              </DialogHeader>
            </div>
            {c && (
              <span className={`shrink-0 px-3 py-1.5 rounded-xl text-[10px] font-black uppercase border ${(c.status || "").toLowerCase() === "active"
                ? "bg-green-50 text-green-700 border-green-100"
                : "bg-red-50 text-red-700 border-red-100"
                }`}>{c.status || "Unknown"}</span>
            )}
          </div>
          {c && (
            <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-100">
              {[
                { label: "Paid-up Capital", value: fmtCr(parseAmount(c.paid_capital)) },
                { label: "Total Charges", value: fmtCr(parseAmount(data!.total_charge)) },
                { label: "Board Strength", value: `${data!.board.length} Directors` }
              ].map((m, i) => (
                <div key={i}>
                  <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest">{m.label}</p>
                  <p className="text-lg font-black text-gray-900 mt-0.5">{m.value}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white overflow-y-auto max-h-[420px]">
          {loading ? (
            <div className="flex items-center justify-center py-20 gap-3">
              <Loader2 className="animate-spin text-[#75479C]" size={24} />
              <span className="text-sm font-bold text-gray-400">Pulling Registry…</span>
            </div>
          ) : data ? (
            <div className="p-8 space-y-8">
              <div>
                <h4 className="text-[9px] font-black text-gray-400 uppercase tracking-widest mb-4">Statutory Details</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {[
                    { label: "Incorporated", value: c?.incorporation_date },
                    { label: "Category", value: c?.category },
                    { label: "Class", value: c?.class },
                    { label: "ROC", value: c?.roc },
                    { label: "Last AGM", value: c?.last_agm },
                    { label: "Last B/S", value: c?.last_bal_sheet },
                    { label: "State", value: c?.state },
                    { label: "Address", value: c?.address },
                    { label: "Auth Capital", value: fmtCr(parseAmount(c?.auth_capital)) },
                  ].filter(f => f.value && f.value !== "₹0 Cr").map((f, i) => (
                    <div key={i} className="bg-gray-50 rounded-xl p-3 border border-gray-100">
                      <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest mb-0.5">{f.label}</p>
                      <p className="text-xs font-bold text-gray-800 truncate">{f.value}</p>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <h4 className="text-[9px] font-black text-gray-400 uppercase tracking-widest mb-3">Board Composition</h4>
                <div className="space-y-2">
                  {data.board.map((d, i) => (
                    <div key={i} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl border border-gray-100">
                      <div>
                        <p className="font-black text-gray-800 text-sm">{d.director_name}</p>
                        <p className="text-[10px] font-bold text-gray-400 uppercase">{d.designation}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-[9px] font-mono text-gray-300">DIN {d.din}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              {data.charges.length > 0 && (
                <div>
                  <h4 className="text-[9px] font-black text-gray-400 uppercase tracking-widest mb-3">Charges & Borrowings</h4>
                  <div className="space-y-2">
                    {data.charges.map((ch, i) => (
                      <div key={i} className="flex items-center justify-between p-4 bg-red-50 rounded-xl border border-red-100">
                        <div>
                          <p className="font-bold text-gray-800 text-sm">{ch.holder || "Undisclosed Holder"}</p>
                          <p className="text-[10px] font-bold text-gray-400">Created: {ch.creation_date}</p>
                        </div>
                        <p className="text-lg font-black text-red-600">{fmtLakh(parseAmount(ch.amount))}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>
        <div className="p-4 bg-gray-50 border-t border-gray-100 text-center">
          <p className="text-[9px] font-black text-gray-400 uppercase tracking-[0.3em]">Aegis Institutional Risk Terminal</p>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// ══════════════════════════════════════════════════════════════
//  MAIN COMPONENT
// ══════════════════════════════════════════════════════════════
const InstitutionalRiskMonitor = () => {
  const [tab, setTab] = useState<"overview" | "red-flags" | "sector" | "interlock">("overview");
  const [rfTab, setRfTab] = useState<"dormant" | "stale" | "leverage">("dormant");
  const [summary, setSummary] = useState<Summary | null>(null);
  const [redFlags, setRedFlags] = useState<RedFlags | null>(null);
  const [sectorData, setSectorData] = useState<SectorData | null>(null);
  const [interlocks, setInterlocks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCIN, setSelectedCIN] = useState("");
  const [entityOpen, setEntityOpen] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch("/api/institutional-risk/summary").then(r => r.json()).then(setSummary).catch(console.error),
      fetch("/api/institutional-risk/red-flags").then(r => r.json()).then(setRedFlags).catch(console.error),
      fetch("/api/institutional-risk/sector-map").then(r => r.json()).then(setSectorData).catch(console.error),
      fetch("/api/institutional-risk/board-interlock").then(r => r.json()).then(d => setInterlocks(d?.interlocks || [])).catch(console.error)
    ]).finally(() => setLoading(false));
  }, []);

  const openEntity = (cin: string) => { if (cin) { setSelectedCIN(cin); setEntityOpen(true); } };

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-white">
      <Loader2 className="h-10 w-10 animate-spin text-[#75479C]" />
    </div>
  );

  const rfData = rfTab === "dormant" ? redFlags?.dormant_with_directors
    : rfTab === "stale" ? redFlags?.stale_filings
      : redFlags?.high_leverage;

  return (
    <div className="min-h-screen bg-white p-6">

      {/* ── Page Header ──────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10 border-b border-gray-100 pb-8">
        <div>
          <h1 className="text-3xl font-black text-gray-900 tracking-tight flex items-center gap-3">
            <Shield className="text-[#75479C]" size={28} />
            Aegis Institutional Risk & Compliance Terminal
          </h1>
          <p className="text-gray-500 font-medium ml-10">Advanced Governance & Ecosystem Exposure Monitoring</p>
        </div>
        <div className="flex gap-8">
          <div className="text-right">
            <p className="text-[10px] font-bold text-gray-400">Total entities</p>
            <p className="text-2xl font-black" style={{ color: AEGIS_INDIGO }}>{summary?.total_companies?.toLocaleString() ?? "–"}</p>
          </div>
          <div className="h-10 w-px bg-gray-100" />
          <div className="text-right">
            <p className="text-[10px] font-bold text-gray-400">Ecosystem leverage</p>
            <p className="text-2xl font-black text-red-500">{fmtCr(summary?.ecosystem_leverage)}</p>
          </div>
        </div>
      </div>

      {/* ── KPI Row ──────────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-5 mb-10">
        <KPICard
          icon={Building2} label="Entities synced" value={summary?.total_companies?.toLocaleString() ?? "–"}
          sub="Unique CINs in registry" accent={AEGIS_BLUE}
          tooltip="Number of unique companies within the Adani ecosystem group perimeter." />
        <KPICard
          icon={DollarSign} label="Ecosystem leverage" value={fmtCr(summary?.ecosystem_leverage)}
          sub={`${summary?.charge_records ?? 0} active charge records`} accent={AEGIS_RED}
          tooltip="Total borrowing and charge exposure across all identified ecosystem entities." />
        <KPICard
          icon={TrendingUp} label="Paid-up capital" value={fmtCr(summary?.total_paid_capital)}
          sub="Total across group entities" accent={AEGIS_GREEN}
          tooltip="Volume of individual charge registrations found in the official MCA registry." />
        <KPICard
          icon={CheckCircle} label="Statutory health" value={`${summary?.statutory_health_pct ?? 0}%`}
          sub={`${summary?.filed_agm_count ?? 0} compliant entities`} accent={AEGIS_AMBER}
          tooltip="Percentage of companies with compliant AGM and annual filing status." />
      </div>

      {/* ── Nav Tabs ─────────────────────────────────────────── */}
      <div className="flex flex-wrap gap-2 mb-8 bg-gray-50 p-2 rounded-2xl border border-gray-100">
        {([
          { id: "overview", label: "Network Overview", icon: Activity },
          { id: "red-flags", label: "Governance Red-Flags", icon: AlertTriangle },
          { id: "sector", label: "Sector Intelligence", icon: Layers },
          { id: "interlock", label: "Board Interlock", icon: Users }
        ] as const).map(item => (
          <button key={item.id} onClick={() => setTab(item.id as any)}
            className={`flex items-center gap-2 px-5 py-3 rounded-xl font-bold text-sm transition-all ${tab === item.id ? "bg-[#75479C] text-white shadow-md" : "text-gray-500 hover:bg-white hover:text-[#75479C]"
              }`}>
            <item.icon size={15} />
            {item.label}
          </button>
        ))}
      </div>

      {/* ── Content ──────────────────────────────────────────── */}
      <AnimatePresence mode="wait">

        {/* OVERVIEW */}
        {tab === "overview" && (
          <motion.div key="ov" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="rounded-[2rem] border border-gray-100/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] bg-white overflow-hidden">
                <CardHeader className="py-4 px-6 border-b border-gray-50 flex flex-row items-center justify-between">
                  <CardTitle className="text-[10px] font-bold text-gray-500">Company status distribution</CardTitle>
                </CardHeader>
                <CardContent className="p-4">
                  <AegisHighPie
                    data={(summary?.status_breakdown || []).map(s => ({ name: s.status, y: s.count, drilldown: s.status }))}
                    drilldownData={(summary?.status_breakdown || []).map(s => ({ id: s.status, name: `States (${s.status})`, data: s.state_breakdown }))}
                    total={summary?.total_companies ?? 0} label="Companies" colors={[AEGIS_BLUE, AEGIS_RED, AEGIS_AMBER, "#E2E8F0"]} />
                </CardContent>
              </Card>
              <Card className="rounded-[2rem] border border-gray-100/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] bg-white overflow-hidden">
                <CardHeader className="py-4 px-6 border-b border-gray-50">
                  <CardTitle className="text-[10px] font-bold text-gray-500">Listed vs unlisted portfolio</CardTitle>
                </CardHeader>
                <CardContent className="p-4">
                  <AegisHighPie
                    data={(summary?.listing_breakdown || []).map(s => ({ name: s.list_status, y: s.count }))}
                    total={summary?.total_companies ?? 0} label="Entities" colors={[AEGIS_INDIGO, AEGIS_BLUE, "#E2E8F0"]} />
                </CardContent>
              </Card>
            </div>
          </motion.div>
        )}

        {/* RED FLAGS */}
        {tab === "red-flags" && (
          <motion.div key="rf" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div className="flex items-center gap-4 p-5 bg-red-50 border border-red-100 rounded-2xl mb-6">
              <AlertTriangle className="text-red-500 shrink-0" size={18} />
              <p className="text-sm font-medium text-red-700">Governance risks auto-detected. Click any row to open the full institutional profile.</p>
            </div>
            <div className="flex flex-wrap gap-2 mb-6">
              <TooltipProvider>
                {([
                  { id: "dormant", label: `Dormant/non-active (${redFlags?.dormant_with_directors?.length ?? 0})`, cls: "bg-red-50 text-red-700 border-red-100", tooltip: "Flags entities that are currently struck off, liquidated, or no longer operational." },
                  { id: "stale", label: `Stale filings (${redFlags?.stale_filings?.length ?? 0})`, cls: "bg-amber-50 text-amber-700 border-amber-100", tooltip: "Identifies entities with overdue AGM filings, a key indicator of compliance lag." },
                  { id: "leverage", label: `High-leverage (${redFlags?.high_leverage?.length ?? 0})`, cls: "bg-purple-50 text-purple-700 border-purple-100", tooltip: "Monitors entities with high borrowing exposure relative to others in the ecosystem." }
                ] as const).map(p => (
                  <Tooltip key={p.id} delayDuration={0}>
                    <TooltipTrigger asChild>
                      <button onClick={() => setRfTab(p.id)} className={`px-5 py-2 rounded-xl text-[11px] font-black uppercase tracking-wider transition-all border ${rfTab === p.id ? `${p.cls} border-opacity-100` : "bg-white text-gray-400 border-gray-100 hover:border-gray-200"}`}>
                        {p.label}
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="top" className="bg-white text-gray-800 border-gray-100 shadow-2xl rounded-xl p-3 max-w-[220px]">
                      <p className="text-[11px] font-medium leading-relaxed">{p.tooltip}</p>
                    </TooltipContent>
                  </Tooltip>
                ))}
              </TooltipProvider>
            </div>
            <Card className="rounded-[2rem] border border-gray-100/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden bg-white">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-100">
                    {["Company", "Flag", "State", rfTab === "leverage" ? "Active charges" : "Directors", ""].map((h, i) => (
                      <th key={i} className={`py-4 ${i === 0 ? "pl-6 text-left" : i === 4 ? "" : "px-3 text-left"} text-[10px] font-bold text-gray-500`}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(rfData || []).map((item, idx) => <RedFlagRow key={idx} item={item} type={rfTab} onClick={() => openEntity(item.cin)} />)}
                </tbody>
              </table>
            </Card>
          </motion.div>
        )}

        {/* SECTOR INTELLIGENCE */}
        {tab === "sector" && (
          <motion.div key="sc" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="rounded-[2rem] border border-gray-100/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] bg-white overflow-hidden">
                <CardHeader className="py-4 px-6 border-b border-gray-50">
                  <CardTitle className="text-[10px] font-bold text-gray-500">Sector distribution & capital density</CardTitle>
                </CardHeader>
                <CardContent className="p-4">
                  <HighchartsReact highcharts={Highcharts} options={{
                    chart: { type: 'variablepie', height: 320, backgroundColor: 'transparent' },
                    title: { text: '' },
                    tooltip: {
                      backgroundColor: '#ffffff', borderRadius: 12, shadow: true, useHTML: true,
                      headerFormat: '<span style="font-size: 10px; color: #9CA3AF; font-weight: 700">{point.key}</span><br/>',
                      pointFormat: '<span style="color:{point.color}">●</span> <b>Entities:</b> {point.y}<br/>' +
                        '<span style="color:#75479C">●</span> <b>Total Capital:</b> ₹{point.z_fmt}'
                    },
                    series: [{
                      minPointSize: 10, innerSize: '30%', zMin: 0,
                      name: 'Sectors',
                      data: (sectorData?.sectors || []).map((s, i) => ({
                        name: s.sector,
                        y: s.count,
                        z: s.total_capital,
                        z_fmt: fmtCr(s.total_capital),
                        color: SECTOR_COLORS[i % SECTOR_COLORS.length]
                      }))
                    }],
                    credits: { enabled: false }
                  }} />
                </CardContent>
              </Card>
              <Card className="rounded-[2rem] border border-gray-100/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] bg-white overflow-hidden">
                <CardHeader className="py-4 px-6 border-b border-gray-50">
                  <CardTitle className="text-[10px] font-bold text-gray-500">Capital by sector</CardTitle>
                </CardHeader>
                <CardContent className="p-4">
                  <HighchartsReact highcharts={Highcharts} options={{
                    chart: { type: 'bar', height: 260 }, title: { text: '' },
                    xAxis: { categories: (sectorData?.sectors || []).map(s => s.sector), labels: { style: { fontWeight: '700', fontSize: '9px' } } },
                    yAxis: { title: { text: 'Capital' } },
                    series: [{ name: 'Capital', data: (sectorData?.sectors || []).map(s => s.total_capital), color: AEGIS_INDIGO, borderRadius: 4 }],
                    credits: { enabled: false }
                  }} />
                </CardContent>
              </Card>
            </div>
            <Card className="rounded-[2rem] border border-gray-100 shadow-sm overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-100">
                  <tr>
                    <th className="py-4 pl-8 text-left text-[10px] font-bold text-gray-400">Sector</th>
                    <th className="py-4 px-4 text-center text-[10px] font-bold text-gray-400">Entities</th>
                    <th className="py-4 pr-8 text-right text-[10px] font-bold text-gray-400">Capital</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {(sectorData?.sectors || []).map((s, i) => (
                    <tr key={i} className="hover:bg-gray-50/50 transition-colors">
                      <td className="py-4 pl-8 font-bold text-sm text-gray-800">{s.sector}</td>
                      <td className="py-4 px-4 text-center text-sm font-medium text-gray-500">{s.count}</td>
                      <td className="py-4 pr-8 text-right font-black text-[#75479C]">{fmtCr(s.total_capital)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          </motion.div>
        )}

        {/* BOARD INTERLOCK */}
        {tab === "interlock" && (
          <motion.div key="il" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div className="flex items-center gap-3 p-5 bg-blue-50 border border-blue-100 rounded-2xl mb-6">
              <Users className="text-blue-500 shrink-0" size={18} />
              <p className="text-sm font-medium text-blue-700">Directors with 2+ ecosystems seats – primary network connectivity nodes.</p>
            </div>
            <Card className="rounded-[2rem] border border-gray-100 shadow-sm overflow-hidden bg-white">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-100">
                  <tr>
                    <th className="py-4 pl-8 text-left text-[10px] font-bold text-gray-400">Director</th>
                    <th className="py-4 px-4 text-center text-[10px] font-bold text-gray-400">DIN</th>
                    <th className="py-4 px-4 text-center text-[10px] font-bold text-gray-400">Seats</th>
                    <th className="py-4 pr-8 text-left text-[10px] font-bold text-gray-400">Companies</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {interlocks.map((d, i) => (
                    <tr key={i} className="hover:bg-gray-50/50 transition-colors">
                      <td className="py-4 pl-8 font-black text-sm text-gray-800">{d.director_name}</td>
                      <td className="py-4 px-4 text-center font-mono text-xs text-gray-400">{d.din}</td>
                      <td className="py-4 px-4 text-center">
                        <span className="px-3 py-1 rounded-full text-[10px] font-black bg-purple-50 text-[#75479C]">{d.company_count}</span>
                      </td>
                      <td className="py-4 pr-8 text-left text-xs text-gray-500 font-medium">
                        {(d.companies || []).join(", ")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          </motion.div>
        )}

      </AnimatePresence>

      <EntityModal cin={selectedCIN} open={entityOpen} onClose={() => setEntityOpen(false)} />

      <footer className="mt-20 pt-10 border-t border-gray-100 text-center opacity-30">
        <span className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]">Aegis Institutional Risk & Compliance Terminal</span>
      </footer>
    </div>
  );
};

export default InstitutionalRiskMonitor;
