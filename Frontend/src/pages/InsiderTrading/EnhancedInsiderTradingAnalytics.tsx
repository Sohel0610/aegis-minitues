import { useState, useEffect } from "react";
import { Loader2, AlertCircle, Users, TrendingUp, Lightbulb, Activity } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useInsiderTradingFilters } from "@/contexts/InsiderTradingFilterContext";
import InsiderTradingFilterBar from "@/components/InsiderTradingFilterBar";

// ── Types ─────────────────────────────────────────────────────────
interface InsiderTradingSummary {
  total_companies: number;
  total_investors: number;
  total_shares: number;
  net_investors_change: number;
  net_shares_change: number;
  added_count: number;
  removed_count: number;
  changed_count: number;
  unchanged_count: number;
}

interface InsiderRecord {
  pangir: string;
  name: string;
  email: string;
  position_latest: number;
  position_older: number;
  position_difference: number;
  status: string;
  source?: string;
  company?: string;
  batch?: string;
  depository?: string;
}

interface EnhancedInsiderTradingDetails {
  summary: InsiderTradingSummary;
  top_new_investors: InsiderRecord[];
  top_exits: InsiderRecord[];
  top_buyers: InsiderRecord[];
  top_sellers: InsiderRecord[];
}

// ── Component ─────────────────────────────────────────────────────
const EnhancedInsiderTradingAnalytics = () => {
  const { filters, buildQuery } = useInsiderTradingFilters();
  const [activeTab, setActiveTab] = useState<'new' | 'exits' | 'buyers' | 'sellers'>('new');
  const [details, setDetails] = useState<EnhancedInsiderTradingDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Refetch whenever global filters change
  useEffect(() => {
    fetchData();
  }, [filters.company, filters.batch, filters.depository]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const qs = buildQuery();
      const res = await fetch(`/api/insider-trading/enhanced-details${qs}`);
      if (!res.ok) throw new Error("Failed to fetch data");
      const data: EnhancedInsiderTradingDetails = await res.json();
      setDetails(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  // Display helpers
  const displayName = (record: InsiderRecord) => {
    const name = record.name?.trim();
    const pan = record.pangir?.trim();
    const panPattern = /^[A-Z]{5}\d{4}[A-Z]$/i;
    if (!name || name === pan || panPattern.test(name) || name === "unavailable") return "N/A";
    return name;
  };

  const displaySource = (record: InsiderRecord) => {
    if (record.company) {
      return `${record.company}${record.depository ? ` — ${record.depository}` : ""}`;
    }
    return record.source || "N/A";
  };

  // KPI Insights
  const getTopInsights = () => {
    if (!details?.summary) {
      return [
        { title: "Total Investors", value: "0", icon: Users, change: "0", changeType: "neutral" },
        { title: "Net Investor Change", value: "0", icon: TrendingUp, change: "vs last period", changeType: "neutral" },
        { title: "Net Shares Change", value: "0", icon: Activity, change: "positions modified", changeType: "neutral" },
      ];
    }
    const s = details.summary;
    const netChange = (s.added_count || 0) - (s.removed_count || 0);
    return [
      {
        title: "Total Investors",
        value: s.total_investors?.toLocaleString() || "0",
        icon: Users,
        change: s.net_investors_change > 0 ? `+${s.net_investors_change}` : `${s.net_investors_change}`,
        changeType: s.net_investors_change >= 0 ? "positive" : "negative",
      },
      {
        title: "Net Investor Change",
        value: `${netChange >= 0 ? "+" : ""}${netChange}`,
        icon: TrendingUp,
        change: "vs last period",
        changeType: netChange >= 0 ? "positive" : "negative",
      },
      {
        title: "Modified Positions",
        value: s.changed_count?.toLocaleString() || "0",
        icon: Activity,
        change: "positions modified",
        changeType: "neutral",
      },
    ];
  };

  const topInsights = getTopInsights();

  // ── Render ────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "#ffffff" }}>
        <div className="text-center">
          <Loader2 className="h-10 w-10 animate-spin mx-auto mb-3" style={{ color: "#75479C" }} />
          <p className="text-base text-gray-900">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "#ffffff" }}>
        <div className="text-center p-5 max-w-md">
          <AlertCircle className="h-10 w-10 mx-auto mb-3" style={{ color: "#EF4444" }} />
          <h2 className="text-lg font-semibold mb-2 text-gray-900">Error Loading Analytics</h2>
          <p className="mb-3 text-sm text-gray-700">{error}</p>
          <button onClick={fetchData} className="px-3 py-1.5 bg-[#75479C] text-white rounded text-sm hover:bg-[#5a357a] transition-colors">
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Get the active table data
  const tableData: InsiderRecord[] = (() => {
    if (!details) return [];
    switch (activeTab) {
      case "new": return details.top_new_investors || [];
      case "exits": return details.top_exits || [];
      case "buyers": return details.top_buyers || [];
      case "sellers": return details.top_sellers || [];
      default: return [];
    }
  })();

  return (
    <div className="min-h-screen p-4 md:p-6" style={{ background: "#ffffff" }}>
      {/* Header */}
      <div className="mb-5">
        <Card className="border-0 shadow-none bg-transparent">
          <CardHeader className="px-0 pb-3">
            <div className="flex items-center gap-2.5">
              <Activity className="h-7 w-7" style={{ color: "#75479C" }} />
              <div>
                <CardTitle className="text-xl font-semibold text-gray-900">
                  Insider Trading Analytics
                </CardTitle>
                <CardDescription className="text-sm" style={{ color: "#666666" }}>
                  Comprehensive analysis of insider trading activities
                </CardDescription>
              </div>
            </div>
          </CardHeader>
        </Card>
      </div>

      {/* Global filter bar */}
      <InsiderTradingFilterBar />

      {/* Key Metrics */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-3">
          <Lightbulb className="h-5 w-5 text-[#75479C]" />
          <h3 className="text-lg font-semibold text-gray-900">Key Metrics</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {topInsights.map((insight, index) => (
            <div key={index} className="bg-white border rounded-md p-4 shadow-sm">
              <div className="flex items-center gap-3 mb-2">
                <insight.icon className="h-5 w-5 text-[#75479C] flex-shrink-0" />
                <h4 className="font-medium text-sm text-gray-900">{insight.title}</h4>
              </div>
              <div className="border-t border-gray-200 pt-2">
                <p className="text-2xl font-bold text-gray-900 text-center">{insight.value}</p>
                {insight.change && (
                  <p className={`text-xs text-center mt-1 ${insight.changeType === "positive" ? "text-green-600" :
                      insight.changeType === "negative" ? "text-red-600" : "text-gray-500"
                    }`}>
                    {insight.change}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Movement Analysis */}
      <div className="mb-6">
        <Card className="border rounded-md shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              <Activity className="h-5 w-5 text-[#75479C]" />
              Movement Analysis
            </CardTitle>
            <CardDescription className="text-sm" style={{ color: "#666666" }}>
              Overview of insider trading activities
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-green-50 border border-green-200 rounded-md p-4 flex flex-col items-center">
                <div className="text-2xl font-semibold text-green-800">{details?.summary?.added_count?.toLocaleString() ?? "0"}</div>
                <div className="text-green-700 text-xs mt-1">New Investors</div>
              </div>
              <div className="bg-red-50 border border-red-200 rounded-md p-4 flex flex-col items-center">
                <div className="text-2xl font-semibold text-red-800">{details?.summary?.removed_count?.toLocaleString() ?? "0"}</div>
                <div className="text-red-700 text-xs mt-1">Full Exits</div>
              </div>
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 flex flex-col items-center">
                <div className="text-2xl font-semibold text-yellow-800">{details?.summary?.changed_count?.toLocaleString() ?? "0"}</div>
                <div className="text-yellow-700 text-xs mt-1">Modified Positions</div>
              </div>
              <div className="bg-gray-50 border border-gray-200 rounded-md p-4 flex flex-col items-center">
                <div className="text-2xl font-semibold text-gray-800">{details?.summary?.unchanged_count?.toLocaleString() ?? "0"}</div>
                <div className="text-gray-700 text-xs mt-1">Unchanged</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analysis — 15 records per tab */}
      <div className="mb-6">
        <Card className="border rounded-md shadow-sm">
          <CardHeader>
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <CardTitle className="text-lg font-semibold text-gray-900">Detailed Analysis</CardTitle>
                <CardDescription className="text-sm" style={{ color: "#666666" }}>
                  Top 15 movers in insider trading activities
                </CardDescription>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button variant={activeTab === "new" ? "default" : "outline"} onClick={() => setActiveTab("new")}
                  className={activeTab === "new" ? "bg-[#4CAF50] text-white" : ""}>
                  New Investors ({details?.top_new_investors?.length ?? 0})
                </Button>
                <Button variant={activeTab === "exits" ? "default" : "outline"} onClick={() => setActiveTab("exits")}
                  className={activeTab === "exits" ? "bg-[#EF4444] text-white" : ""}>
                  Exits ({details?.top_exits?.length ?? 0})
                </Button>
                <Button variant={activeTab === "buyers" ? "default" : "outline"} onClick={() => setActiveTab("buyers")}
                  className={activeTab === "buyers" ? "bg-[#2196F3] text-white" : ""}>
                  Top Buyers ({details?.top_buyers?.length ?? 0})
                </Button>
                <Button variant={activeTab === "sellers" ? "default" : "outline"} onClick={() => setActiveTab("sellers")}
                  className={activeTab === "sellers" ? "bg-[#FF9800] text-white" : ""}>
                  Top Sellers ({details?.top_sellers?.length ?? 0})
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-medium text-gray-900">PAN/GIR</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Name</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Position Older</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Position Latest</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Difference</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Email</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Source</th>
                  </tr>
                </thead>
                <tbody>
                  {tableData.length > 0 ? (
                    tableData.map((record, index) => (
                      <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-3 px-4 font-mono text-sm">{record.pangir?.trim() || "N/A"}</td>
                        <td className="py-3 px-4 font-medium text-gray-900">{displayName(record)}</td>
                        <td className="py-3 px-4">{record.position_older?.toLocaleString() ?? "0"}</td>
                        <td className="py-3 px-4">{record.position_latest?.toLocaleString() ?? "0"}</td>
                        <td className={`py-3 px-4 font-medium ${record.position_difference > 0 ? "text-green-600" :
                            record.position_difference < 0 ? "text-red-600" : "text-gray-600"
                          }`}>
                          {record.position_difference > 0 ? "+" : ""}
                          {record.position_difference?.toLocaleString() ?? "0"}
                        </td>
                        <td className="py-3 px-4 text-sm">{record.email?.trim() || "N/A"}</td>
                        <td className="py-3 px-4 text-sm">{displaySource(record)}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={7} className="text-center py-10 text-gray-500">
                        No data available for the selected filters
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Footer */}
      <div className="mt-8 text-center">
        <p className="text-gray-600 text-sm">
          📊 Data based on insider trading records | Analysis for{" "}
          {details?.summary?.total_investors?.toLocaleString() ?? "0"} investors across{" "}
          {details?.summary?.total_companies ?? "0"} companies
        </p>
      </div>
    </div>
  );
};

export default EnhancedInsiderTradingAnalytics;
