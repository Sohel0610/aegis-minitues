import { useState, useEffect } from "react";
import { Database, AlertCircle, Search, Loader2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useInsiderTradingFilters } from "@/contexts/InsiderTradingFilterContext";
import InsiderTradingFilterBar from "@/components/InsiderTradingFilterBar";

// ── Types ─────────────────────────────────────────────────────────
interface SummaryRow {
  id?: number;
  company: string;
  batch: string;
  depository: string;
  added: number;
  removed: number;
  changed: number;
  unchanged: number;
  total: number;
  empty_pangir_latest?: number;
  empty_pangir_older?: number;
}

// ── Component ─────────────────────────────────────────────────────
const InsiderTradingDataSource = () => {
  const { filters, buildQuery } = useInsiderTradingFilters();
  const [summaryRows, setSummaryRows] = useState<SummaryRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  // Refetch whenever global filters change
  useEffect(() => {
    fetchData();
  }, [filters.company, filters.batch, filters.depository]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const qs = buildQuery();
      const res = await fetch(`/api/insider-trading/summary/detail${qs}`);
      if (!res.ok) throw new Error("Failed to fetch summary data");
      const data = await res.json();
      setSummaryRows(data.summary || []);
    } catch (err) {
      console.error("Error fetching data:", err);
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  const filteredRows = summaryRows.filter((row) =>
    row.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
    row.batch.toLowerCase().includes(searchTerm.toLowerCase()) ||
    row.depository.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Aggregate totals
  const totals = filteredRows.reduce(
    (acc, r) => ({
      added: acc.added + (r.added || 0),
      removed: acc.removed + (r.removed || 0),
      changed: acc.changed + (r.changed || 0),
      unchanged: acc.unchanged + (r.unchanged || 0),
      total: acc.total + (r.total || 0),
    }),
    { added: 0, removed: 0, changed: 0, unchanged: 0, total: 0 }
  );

  // ── Render ────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "#ffffff" }}>
        <div className="text-center">
          <Loader2 className="h-10 w-10 animate-spin mx-auto mb-3" style={{ color: "#75479C" }} />
          <p className="text-base text-gray-900">Loading data sources...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "#ffffff" }}>
        <div className="text-center p-5 max-w-md">
          <AlertCircle className="h-10 w-10 mx-auto mb-3" style={{ color: "#EF4444" }} />
          <h2 className="text-lg font-semibold mb-2 text-gray-900">Error Loading Data</h2>
          <p className="mb-3 text-sm text-gray-700">{error}</p>
          <Button onClick={fetchData} className="bg-[#75479C] hover:bg-[#5a357a] text-white">Retry</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 md:p-6" style={{ background: "#ffffff" }}>
      {/* Header */}
      <div className="mb-6">
        <Card className="border-0 shadow-none bg-transparent">
          <CardHeader className="px-0 pb-3">
            <div className="flex items-center gap-2.5">
              <Database className="h-7 w-7" style={{ color: "#75479C" }} />
              <div>
                <CardTitle className="text-xl font-semibold text-gray-900">Data Sources</CardTitle>
                <CardDescription className="text-sm" style={{ color: "#666666" }}>
                  Summary of insider trading data per company, batch, and depository
                </CardDescription>
              </div>
            </div>
          </CardHeader>
        </Card>
      </div>

      {/* Global filter bar */}
      <InsiderTradingFilterBar />

      {/* Aggregate summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
        <div className="bg-white border rounded-md p-3 text-center shadow-sm">
          <div className="text-2xl font-bold text-gray-900">{totals.total.toLocaleString()}</div>
          <div className="text-xs text-gray-500 mt-1">Total Records</div>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-md p-3 text-center">
          <div className="text-2xl font-bold text-green-800">{totals.added.toLocaleString()}</div>
          <div className="text-xs text-green-700 mt-1">Added</div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-md p-3 text-center">
          <div className="text-2xl font-bold text-red-800">{totals.removed.toLocaleString()}</div>
          <div className="text-xs text-red-700 mt-1">Removed</div>
        </div>
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 text-center">
          <div className="text-2xl font-bold text-yellow-800">{totals.changed.toLocaleString()}</div>
          <div className="text-xs text-yellow-700 mt-1">Changed</div>
        </div>
        <div className="bg-gray-50 border border-gray-200 rounded-md p-3 text-center">
          <div className="text-2xl font-bold text-gray-700">{totals.unchanged.toLocaleString()}</div>
          <div className="text-xs text-gray-500 mt-1">Unchanged</div>
        </div>
      </div>

      {/* Summary Table */}
      <div className="mb-6">
        <Card className="border rounded-md shadow-sm">
          <CardHeader className="border-b">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <CardTitle className="text-lg font-semibold text-gray-900">Company Summary</CardTitle>
                <CardDescription className="text-sm" style={{ color: "#666666" }}>
                  {filteredRows.length} summary rows found
                </CardDescription>
              </div>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  type="text"
                  placeholder="Search companies..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 border rounded-md w-64"
                />
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Company</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Batch</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Depository</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-900">Total</th>
                    <th className="text-right py-3 px-4 font-medium text-green-700">Added</th>
                    <th className="text-right py-3 px-4 font-medium text-red-700">Removed</th>
                    <th className="text-right py-3 px-4 font-medium text-yellow-700">Changed</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-500">Unchanged</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRows.length > 0 ? (
                    filteredRows.map((row, idx) => (
                      <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-3 px-4 font-medium text-gray-900">{row.company}</td>
                        <td className="py-3 px-4 text-sm text-gray-700">{row.batch}</td>
                        <td className="py-3 px-4">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${row.depository === "CDSL" ? "bg-purple-100 text-purple-800" :
                              row.depository === "NSDL" ? "bg-blue-100 text-blue-800" :
                                "bg-orange-100 text-orange-800"
                            }`}>
                            {row.depository}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right font-semibold text-gray-900">{row.total?.toLocaleString()}</td>
                        <td className="py-3 px-4 text-right text-green-600 font-medium">{row.added?.toLocaleString()}</td>
                        <td className="py-3 px-4 text-right text-red-600 font-medium">{row.removed?.toLocaleString()}</td>
                        <td className="py-3 px-4 text-right text-yellow-600 font-medium">{row.changed?.toLocaleString()}</td>
                        <td className="py-3 px-4 text-right text-gray-500">{row.unchanged?.toLocaleString()}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={8} className="text-center py-10 text-gray-500">
                        No summary data available for the selected filters
                      </td>
                    </tr>
                  )}
                </tbody>
                {filteredRows.length > 0 && (
                  <tfoot>
                    <tr className="border-t-2 border-gray-300 bg-gray-50 font-semibold">
                      <td className="py-3 px-4 text-gray-900" colSpan={3}>Total</td>
                      <td className="py-3 px-4 text-right text-gray-900">{totals.total.toLocaleString()}</td>
                      <td className="py-3 px-4 text-right text-green-600">{totals.added.toLocaleString()}</td>
                      <td className="py-3 px-4 text-right text-red-600">{totals.removed.toLocaleString()}</td>
                      <td className="py-3 px-4 text-right text-yellow-600">{totals.changed.toLocaleString()}</td>
                      <td className="py-3 px-4 text-right text-gray-500">{totals.unchanged.toLocaleString()}</td>
                    </tr>
                  </tfoot>
                )}
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default InsiderTradingDataSource;
