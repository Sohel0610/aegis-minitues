import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { RefreshCw, Activity, Bell, TrendingUp, FileText, Loader2, AlertCircle, Calendar as CalendarIcon, X } from "lucide-react";
import SEBIAnalysisDashboardLayout from "@/components/layout/SEBIAnalysisDashboardLayout";
import SEBIDailyTrendChart from "@/components/charts/SEBIDailyTrendChart";
import SEBIMonthlyTrendChart from "@/components/charts/SEBIMonthlyTrendChart";
import SEBIWeeklyPieChart from "@/components/charts/SEBIWeeklyPieChart";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import ExcelView from "../components/ui/ExcelView";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { format } from "date-fns";

import NotificationDetailsModal from "@/components/NotificationDetailsModal";
import { sebiService, SEBIExcelSummary } from "@/services/sebiService";
import {
  processDataForSEBIData,
  transformSEBIDataForExcelView,
  getLatestMonthYear,
  parseDate
} from "@/utils/sebiDashboardUtils";

const SEBIDashboard = () => {
  // Add scroll to top effect
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  const [selectedRecord, setSelectedRecord] = useState<any | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [sebiData, setSEBIData] = useState<any[] | null>(null);
  const [filteredSebiData, setFilteredSebiData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [chartData, setChartData] = useState<any>(null);
  const [useCache, setUseCache] = useState<boolean>(true);
  const [dateRange, setDateRange] = useState<{ from: Date | undefined; to: Date | undefined }>({
    from: undefined,
    to: undefined
  });
  const [isCalendarOpen, setIsCalendarOpen] = useState<boolean>(false);

  // Handle view notification
  const handleViewNotification = (record: any): void => {
    setSelectedRecord(record);
    setIsModalOpen(true);
  };

  // Handle opening external link
  const handleOpenLink = (url: string): void => {
    if (url.startsWith('http')) {
      window.open(url, '_blank', 'noopener,noreferrer');
    }
  };

  // Handle date range selection
  const handleDateRangeSelect = (range: { from: Date | undefined; to: Date | undefined } | undefined): void => {
    if (range) {
      setDateRange(range);
      if (range.from && range.to) {
        setIsCalendarOpen(false);
      }
    }
  };

  // Clear date range filter
  const clearDateRange = (): void => {
    setDateRange({ from: undefined, to: undefined });
  };

  // Filter data based on date range
  useEffect(() => {
    if (!sebiData) return;

    if (!dateRange.from && !dateRange.to) {
      const parseDateFn = (s: any) => parseDate(s);
      let latest: Date | null = null;
      for (const row of sebiData) {
        const d = parseDateFn(row["Date"]);
        if (d && (!latest || d > latest)) latest = d;
      }
      if (latest) {
        const lm = latest.getMonth();
        const ly = latest.getFullYear();
        const onlyLatest = sebiData.filter(row => {
          const d = parseDateFn(row["Date"]);
          return d && d.getMonth() === lm && d.getFullYear() === ly;
        });
        setFilteredSebiData(onlyLatest);
        return;
      }
      setFilteredSebiData(sebiData);
      return;
    }

    const filtered = sebiData.filter(row => {
      const dateValue = row["Date"];
      if (!dateValue) return true;

      try {
        // Parse the date string
        let rowDate: Date;
        const parsed = parseDate(dateValue);
        if (parsed) {
          rowDate = parsed;
        } else {
          // Original logic fallback if needed, but parseDate covers most cases
          const dateString = String(dateValue);
          rowDate = new Date(dateString);
        }


        // Check if rowDate is valid
        if (isNaN(rowDate.getTime())) return true;

        // Check if date is within range
        const fromValid = !dateRange.from || rowDate >= dateRange.from;
        const toValid = !dateRange.to || rowDate <= dateRange.to;

        return fromValid && toValid;
      } catch (e) {
        console.error("Error parsing date:", dateValue, e);
        return true;
      }
    });

    setFilteredSebiData(filtered);

    // Update chart data with filtered data
    if (filtered.length > 0) {
      const processedChartData = processDataForSEBIData(filtered);
      setChartData(processedChartData);
    }
  }, [sebiData, dateRange]);

  // Handle refresh with optimizations
  const handleRefresh = useCallback(async (): Promise<void> => {
    try {
      setLoading(true);
      setError(null);

      // Fetch SEBI data from the new endpoint
      // Fetch SEBI data from the new endpoint
      const sebiDataResponse = await sebiService.fetchSEBIData(10000, 0); // Fetch all valid records
      const sebiData = sebiDataResponse.data;

      // Process data for charts
      const processedChartData = processDataForSEBIData(sebiData);
      setChartData(processedChartData);

      // Transform data for ExcelView
      const transformedData = transformSEBIDataForExcelView(sebiData);

      setSEBIData(transformedData);
    } catch (err) {
      console.error("Error refreshing SEBI data:", err);
      setError(err instanceof Error ? err.message : "Failed to refresh SEBI data");
    } finally {
      setLoading(false);
    }
  }, []);

  // Load SEBI data on component mount
  useEffect(() => {
    const loadSEBIData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch SEBI data from the new endpoint
        // Fetch SEBI data from the new endpoint
        const sebiDataResponse = await sebiService.fetchSEBIData(10000, 0); // Fetch all valid records
        const sebiData = sebiDataResponse.data;

        // Filter out NIL records
        const filteredData = sebiData.filter((item: SEBIExcelSummary) =>
          item.pdf_link !== 'NIL' && item.summary !== 'NIL'
        );

        // Process data for charts
        const processedChartData = processDataForSEBIData(filteredData);
        setChartData(processedChartData);

        // Transform data for ExcelView
        const transformedData = transformSEBIDataForExcelView(filteredData);

        setSEBIData(transformedData);
      } catch (err) {
        console.error("Error loading SEBI data:", err);
        setError(err instanceof Error ? err.message : "Failed to load SEBI data");
      } finally {
        setLoading(false);
      }
    };

    loadSEBIData();
  }, []);

  if (loading && !sebiData) {
    return (
      <SEBIAnalysisDashboardLayout>
        <div className="min-h-screen flex items-center justify-center" style={{ background: "#ffffff" }}>
          <div className="text-center">
            <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4" style={{ color: "#BD3861" }} />
            <p className="text-lg" style={{ color: "#000000" }}>Loading SEBI Dashboard data...</p>
          </div>
        </div>
      </SEBIAnalysisDashboardLayout>
    );
  }

  if (error && !sebiData) {
    return (
      <SEBIAnalysisDashboardLayout>
        <div className="min-h-screen flex items-center justify-center" style={{ background: "#ffffff" }}>
          <div className="text-center p-6 max-w-md">
            <AlertCircle className="h-12 w-12 mx-auto mb-4" style={{ color: "#EF4444" }} />
            <h2 className="text-xl font-bold mb-2" style={{ color: "#000000" }}>Error Loading SEBI Dashboard Data</h2>
            <p className="mb-4" style={{ color: "#000000" }}>{error}</p>
            <Button
              onClick={handleRefresh}
              style={{
                backgroundColor: '#BD3861',
                borderColor: '#BD3861',
                color: 'white'
              }}
            >
              Retry
            </Button>
          </div>
        </div>
      </SEBIAnalysisDashboardLayout>
    );
  }

  return (
    <SEBIAnalysisDashboardLayout>
      <div className="min-h-screen" style={{
        background: "#ffffff"
      }}>
        {/* Main Content Container */}
        <div className="w-full px-4">
          {/* Header Section */}
          <motion.div
            initial={{ opacity: 0, y: -30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1.0, ease: "easeOut" }}
            className="mb-8"
          >
            <Card className="border-0 shadow-none bg-transparent">
              <CardHeader className="px-0 pb-4">
                <div className="flex items-center gap-3 mb-2">
                  <Activity className="h-8 w-8" style={{ color: "#BD3861" }} />
                  <CardTitle className="text-2xl sm:text-3xl lg:text-4xl font-bold" style={{ color: "#000000" }}>
                    SEBI DASHBOARD
                  </CardTitle>
                </div>
                <CardDescription className="text-lg" style={{ color: '#000000' }}>
                  Real-time monitoring and analytics for Securities and Exchange Board of India notifications
                </CardDescription>
              </CardHeader>
            </Card>
          </motion.div>

          {/* 4-Tile Grid Layout: 1 Stats Tile + 3 Chart Tiles */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-0 mb-12">
            {/* Total Notifications Tile - Top Left */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1.2, delay: 0.3 }}
              className="lg:col-span-1 h-[250px]"
            >
              <Card className="h-full" style={{
                background: "#ffffff",
                border: 'none',
                boxShadow: 'none'
              }}>
                <CardHeader className="relative pb-1">
                  <div className="relative z-10 flex items-center gap-1">
                    <Bell className="h-5 w-5" style={{ color: "#0B74B0" }} />
                    <div>
                      <CardTitle className="text-base font-semibold font-mono leading-tight" style={{ color: '#010741' }}>
                        Total Notifications
                      </CardTitle>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="flex flex-col justify-center items-center h-full pb-2">
                  <motion.div
                    animate={{
                      scale: [1, 1.05, 1],
                      opacity: [0.8, 1, 0.8]
                    }}
                    transition={{
                      duration: 3,
                      repeat: Infinity,
                      ease: "easeInOut"
                    }}
                    className="text-center"
                  >
                    <div className="text-4xl font-bold font-mono mb-2" style={{ color: '#0B74B0' }}>
                      {sebiData?.length || 0}
                    </div>
                    <div className="text-sm font-mono" style={{ color: 'rgba(1, 7, 65, 0.8)' }}>
                      Till Date
                    </div>
                    <div className="flex items-center justify-center gap-1 mt-2">
                      <TrendingUp size={14} style={{ color: '#0B74B0' }} />
                      <span className="text-xs font-mono" style={{ color: '#BD3861' }}>LIVE MONITORING</span>
                    </div>
                  </motion.div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Daily Trend Chart - Top Right */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1.2, delay: 0.6 }}
              className="lg:col-span-1 h-[250px]"
            >
              <SEBIDailyTrendChart data={chartData?.daily || []} />
            </motion.div>

            {/* Monthly Trend Chart - Bottom Left */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1.2, delay: 0.9 }}
              className="lg:col-span-1 h-[250px]"
            >
              <SEBIMonthlyTrendChart data={chartData?.monthly || []} />
            </motion.div>

            {/* Weekly Trend Chart (now with pie chart) - Bottom Right */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1.2, delay: 1.2 }}
              className="lg:col-span-1 h-[250px]"
            >
              <SEBIWeeklyPieChart data={chartData?.weekly || []} />
            </motion.div>
          </div>

          {/* Excel View Section with proper spacing */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1.2, delay: 1.8 }}
            className="mt-8"
          >
            {filteredSebiData ? (
              <ExcelView
                initialData={filteredSebiData}
                columns={['Date', 'PDF Link', 'Summary']}
                title={`${getLatestMonthYear(filteredSebiData)} Notifications`}
                onViewRow={(row, rowIndex) => {
                  handleViewNotification(row);
                }}
                initializeWithEmptyRows={false}
                columnWidths={{
                  'Date': '120px',
                  'PDF Link': '150px',
                  'Summary': 'minmax(200px, 2fr)'
                }}
                enableDateRangeFilter={true}
                onDateRangeChange={handleDateRangeSelect}
                initialDateRange={dateRange}
              />
            ) : (
              <ExcelView
                initialData={[]}
                columns={['Date', 'PDF Link', 'Summary']}
                title={`${getLatestMonthYear([])} Notifications`}
                onViewRow={(row, rowIndex) => {
                  handleViewNotification(row);
                }}
                initializeWithEmptyRows={false}
                columnWidths={{
                  'Date': '120px',
                  'PDF Link': '150px',
                  'Summary': 'minmax(200px, 2fr)'
                }}
                enableDateRangeFilter={true}
                onDateRangeChange={handleDateRangeSelect}
                initialDateRange={dateRange}
              />
            )}
          </motion.div>

          {/* System Status Footer - REMOVED as per user request */}
        </div>
        </div>
        {/* Notification Details Modal */}
        <NotificationDetailsModal
          isOpen={isModalOpen}
          onOpenChange={setIsModalOpen}
          record={selectedRecord}
        />
    </SEBIAnalysisDashboardLayout>
  );
};

export default SEBIDashboard;
