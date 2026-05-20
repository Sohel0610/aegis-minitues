import { useState, useEffect } from "react";
import { Loader2, AlertCircle, RefreshCw, CheckCircle, HelpCircle, FileSpreadsheet, ShieldAlert, Award, UserCheck } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface SummaryMetrics {
  total_declarations: number;
  total_holdings: number;
  total_preclearances: number;
  unsanctioned_trades_count: number;
  volume_breaches_count: number;
  holding_discrepancies_count: number;
}

interface ViolationRecord {
  shareholder_name?: string;
  pan?: string;
  company_name?: string;
  shares_traded?: number;
  batch_name?: string;
  transaction_date?: string;
  employee_name?: string;
  employee_email?: string;
  approved_volume?: number;
  excess_volume?: number;
  ritm_number?: string;
  declarant_name?: string;
  relationship?: string;
  declared_quantity?: number;
  depository_quantity?: number;
  difference?: number;
  phase?: string;
  fiscal_year?: string;
}

interface SyncStep {
  step: string;
  status: string;
  detail: string;
}

interface SyncResult {
  message: string;
  api_fetched: boolean;
  new_records_from_api: number;
  steps: SyncStep[];
}

const ServiceNowReconciliation = () => {
  const [activeTab, setActiveTab] = useState<'UNSANCTIONED' | 'VOLUME_BREACH' | 'HOLDING_MISMATCH'>('UNSANCTIONED');
  const [summary, setSummary] = useState<SummaryMetrics | null>(null);
  const [violations, setViolations] = useState<ViolationRecord[]>([]);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [loadingViolations, setLoadingViolations] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncPhase, setSyncPhase] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [syncResult, setSyncResult] = useState<SyncResult | null>(null);

  useEffect(() => {
    fetchSummary();
  }, []);

  useEffect(() => {
    fetchViolations();
  }, [activeTab]);

  const fetchSummary = async () => {
    try {
      setLoadingSummary(true);
      const res = await fetch("/api/servicenow/summary");
      if (!res.ok) throw new Error("Failed to fetch ServiceNow summary metadata");
      const data = await res.json();
      setSummary(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingSummary(false);
    }
  };

  const fetchViolations = async () => {
    try {
      setLoadingViolations(true);
      setError(null);
      const res = await fetch(`/api/servicenow/violations?type=${activeTab}&limit=100`);
      if (!res.ok) throw new Error("Failed to fetch violations records");
      const data = await res.json();
      setViolations(data.violations || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load violations details");
    } finally {
      setLoadingViolations(false);
    }
  };

  const handleSync = async () => {
    try {
      setSyncing(true);
      setSyncResult(null);
      setError(null);
      setSyncPhase('Connecting to ServiceNow API...');

      const res = await fetch("/api/servicenow/sync", { method: "POST" });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Synchronization request failed");
      }

      const data: SyncResult = await res.json();
      setSyncResult(data);

      // Refresh dashboard data
      setSyncPhase('Refreshing dashboard...');
      await fetchSummary();
      await fetchViolations();

      setTimeout(() => {
        setSyncResult(null);
      }, 12000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to sync ServiceNow records");
    } finally {
      setSyncing(false);
      setSyncPhase('');
    }
  };

  const getStepIcon = (status: string) => {
    if (status === 'success') return <CheckCircle className="h-4 w-4 text-green-600 flex-shrink-0" />;
    if (status === 'error') return <AlertCircle className="h-4 w-4 text-red-600 flex-shrink-0" />;
    return <HelpCircle className="h-4 w-4 text-amber-500 flex-shrink-0" />;
  };

  const getStepLabel = (step: string) => {
    if (step === 'fetch_api') return 'ServiceNow API';
    if (step === 'save_json') return 'Save JSON File';
    if (step === 'db_ingestion') return 'Database Update';
    return step;
  };

  return (
    <div className="min-h-screen p-4 md:p-6" style={{ background: "#ffffff" }}>
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6 border-b border-gray-100 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <ShieldAlert className="h-7 w-7 text-[#75479C]" />
            ServiceNow PIT Compliance
          </h1>
          <p className="text-sm text-gray-600">
            Compare ServiceNow employee disclosures & pre-clearance approvals against CDSL/NSDL depository trade logs.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={handleSync}
            disabled={syncing}
            className="bg-[#75479C] hover:bg-[#5a357a] text-white flex items-center gap-2"
          >
            {syncing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            {syncing ? (syncPhase || "Syncing...") : "Sync ServiceNow Data"}
          </Button>
        </div>
      </div>

      {/* Sync Result Steps */}
      {syncResult && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-md">
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0" />
            <span className="text-sm font-semibold text-green-900">{syncResult.message}</span>
            {syncResult.new_records_from_api > 0 && (
              <span className="ml-2 px-2 py-0.5 bg-green-200 text-green-900 text-xs font-bold rounded">
                +{syncResult.new_records_from_api} new records
              </span>
            )}
          </div>
          <div className="space-y-1.5">
            {syncResult.steps.map((s, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                {getStepIcon(s.status)}
                <span className="font-semibold text-gray-700 w-28">{getStepLabel(s.step)}</span>
                <span className="text-gray-600">{s.detail}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-800 rounded-md flex items-center gap-2.5">
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0" />
          <span className="text-sm font-medium">{error}</span>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        <Card className="border rounded-md shadow-sm">
          <CardHeader className="p-4 pb-2">
            <CardDescription className="text-xs font-semibold uppercase text-gray-500">Declarations</CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-xl font-bold text-gray-900">
              {loadingSummary ? <Loader2 className="h-5 w-5 animate-spin" /> : summary?.total_declarations ?? 0}
            </div>
            <p className="text-[10px] text-gray-500 mt-1">Submitted Forms</p>
          </CardContent>
        </Card>

        <Card className="border rounded-md shadow-sm">
          <CardHeader className="p-4 pb-2">
            <CardDescription className="text-xs font-semibold uppercase text-gray-500">Holdings Declared</CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-xl font-bold text-gray-900">
              {loadingSummary ? <Loader2 className="h-5 w-5 animate-spin" /> : summary?.total_holdings ?? 0}
            </div>
            <p className="text-[10px] text-gray-500 mt-1">Position Lines</p>
          </CardContent>
        </Card>

        <Card className="border rounded-md shadow-sm">
          <CardHeader className="p-4 pb-2">
            <CardDescription className="text-xs font-semibold uppercase text-gray-500">Pre-clearances</CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-xl font-bold text-gray-900">
              {loadingSummary ? <Loader2 className="h-5 w-5 animate-spin" /> : summary?.total_preclearances ?? 0}
            </div>
            <p className="text-[10px] text-gray-500 mt-1">Buy/Sell Applications</p>
          </CardContent>
        </Card>

        <Card className="border rounded-md shadow-sm bg-red-50 border-red-200">
          <CardHeader className="p-4 pb-2">
            <CardDescription className="text-xs font-semibold uppercase text-red-700">Unsanctioned Trades</CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-xl font-bold text-red-900">
              {loadingSummary ? <Loader2 className="h-5 w-5 animate-spin" /> : summary?.unsanctioned_trades_count ?? 0}
            </div>
            <p className="text-[10px] text-red-600 mt-1">No Pre-clearance Approved</p>
          </CardContent>
        </Card>

        <Card className="border rounded-md shadow-sm bg-orange-50 border-orange-200">
          <CardHeader className="p-4 pb-2">
            <CardDescription className="text-xs font-semibold uppercase text-orange-700">Volume Breaches</CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-xl font-bold text-orange-900">
              {loadingSummary ? <Loader2 className="h-5 w-5 animate-spin" /> : summary?.volume_breaches_count ?? 0}
            </div>
            <p className="text-[10px] text-orange-600 mt-1">Traded over approved limit</p>
          </CardContent>
        </Card>

        <Card className="border rounded-md shadow-sm bg-amber-50 border-amber-200">
          <CardHeader className="p-4 pb-2">
            <CardDescription className="text-xs font-semibold uppercase text-amber-700">Holding Mismatches</CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-xl font-bold text-amber-900">
              {loadingSummary ? <Loader2 className="h-5 w-5 animate-spin" /> : summary?.holding_discrepancies_count ?? 0}
            </div>
            <p className="text-[10px] text-amber-600 mt-1">Form vs Depository mismatch</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Tabbed Grid */}
      <Card className="border rounded-md shadow-sm">
        <CardHeader className="border-b border-gray-100">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div>
              <CardTitle className="text-base font-bold text-gray-900">Compliance Check Details</CardTitle>
              <CardDescription className="text-xs">
                Select a violation type to inspect matched records and discrepancies.
              </CardDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                variant={activeTab === 'UNSANCTIONED' ? 'default' : 'outline'}
                onClick={() => setActiveTab('UNSANCTIONED')}
                className={activeTab === 'UNSANCTIONED' ? 'bg-[#EF4444] hover:bg-[#DC2626] text-white' : ''}
              >
                Unsanctioned Trades ({summary?.unsanctioned_trades_count ?? 0})
              </Button>
              <Button
                variant={activeTab === 'VOLUME_BREACH' ? 'default' : 'outline'}
                onClick={() => setActiveTab('VOLUME_BREACH')}
                className={activeTab === 'VOLUME_BREACH' ? 'bg-[#F97316] hover:bg-[#EA580C] text-white' : ''}
              >
                Volume Breaches ({summary?.volume_breaches_count ?? 0})
              </Button>
              <Button
                variant={activeTab === 'HOLDING_MISMATCH' ? 'default' : 'outline'}
                onClick={() => setActiveTab('HOLDING_MISMATCH')}
                className={activeTab === 'HOLDING_MISMATCH' ? 'bg-[#F59E0B] hover:bg-[#D97706] text-white' : ''}
              >
                Holding Discrepancies ({summary?.holding_discrepancies_count ?? 0})
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loadingViolations ? (
            <div className="py-20 flex flex-col items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-[#75479C] mb-2" />
              <p className="text-sm text-gray-600">Calculating compliance metrics...</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50 text-gray-700 font-semibold">
                    {activeTab === 'UNSANCTIONED' && (
                      <>
                        <th className="text-left py-3 px-4">Insider Shareholder</th>
                        <th className="text-left py-3 px-4">PAN</th>
                        <th className="text-left py-3 px-4">Company</th>
                        <th className="text-left py-3 px-4">Employee / Owner</th>
                        <th className="text-left py-3 px-4">Traded Quantity</th>
                        <th className="text-left py-3 px-4">Batch Period</th>
                        <th className="text-left py-3 px-4">Date</th>
                      </>
                    )}
                    {activeTab === 'VOLUME_BREACH' && (
                      <>
                        <th className="text-left py-3 px-4">Insider Shareholder</th>
                        <th className="text-left py-3 px-4">PAN</th>
                        <th className="text-left py-3 px-4">Company</th>
                        <th className="text-left py-3 px-4">Employee / Owner</th>
                        <th className="text-left py-3 px-4">Traded Volume</th>
                        <th className="text-left py-3 px-4">Approved Volume</th>
                        <th className="text-left py-3 px-4">Excess Volume</th>
                        <th className="text-left py-3 px-4">RITM Ticket</th>
                        <th className="text-left py-3 px-4">Date</th>
                      </>
                    )}
                    {activeTab === 'HOLDING_MISMATCH' && (
                      <>
                        <th className="text-left py-3 px-4">Employee Name</th>
                        <th className="text-left py-3 px-4">Declared Shareholder</th>
                        <th className="text-left py-3 px-4">Relationship</th>
                        <th className="text-left py-3 px-4">PAN</th>
                        <th className="text-left py-3 px-4">Company</th>
                        <th className="text-left py-3 px-4">Declared Qty</th>
                        <th className="text-left py-3 px-4">Depository Qty</th>
                        <th className="text-left py-3 px-4">Difference</th>
                        <th className="text-left py-3 px-4">Declaration Ticket</th>
                        <th className="text-left py-3 px-4">Period</th>
                      </>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {violations.length > 0 ? (
                    violations.map((record, index) => (
                      <tr key={index} className="border-b border-gray-100 hover:bg-gray-50 text-gray-900">
                        {activeTab === 'UNSANCTIONED' && (
                          <>
                            <td className="py-3.5 px-4 font-medium">{record.shareholder_name}</td>
                            <td className="py-3.5 px-4 font-mono text-xs">{record.pan}</td>
                            <td className="py-3.5 px-4">{record.company_name}</td>
                            <td className="py-3.5 px-4">
                              <div>{record.employee_name}</div>
                              <div className="text-[10px] text-gray-500">{record.employee_email}</div>
                            </td>
                            <td className="py-3.5 px-4 font-bold text-red-600">
                              {record.shares_traded && record.shares_traded > 0 ? "+" : ""}
                              {record.shares_traded?.toLocaleString()}
                            </td>
                            <td className="py-3.5 px-4 text-xs text-gray-600">{record.batch_name}</td>
                            <td className="py-3.5 px-4 text-xs text-gray-600">{record.transaction_date}</td>
                          </>
                        )}
                        {activeTab === 'VOLUME_BREACH' && (
                          <>
                            <td className="py-3.5 px-4 font-medium">{record.shareholder_name}</td>
                            <td className="py-3.5 px-4 font-mono text-xs">{record.pan}</td>
                            <td className="py-3.5 px-4">{record.company_name}</td>
                            <td className="py-3.5 px-4">
                              <div>{record.employee_name}</div>
                              <div className="text-[10px] text-gray-500">{record.employee_email}</div>
                            </td>
                            <td className="py-3.5 px-4 font-semibold">{record.shares_traded?.toLocaleString()}</td>
                            <td className="py-3.5 px-4 text-gray-600">{record.approved_volume?.toLocaleString()}</td>
                            <td className="py-3.5 px-4 font-bold text-red-600">+{record.excess_volume?.toLocaleString()}</td>
                            <td className="py-3.5 px-4 font-mono text-xs text-[#75479C]">{record.ritm_number}</td>
                            <td className="py-3.5 px-4 text-xs text-gray-600">{record.transaction_date}</td>
                          </>
                        )}
                        {activeTab === 'HOLDING_MISMATCH' && (
                          <>
                            <td className="py-3.5 px-4 font-medium">
                              <div>{record.employee_name}</div>
                              <div className="text-[10px] text-gray-500">{record.employee_email}</div>
                            </td>
                            <td className="py-3.5 px-4 font-medium">{record.declarant_name}</td>
                            <td className="py-3.5 px-4 capitalize text-xs text-gray-600">{record.relationship}</td>
                            <td className="py-3.5 px-4 font-mono text-xs">{record.pan}</td>
                            <td className="py-3.5 px-4 text-xs">{record.company_name}</td>
                            <td className="py-3.5 px-4 text-gray-600">{record.declared_quantity?.toLocaleString()}</td>
                            <td className="py-3.5 px-4 font-semibold">{record.depository_quantity?.toLocaleString()}</td>
                            <td className="py-3.5 px-4 font-bold text-orange-600">
                              {record.difference && record.difference > 0 ? "+" : ""}
                              {record.difference?.toLocaleString()}
                            </td>
                            <td className="py-3.5 px-4 font-mono text-xs text-[#75479C]">{record.ritm_number}</td>
                            <td className="py-3.5 px-4 text-xs text-gray-600">
                              {record.fiscal_year} — {record.phase}
                            </td>
                          </>
                        )}
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={10} className="text-center py-16 text-gray-500">
                        <UserCheck className="h-10 w-10 mx-auto text-green-500 mb-2 opacity-55" />
                        <h4 className="font-semibold text-gray-900 text-sm mb-1">Compliance Clear</h4>
                        <p className="text-xs max-w-xs mx-auto">
                          No active {activeTab.toLowerCase().replace('_', ' ')} violations detected in the database records.
                        </p>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Footer information */}
      <div className="mt-8 text-center text-xs text-gray-600 max-w-2xl mx-auto">
        <p>
          🔒 Compliance data synced and audited automatically. Checks follow SEBI Prohibition of Insider Trading regulations.
        </p>
      </div>
    </div>
  );
};

export default ServiceNowReconciliation;
