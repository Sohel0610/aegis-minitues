import { useState, useEffect } from "react";
import { Database, Search, AlertCircle, CheckCircle, Loader2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useInsiderTradingFilters } from "@/contexts/InsiderTradingFilterContext";
import InsiderTradingFilterBar from "@/components/InsiderTradingFilterBar";

// ── Types ─────────────────────────────────────────────────────────
interface InsiderRecord {
  id?: number;
  company?: string;
  batch?: string;
  depository?: string;
  pangir: string;
  name: string;
  email: string;
  position_latest: number;
  position_older: number;
  position_difference: number;
  status: string;
  source?: string;
}

interface RecordsResponse {
  records: InsiderRecord[];
  total: number;
  limit: number;
  offset: number;
}

const RECORDS_PER_PAGE = 15;

// ── Component ─────────────────────────────────────────────────────
const InsiderTradingMasterData = () => {
  const { filters, buildQuery } = useInsiderTradingFilters();
  const [records, setRecords] = useState<InsiderRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [searchTerm, setSearchTerm] = useState("");
  const [counts, setCounts] = useState<Record<string, number>>({ ADDED: 0, REMOVED: 0, CHANGED: 0, UNCHANGED: 0, TOTAL: 0 });

  // Refetch whenever global filters or status changes
  useEffect(() => {
    setOffset(0);
    fetchCounts();
  }, [filters.company, filters.batch, filters.depository]);

  useEffect(() => {
    fetchRecords();
  }, [filters.company, filters.batch, filters.depository, statusFilter, offset]);

  const fetchCounts = async () => {
    try {
      const qs = buildQuery();
      const res = await fetch(`/api/insider-trading/counts${qs}`);
      if (res.ok) {
        const data = await res.json();
        setCounts(data);
      }
    } catch (err) {
      console.error("Error fetching counts:", err);
    }
  };

  const fetchRecords = async () => {
    try {
      setLoading(true);
      setError(null);

      const extra: Record<string, string | number> = { limit: RECORDS_PER_PAGE, offset };
      if (statusFilter) extra.status = statusFilter;

      const qs = buildQuery(extra);
      const res = await fetch(`/api/insider-trading/records${qs}`);
      if (!res.ok) throw new Error("Failed to fetch records");


      const data: RecordsResponse = await res.json();
      setRecords(data.records || []);
      setTotal(data.total || 0);
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

  const getStatusColor = (status: string) => {
    switch (status?.toUpperCase()) {
      case "ADDED": return "bg-green-100 text-green-800 border-green-200";
      case "REMOVED": return "bg-red-100 text-red-800 border-red-200";
      case "CHANGED": return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "UNCHANGED": return "bg-gray-100 text-gray-700 border-gray-200";
      default: return "bg-gray-100 text-gray-700 border-gray-200";
    }
  };

  // Search filtering (client-side on current page)
  const displayedRecords = records.filter((r) => {
    if (!searchTerm) return true;
    const q = searchTerm.toLowerCase();
    return (
      r.pangir?.toLowerCase().includes(q) ||
      r.name?.toLowerCase().includes(q) ||
      r.email?.toLowerCase().includes(q) ||
      r.company?.toLowerCase().includes(q)
    );
  });

  const totalPages = Math.ceil(total / RECORDS_PER_PAGE);
  const currentPage = Math.floor(offset / RECORDS_PER_PAGE) + 1;

  // ── Render ────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen p-4 md:p-6" style={{ background: "#ffffff" }}>
      {/* Header */}
      <div className="mb-6">
        <Card className="border-0 shadow-none bg-transparent">
          <CardHeader className="px-0 pb-3">
            <div className="flex items-center gap-2.5">
              <Database className="h-7 w-7" style={{ color: "#75479C" }} />
              <div>
                <CardTitle className="text-xl font-semibold text-gray-900">Master Data</CardTitle>
                <CardDescription className="text-sm" style={{ color: "#666666" }}>
                  Individual shareholder records — showing {RECORDS_PER_PAGE} records per page
                </CardDescription>
              </div>
            </div>
          </CardHeader>
        </Card>
      </div>

      {/* Global filter bar */}
      <InsiderTradingFilterBar />

      {/* Status filter buttons */}
      <div className="mb-4 flex flex-wrap gap-2 items-center">
        <span className="text-sm font-medium text-gray-700 mr-2">Status:</span>
        <Button
          variant={!statusFilter ? "default" : "outline"}
          size="sm"
          onClick={() => { setStatusFilter(""); setOffset(0); }}
          className={!statusFilter ? "bg-[#75479C] text-white" : ""}
        >
          All ({counts.TOTAL?.toLocaleString()})
        </Button>
        <Button
          variant={statusFilter === "ADDED" ? "default" : "outline"}
          size="sm"
          onClick={() => { setStatusFilter("ADDED"); setOffset(0); }}
          className={statusFilter === "ADDED" ? "bg-green-600 text-white" : ""}
        >
          Added ({counts.ADDED?.toLocaleString()})
        </Button>
        <Button
          variant={statusFilter === "REMOVED" ? "default" : "outline"}
          size="sm"
          onClick={() => { setStatusFilter("REMOVED"); setOffset(0); }}
          className={statusFilter === "REMOVED" ? "bg-red-600 text-white" : ""}
        >
          Removed ({counts.REMOVED?.toLocaleString()})
        </Button>
        <Button
          variant={statusFilter === "CHANGED" ? "default" : "outline"}
          size="sm"
          onClick={() => { setStatusFilter("CHANGED"); setOffset(0); }}
          className={statusFilter === "CHANGED" ? "bg-yellow-600 text-white" : ""}
        >
          Changed ({counts.CHANGED?.toLocaleString()})
        </Button>
        <Button
          variant={statusFilter === "UNCHANGED" ? "default" : "outline"}
          size="sm"
          onClick={() => { setStatusFilter("UNCHANGED"); setOffset(0); }}
          className={statusFilter === "UNCHANGED" ? "bg-gray-600 text-white" : ""}
        >
          Unchanged ({counts.UNCHANGED?.toLocaleString()})
        </Button>
      </div>

      {/* Records Table */}
      <Card className="border rounded-md shadow-sm">
        <CardHeader className="border-b">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <CardTitle className="text-lg font-semibold text-gray-900">Shareholder Records</CardTitle>
              <CardDescription className="text-sm" style={{ color: "#666666" }}>
                Showing {RECORDS_PER_PAGE} of {total.toLocaleString()} total records (Page {currentPage} of {totalPages || 1})
              </CardDescription>
            </div>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                type="text"
                placeholder="Search PAN, name, email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border rounded-md w-64"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-[#75479C]" />
              <span className="ml-3 text-gray-600">Loading records...</span>
            </div>
          ) : error ? (
            <div className="text-center py-10">
              <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-2" />
              <p className="text-red-600">{error}</p>
              <Button onClick={fetchRecords} variant="outline" className="mt-3">Retry</Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-medium text-gray-900">PAN/GIR</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Name</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Older</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Latest</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Diff</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Status</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Company</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Depository</th>
                  </tr>
                </thead>
                <tbody>
                  {displayedRecords.length > 0 ? (
                    displayedRecords.map((record, idx) => (
                      <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
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
                        <td className="py-3 px-4">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getStatusColor(record.status)}`}>
                            {record.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-sm">{record.company || "—"}</td>
                        <td className="py-3 px-4 text-sm">{record.depository || "—"}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={8} className="text-center py-10 text-gray-500">
                        No records found for the selected filters
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {!loading && !error && total > RECORDS_PER_PAGE && (
            <div className="flex items-center justify-between px-4 py-3 border-t bg-gray-50">
              <div className="text-sm text-gray-600">
                Showing {offset + 1}–{Math.min(offset + RECORDS_PER_PAGE, total)} of {total.toLocaleString()} records
                <span className="ml-2 text-gray-400">({RECORDS_PER_PAGE} per page)</span>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={offset === 0}
                  onClick={() => setOffset(Math.max(0, offset - RECORDS_PER_PAGE))}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={offset + RECORDS_PER_PAGE >= total}
                  onClick={() => setOffset(offset + RECORDS_PER_PAGE)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default InsiderTradingMasterData;