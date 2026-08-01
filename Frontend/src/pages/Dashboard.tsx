import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { RefreshCw, Activity, Bell, TrendingUp, FileText, Loader2, AlertCircle, Calendar as CalendarIcon, X } from "lucide-react";
import BSEAlertsDashboardLayout from "@/components/layout/BSEAlertsDashboardLayout";
import MonthlyTrendChart from "@/components/charts/MonthlyTrendChart";
import WeeklyTrendChart from "@/components/charts/WeeklyTrendChart";
import DailyTrendChart from "@/components/charts/DailyTrendChart";
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

import NotificationBar from "@/components/ui/NotificationBar";
import NotificationDetailsModal from "@/components/NotificationDetailsModal";
import {
  bseAlertsService,
  CombinedWorkbookData,
  SpecialSheetsData,
  ExcelData
} from "@/services/bseAlertsService";
import {
  processDataForBSEData,
  transformBSEDataForExcelView,
  filterDataByLatestMonth,
  parseDate,
  getMonthYearFromFirstRow
} from "@/utils/bseDataUtils";



const Dashboard = () => {
  // Add scroll to top effect
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  const [selectedRecord, setSelectedRecord] = useState<any | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [workbookData, setWorkbookData] = useState<CombinedWorkbookData | null>(null);
  const [filteredWorkbookData, setFilteredWorkbookData] = useState<CombinedWorkbookData | null>(null);
  const [specialSheetsData, setSpecialSheetsData] = useState<SpecialSheetsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [chartData, setChartData] = useState<any>(null);
  const [useCache, setUseCache] = useState<boolean>(true);
  const [bseAlertsData, setBseAlertsData] = useState<any[] | null>(null); // New state for BSE alerts data
  const [dateRange, setDateRange] = useState<{ from: Date | undefined; to: Date | undefined }>({
    from: undefined,
    to: undefined
  });
  const [isCalendarOpen, setIsCalendarOpen] = useState<boolean>(false);

  // Memoized data filtering function
  const filterData = useCallback((data: ExcelData[]) => {
    return data.filter(row => {
      // Check if any column has non-empty data
      const hasValidData = Object.values(row).some(value => {
        if (value === null || value === undefined) return false;
        const stringValue = String(value).trim();
        return stringValue !== '' && stringValue !== 'null' && stringValue !== 'undefined';
      });

      // Filter out rows where "Name of Entity" is "Total"
      const entityName = String(row["Name of Entity"] || "").trim();
      const isTotalEntity = entityName.toUpperCase() === "TOTAL";

      // Exclude rows where "Summary of Intimation" is "NIL"
      const summaryValue = String(row["Summary of Intimation"] || "").trim().toUpperCase();
      const isSummaryNil = summaryValue === "NIL" || summaryValue === "NILL" || summaryValue === "NULL";

      // Return true only if row has valid data, entity is not "Total", and summary is not NIL
      return hasValidData && !isTotalEntity && !isSummaryNil;
    });
  }, []);

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
    if (!workbookData) return;

    if (!dateRange.from && !dateRange.to) {
      // When no date range is selected, filter Excel view to show only the latest month
      // But keep the original total count
      const latestMonthData = filterDataByLatestMonth(workbookData.combined_data);
      const newWorkbookData = {
        ...workbookData,
        combined_data: latestMonthData
        // Keep the original count (total count from API response)
      };
      setFilteredWorkbookData(newWorkbookData);
      return;
    }

    const filtered = workbookData.combined_data.filter(row => {
      const dateValue = row["Date"];
      if (!dateValue) return true;


      try {
        const rowDate = parseDate(dateValue);
        if (!rowDate) return true;

        const fromValid = !dateRange.from || rowDate >= dateRange.from;
        const toValid = !dateRange.to || rowDate <= dateRange.to;

        return fromValid && toValid;
      } catch (e) {
        console.error("Error parsing date:", dateValue, e);
        return true;
      }
    });

    // Create new workbook data with filtered data
    const newWorkbookData = {
      ...workbookData,
      combined_data: filtered,
      count: filtered.length
    };

    setFilteredWorkbookData(newWorkbookData);
  }, [workbookData, dateRange]);

  // Handle refresh with optimizations
  const handleRefresh = useCallback(async (): Promise<void> => {
    try {
      setLoading(true);
      setError(null);

      // Fetch BSE alerts data from the new endpoint
      const bseDataResponse = await bseAlertsService.fetchBSEAlertsData(10000, 0); // Fetch all valid records (there are 835)
      const bseData = bseDataResponse.data;
      const totalNotificationsCount = bseDataResponse.count; // Get total count from API response

      // Process data for charts (using all data for charts)
      const processedChartData = processDataForBSEData(bseData);
      setChartData(processedChartData);

      // Transform data for ExcelView
      const transformedData = transformBSEDataForExcelView(bseData);

      // Apply filtering to remove invalid data
      const filteredData = filterData(transformedData);

      // Filter to show only latest month for Excel view
      const latestMonthData = filterDataByLatestMonth(filteredData);

      // Create mock workbook data structure for ExcelView
      const mockWorkbookData: CombinedWorkbookData = {
        file_name: "bse_alerts.db",
        sheets: ["DailyLogs"],
        combined_data: latestMonthData, // Only latest month for Excel view
        count: totalNotificationsCount, // Total count from API response
        special_sheets_excluded: []
      };

      setWorkbookData(mockWorkbookData);
    } catch (err) {
      console.error("Error refreshing workbook data:", err);
      setError(err instanceof Error ? err.message : "Failed to refresh workbook data");
    } finally {
      setLoading(false);
    }
  }, []);

  // Load workbook data on component mount
  useEffect(() => {
    const loadWorkbookData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch BSE alerts data from the new endpoint
        const bseDataResponse = await bseAlertsService.fetchBSEAlertsData(10000, 0); // Fetch all valid records
        const bseData = bseDataResponse.data;
        const totalNotificationsCount = bseDataResponse.count; // Get total count from API response

        // Process data for charts (using all data for charts)
        const processedChartData = processDataForBSEData(bseData);
        setChartData(processedChartData);

        // Transform data for ExcelView
        const transformedData = transformBSEDataForExcelView(bseData);

        // Apply filtering to remove invalid data
        const filteredData = filterData(transformedData);

        // Filter to show only latest month for Excel view
        const latestMonthData = filterDataByLatestMonth(filteredData);

        // Create mock workbook data structure for ExcelView
        const mockWorkbookData: CombinedWorkbookData = {
          file_name: "bse_alerts.db",
          sheets: ["DailyLogs"],
          combined_data: latestMonthData, // Only latest month for Excel view
          count: totalNotificationsCount, // Total count from API response
          special_sheets_excluded: []
        };

        setWorkbookData(mockWorkbookData);
      } catch (err) {
        console.error("Error loading workbook data:", err);
        setError(err instanceof Error ? err.message : "Failed to load workbook data");
      } finally {
        setLoading(false);
      }
    };

    loadWorkbookData();
  }, []);

  if (loading && !workbookData) {
    return (
      <BSEAlertsDashboardLayout>
        <NotificationBar />
        <div className="min-h-screen flex items-center justify-center" style={{ background: "#ffffff" }}>
          <div className="text-center">
            <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4" style={{ color: "#46798E" }} />
            <p className="text-lg" style={{ color: "#000000" }}>Loading BSE Alerts data...</p>
          </div>
        </div>
      </BSEAlertsDashboardLayout>
    );
  }

  if (error && !workbookData) {
    return (
      <BSEAlertsDashboardLayout>
        <NotificationBar />
        <div className="min-h-screen flex items-center justify-center" style={{ background: "#ffffff" }}>
          <div className="text-center p-6 max-w-md">
            <AlertCircle className="h-12 w-12 mx-auto mb-4" style={{ color: "#EF4444" }} />
            <h2 className="text-xl font-bold mb-2" style={{ color: "#000000" }}>Error Loading BSE Alerts Data</h2>
            <p className="mb-4" style={{ color: "#000000" }}>{error}</p>
            <Button
              onClick={handleRefresh}
              style={{
                backgroundColor: '#46798E',
                borderColor: '#46798E',
                color: 'white'
              }}
            >
              Retry
            </Button>
          </div>
        </div>
      </BSEAlertsDashboardLayout>
    );
  }

  return (
    <BSEAlertsDashboardLayout>
      {/* Notification Bar at top of page */}
      <NotificationBar />

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
                  <Activity className="h-8 w-8" style={{ color: "#46798E" }} />
                  <CardTitle className="text-2xl sm:text-3xl lg:text-4xl font-bold" style={{ color: "#000000" }}>
                    BSE DASHBOARD
                  </CardTitle>
                </div>
                <CardDescription className="text-lg" style={{ color: '#000000' }}>
                  Real-time monitoring and analytics for Bombay Stock Exchange notifications
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
                    <Bell className="h-5 w-5" style={{ color: "#46798E" }} />
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
                    <div className="text-4xl font-bold font-mono mb-2" style={{ color: '#46798E' }}>
                      {specialSheetsData ? 785 : workbookData?.count || 0}
                    </div>
                    <div className="text-sm font-mono" style={{ color: 'rgba(1, 7, 65, 0.8)' }}>
                      Till Date
                    </div>
                    <div className="flex items-center justify-center gap-1 mt-2">
                      <TrendingUp size={14} style={{ color: '#46798E' }} />
                      <span className="text-xs font-mono" style={{ color: '#7E659E' }}>LIVE MONITORING</span>
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
              <DailyTrendChart data={chartData?.daily || []} />
            </motion.div>

            {/* Monthly Trend Chart - Bottom Left */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1.2, delay: 0.9 }}
              className="lg:col-span-1 h-[250px]"
            >
              <MonthlyTrendChart data={chartData?.monthly || []} />
            </motion.div>

            {/* Weekly Trend Chart (now with pie chart) - Bottom Right */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1.2, delay: 1.2 }}
              className="lg:col-span-1 h-[250px]"
            >
              <WeeklyTrendChart data={chartData?.weekly || []} />
            </motion.div>
          </div>

          {/* Excel View Section with proper spacing */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1.2, delay: 1.8 }}
            className="mt-8"
          >
            {filteredWorkbookData ? (
              <ExcelView
                initialData={filteredWorkbookData.combined_data}
                columns={["Name of Entity", "Link to Intimation", "Nature of Intimation", "Summary of Intimation", "Date"]}
                title={`${getMonthYearFromFirstRow(filteredWorkbookData.combined_data)} Notifications`}
                onViewRow={(row, rowIndex) => {
                  handleViewNotification(row);
                }}
                initializeWithEmptyRows={false}
                columnWidths={{
                  "Date": "120px",
                  "Link to Intimation": "150px",
                  "Name of Entity": "minmax(150px, 1fr)",
                  "Nature of Intimation": "minmax(150px, 1fr)",
                  "Summary of Intimation": "minmax(200px, 2fr)"
                }}
                enableDateRangeFilter={true}
                onDateRangeChange={handleDateRangeSelect}
                initialDateRange={dateRange}
              />
            ) : (
              <ExcelView
                initialData={[]}
                columns={["Name of Entity", "Link to Intimation", "Nature of Intimation", "Summary of Intimation", "Date"]}
                title={`${getMonthYearFromFirstRow([])} Notifications`}
                onViewRow={(row, rowIndex) => {
                  handleViewNotification(row);
                }}
                initializeWithEmptyRows={false}
                columnWidths={{
                  "Date": "120px",
                  "Link to Intimation": "150px",
                  "Name of Entity": "minmax(150px, 1fr)",
                  "Nature of Intimation": "minmax(150px, 1fr)",
                  "Summary of Intimation": "minmax(200px, 2fr)"
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
    </BSEAlertsDashboardLayout>
  );
};

export default Dashboard;
