import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Activity, Bell, TrendingUp, FileText, Loader2, AlertCircle, Calendar as CalendarIcon, X } from "lucide-react";
import RBIAnalysisDashboardLayout from "@/components/layout/RBIAnalysisDashboardLayout";
import MonthlyTrendChart from "@/components/charts/MonthlyTrendChart";
import WeeklyTrendChart from "@/components/charts/WeeklyTrendChart";
import DailyTrendChart from "@/components/charts/DailyTrendChart";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import ExcelView from "../components/ui/ExcelView";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { format } from "date-fns";

// Define types for RBI data
interface RBIMasterSummary {
  id: number;
  date_key: string;  // Add this property
  run_date: string;
  pdf_link: string;
  summary: string;
  inserted_at: string;  // Add this property
}

// Fetch RBI data from the new database endpoint
const fetchRBIData = async (limit: number = 100, offset: number = 0): Promise<any> => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout

  // Use explicit path since frontend and backend might be served from different ports
  const API_BASE_URL = '/api';

  try {
    const response = await fetch(`${API_BASE_URL}/rbi-analysis-data?limit=${limit}&offset=${offset}`, {
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      // Try to get error message from response body
      let errorMessage = `Failed to fetch RBI data: ${response.status} ${response.statusText}`;
      try {
        const errorText = await response.text();
        if (errorText) {
          errorMessage = errorText;
        }
      } catch (e) {
        // If we can't parse the error text, use the default message
      }
      throw new Error(errorMessage);
    }

    // Check if response is JSON
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      throw new Error('Received non-JSON response from server');
    }

    return response.json();
  } catch (error: any) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('Request timeout - server is taking too long to respond (15 seconds elapsed)');
    }
    throw error;
  }
};

// Helper to parse DD-MM-YYYY string safely
const parseDateString = (dateStr: string): Date | null => {
  if (!dateStr) return null;
  try {
    // Handle DD-MM-YYYY format
    if (/^\d{1,2}-\d{1,2}-\d{4}$/.test(dateStr)) {
      const [day, month, year] = dateStr.split('-').map(Number);
      return new Date(year, month - 1, day);
    }
    // Handle YYYY-MM-DD format
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
      const [year, month, day] = dateStr.split('-').map(Number);
      return new Date(year, month - 1, day);
    }
    const d = new Date(dateStr);
    return isNaN(d.getTime()) ? null : d;
  } catch (e) {
    return null;
  }
};

// Process data for charts (updated to work with RBI data)
const processDataForRBIData = (data: any[]) => {
  // Sort all data by date once to find latest range
  const sortedRawData = [...data].map(item => ({
    ...item,
    parsedDate: parseDateString(item.date_key || item.Date || "")
  })).filter(item => item.parsedDate !== null).sort((a, b) => b.parsedDate!.getTime() - a.parsedDate!.getTime());

  // Group data by date for daily trend
  const dailyMap: { [key: string]: number } = {};

  // Decide which month to use for Daily/Weekly views
  // Default to current month, but if empty, use the latest month with data
  const now = new Date();
  let targetMonth = now.getMonth();
  let targetYear = now.getFullYear();

  const currentMonthDataRaw = data.filter(item => {
    const d = parseDateString(item.date_key || item.Date || "");
    return d && d.getMonth() === targetMonth && d.getFullYear() === targetYear;
  });

  if (currentMonthDataRaw.length === 0 && sortedRawData.length > 0) {
    targetMonth = sortedRawData[0].parsedDate!.getMonth();
    targetYear = sortedRawData[0].parsedDate!.getFullYear();
  }

  const chartMonthData = data.filter(item => {
    const d = parseDateString(item.date_key || item.Date || "");
    return d && d.getMonth() === targetMonth && d.getFullYear() === targetYear;
  });

  // Process data for daily trend (using selected month)
  chartMonthData.forEach(item => {
    const d = parseDateString(item.date_key || item.Date || "");
    if (d) {
      const formattedDate = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
      dailyMap[formattedDate] = (dailyMap[formattedDate] || 0) + 1;
    }
  });

  const dailyChartData = Object.keys(dailyMap).map(date => ({
    date,
    total_notifications: dailyMap[date]
  })).sort((a, b) => a.date.localeCompare(b.date));

  // Monthly processing (all time)
  const monthlyMap: { [key: string]: number } = {};
  const monthYearSet = new Set<string>();

  data.forEach(item => {
    const d = parseDateString(item.date_key || item.Date || "");
    if (d) {
      const month = d.getMonth() + 1;
      const year = d.getFullYear();
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      const key = `${monthNames[month - 1]}-${year}`;

      monthYearSet.add(key);
      monthlyMap[key] = (monthlyMap[key] || 0) + 1;
    }
  });

  // Ensure 2026 is visible if we want 2026 analysis
  let minYear = 2025;
  let maxYear = 2026;

  if (data.length > 0) {
    const years = Array.from(monthYearSet).map(k => parseInt(k.split('-')[1]));
    minYear = Math.min(minYear, ...years);
    maxYear = Math.max(maxYear, ...years);
  }

  const completeSortedMonthYears: string[] = [];
  for (let y = minYear; y <= maxYear; y++) {
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    monthNames.forEach(m => completeSortedMonthYears.push(`${m}-${y}`));
  }

  const monthlyChartData = completeSortedMonthYears.map(key => {
    const [month, year] = key.split('-');
    return {
      month,
      year,
      total_notifications: monthlyMap[key] || 0,
      entity_name: "RBI"
    };
  });

  // Weekly processing (using same target month)
  const weeklyMap: { [key: string]: number } = {};
  chartMonthData.forEach(item => {
    const d = parseDateString(item.date_key || item.Date || "");
    if (d) {
      const dayOfMonth = d.getDate();
      const weekNumber = Math.ceil(dayOfMonth / 7);
      const key = `Week ${weekNumber}`;
      weeklyMap[key] = (weeklyMap[key] || 0) + 1;
    }
  });

  const weeklyTimeData = [1, 2, 3, 4, 5].map(weekNum => {
    const key = `Week ${weekNum}`;
    return {
      week: key,
      total_notifications: weeklyMap[key] || 0
    };
  });

  return {
    daily: dailyChartData,
    monthly: monthlyChartData,
    weekly: weeklyTimeData,
    targetMonthText: `${['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][targetMonth]} ${targetYear}`
  };
};


// Transform RBI data to match ExcelView format
const transformRBIDataForExcelView = (data: RBIMasterSummary[]) => {
  // Sort data by date in descending order (newest first)
  const sortedData = [...data].sort((a, b) => {
    if (!a.date_key || !b.date_key) return 0;

    try {
      // Parse DD-MM-YYYY format
      const [dayA, monthA, yearA] = a.date_key.split('-').map(Number);
      const [dayB, monthB, yearB] = b.date_key.split('-').map(Number);

      // Create Date objects
      const dateA = new Date(yearA, monthA - 1, dayA);
      const dateB = new Date(yearB, monthB - 1, dayB);

      // Sort in descending order (newest first)
      return dateB.getTime() - dateA.getTime();
    } catch (e) {
      console.error("Error parsing dates for sorting:", a.date_key, b.date_key, e);
      return 0;
    }
  });

  return sortedData
    .filter(item => !(item.pdf_link === 'NIL' && item.summary === 'NIL')) // Only filter out records where both are NIL
    .map(item => ({
      "Date": item.date_key,  // Use date_key instead of run_date
      "PDF Link": item.pdf_link,
      "Summary": item.summary
    }));
};

// Get month and year from the first row's date value
const getMonthYearFromFirstRow = (data: any[]) => {
  if (!data || data.length === 0) {
    // Fallback to current month/year if no data
    const monthNames = [
      "January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"
    ];
    const now = new Date();
    return `${monthNames[now.getMonth()]} ${now.getFullYear()}`;
  }

  // Get the first row's date
  const firstRow = data[0];
  let dateStr = firstRow["Date"];

  // Try other possible date column names if "Date" doesn't exist
  if (!dateStr) {
    const possibleDateColumns = ["Date", "date", "date_key", "Date Key", "Run Date", "Run_Date"];
    for (const col of possibleDateColumns) {
      if (firstRow[col]) {
        dateStr = firstRow[col];
        break;
      }
    }
  }

  if (!dateStr) {
    // Fallback to current month/year if no date
    const monthNames = [
      "January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"
    ];
    const now = new Date();
    return `${monthNames[now.getMonth()]} ${now.getFullYear()}`;
  }

  try {
    // Handle different date formats
    let dateObj: Date | null = null;

    // If it's already a Date object or timestamp
    if (dateStr instanceof Date) {
      dateObj = dateStr;
    }
    // If it's a timestamp number
    else if (typeof dateStr === 'number') {
      dateObj = new Date(dateStr);
    }
    // If it's a string
    else if (typeof dateStr === 'string') {
      // Try parsing as ISO date string (YYYY-MM-DD)
      if (dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
        dateObj = new Date(dateStr);
      }
      // Try parsing as DD-MM-YYYY format
      else if (dateStr.match(/^\d{1,2}-\d{1,2}-\d{4}$/)) {
        const parts = dateStr.split('-');
        if (parts.length === 3) {
          const day = parseInt(parts[0], 10);
          const month = parseInt(parts[1], 10) - 1; // JS months are 0-indexed
          const year = parseInt(parts[2], 10);
          dateObj = new Date(year, month, day);
        }
      }
      // Try parsing as MM/DD/YYYY format
      else if (dateStr.match(/^\d{1,2}\/\d{1,2}\/\d{4}$/)) {
        const parts = dateStr.split('/');
        if (parts.length === 3) {
          const month = parseInt(parts[0], 10) - 1; // JS months are 0-indexed
          const day = parseInt(parts[1], 10);
          const year = parseInt(parts[2], 10);
          dateObj = new Date(year, month, day);
        }
      }
      // Try parsing as YYYY/MM/DD format
      else if (dateStr.match(/^\d{4}\/\d{1,2}\/\d{1,2}$/)) {
        const parts = dateStr.split('/');
        if (parts.length === 3) {
          const year = parseInt(parts[0], 10);
          const month = parseInt(parts[1], 10) - 1; // JS months are 0-indexed
          const day = parseInt(parts[2], 10);
          dateObj = new Date(year, month, day);
        }
      }
      // If all else fails, try to parse with Date constructor
      else {
        dateObj = new Date(dateStr);
      }
    }

    // Check if we have a valid date
    if (dateObj && !isNaN(dateObj.getTime())) {
      const monthNames = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
      ];
      return `${monthNames[dateObj.getMonth()]} ${dateObj.getFullYear()}`;
    }
  } catch (e) {
    console.error("Error parsing date:", dateStr, e);
  }

  // Fallback to current month/year if parsing fails
  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];
  const now = new Date();
  return `${monthNames[now.getMonth()]} ${now.getFullYear()}`;
};

const RBIDashboard = () => {
  // Add scroll to top effect
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  const [selectedRecord, setSelectedRecord] = useState<any | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [rbiData, setRBIData] = useState<any[] | null>(null);
  const [filteredRbiData, setFilteredRbiData] = useState<any[] | null>(null);
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
    if (!rbiData) return;

    let filtered = rbiData;
    if (dateRange.from || dateRange.to) {
      filtered = rbiData.filter(row => {
        const dateValue = row["Date"];
        if (!dateValue) return true;

        const rowDate = parseDateString(String(dateValue));
        if (!rowDate) return true;

        const fromValid = !dateRange.from || rowDate >= dateRange.from;
        const toValid = !dateRange.to || rowDate <= dateRange.to;

        return fromValid && toValid;
      });
    }

    setFilteredRbiData(filtered);

    // Update chart data with filtered data
    // ALWAYS update chart data, even if it uses the same rbiData, to ensure consistency
    const processedChartData = processDataForRBIData(filtered);
    setChartData(processedChartData);
  }, [rbiData, dateRange]);


  // Load RBI data on component mount
  useEffect(() => {
    const loadRBIData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch RBI data from the new endpoint
        const rbiDataResponse = await fetchRBIData(10000, 0); // Fetch all valid records
        const rbiData = rbiDataResponse.data;

        // Filter out records where both pdf_link and summary are NIL
        const filteredData = rbiData.filter((item: RBIMasterSummary) =>
          !(item.pdf_link === 'NIL' && item.summary === 'NIL')
        );

        // Process data for charts
        const processedChartData = processDataForRBIData(filteredData);
        setChartData(processedChartData);

        // Transform data for ExcelView
        const transformedData = transformRBIDataForExcelView(filteredData);

        setRBIData(transformedData);
      } catch (err) {
        console.error("Error loading RBI data:", err);
        setError(err instanceof Error ? err.message : "Failed to load RBI data");
      } finally {
        setLoading(false);
      }
    };

    loadRBIData();
  }, []);

  if (loading && !rbiData) {
    return (
      <RBIAnalysisDashboardLayout>
        <div className="min-h-screen flex items-center justify-center" style={{ background: "#ffffff" }}>
          <div className="text-center">
            <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4" style={{ color: "#75479C" }} />
            <p className="text-lg" style={{ color: "#000000" }}>Loading RBI Dashboard data...</p>
          </div>
        </div>
      </RBIAnalysisDashboardLayout>
    );
  }

  if (error && !rbiData) {
    return (
      <RBIAnalysisDashboardLayout>
        <div className="min-h-screen flex items-center justify-center" style={{ background: "#ffffff" }}>
          <div className="text-center p-6 max-w-md">
            <AlertCircle className="h-12 w-12 mx-auto mb-4" style={{ color: "#EF4444" }} />
            <h2 className="text-xl font-bold mb-2" style={{ color: "#000000" }}>Error Loading RBI Dashboard Data</h2>
            <p className="mb-4" style={{ color: "#000000" }}>{error}</p>
            <p className="text-sm" style={{ color: "#000000" }}>Please try again later</p>
          </div>
        </div>
      </RBIAnalysisDashboardLayout>
    );
  }

  return (
    <RBIAnalysisDashboardLayout>
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
                  <Activity className="h-8 w-8" style={{ color: "#75479C" }} />
                  <CardTitle className="text-2xl sm:text-3xl lg:text-4xl font-bold" style={{ color: "#000000" }}>
                    RBI DASHBOARD
                  </CardTitle>
                </div>
                <CardDescription className="text-lg" style={{ color: '#000000' }}>
                  Real-time monitoring and analytics for Reserve Bank of India notifications
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
                    <Bell className="h-5 w-5" style={{ color: "#75479C" }} />
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
                    <div className="text-4xl font-bold font-mono mb-2" style={{ color: '#75479C' }}>
                      {rbiData?.length || 0}
                    </div>
                    <div className="text-sm font-mono" style={{ color: 'rgba(1, 7, 65, 0.8)' }}>
                      Till Date
                    </div>
                    <div className="flex items-center justify-center gap-1 mt-2">
                      <TrendingUp size={14} style={{ color: '#75479C' }} />
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
              <DailyTrendChart
                data={chartData?.daily || []}
                title={`Daily Analysis Trend (${chartData?.targetMonthText || 'Current'})`}
              />
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

            {/* Weekly Trend Chart - Bottom Right */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1.2, delay: 1.2 }}
              className="lg:col-span-1 h-[250px]"
            >
              <WeeklyTrendChart
                data={chartData?.weekly || []}
                title={`Weekly Trend (${chartData?.targetMonthText || 'Current'})`}
              />
            </motion.div>

          </div>

          {/* Excel View Section with proper spacing */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1.2, delay: 1.8 }}
            className="mt-8"
          >
            {filteredRbiData ? (
              <ExcelView
                initialData={filteredRbiData}
                columns={['Date', 'PDF Link', 'Summary']}
                title={`${getMonthYearFromFirstRow(filteredRbiData)} Notifications`}
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
                title={`${getMonthYearFromFirstRow([])} Notifications`}
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
        </div>
      </div>

      {/* Record Details Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto w-full" style={{ background: '#ffffff' }}>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3 text-xl " style={{ color: '#000000' }}>
              <FileText className="h-6 w-6" style={{ color: '#75479C' }} />
              Notification Details
            </DialogTitle>
            <DialogDescription style={{ color: '#000000' }}>
              Detailed information for the selected notification record
            </DialogDescription>
          </DialogHeader>

          {selectedRecord && (
            <div className="space-y-6 mt-4 w-full">
              {/* Entity Information */}
              <div className="grid grid-cols-1 gap-4 w-full">
                <Card style={{ background: '#ffffff', border: '2px solid #75479C', boxShadow: '0 4px 15px rgba(117, 71, 156, 0.2)' }} className="w-full">
                  <CardHeader className="pb-3" style={{ background: '#75479C', borderRadius: '8px 8px 0 0' }}>
                    <CardTitle className="text-sm font-mono text-white">Notification Details</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <span className="text-xs font-mono font-semibold" style={{ color: '#010741' }}>Details:</span>
                      <div className="mt-2 space-y-2">
                        {Object.entries(selectedRecord).map(([key, value]) => (
                          <div key={key} className="text-sm">
                            <span className="font-medium" style={{ color: '#75479C' }}>{key}:</span>{" "}
                            <span style={{ color: '#010741' }}>{String(value)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Summary Section */}
              <Card style={{ background: '#ffffff' }} className="w-full">
                <CardHeader>
                  <CardTitle className="text-lg " style={{ color: '#75479C' }}>Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="prose prose-sm max-w-none w-full">
                    <div
                      className="text-sm leading-relaxed whitespace-pre-line p-4 rounded-lg w-full"
                      style={{
                        background: '#ffffff',
                        border: '1px solid #75479C'
                      }}
                    >
                      {selectedRecord["Summary"] || "No summary available"}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Action Buttons */}
              <div className="flex justify-between items-center pt-4 border-t w-full" >
                <div className="text-xs font-mono font-semibold" style={{ color: '#75479C' }}>
                  Record viewed at {new Date().toLocaleString()}
                </div>
                <div className="flex gap-3">
                  {selectedRecord["PDF Link"] && selectedRecord["PDF Link"] !== "NIL" && (
                    <Button
                      onClick={() => handleOpenLink(selectedRecord["PDF Link"])}
                      className="flex items-center gap-2 font-semibold"
                      style={{
                        background: 'linear-gradient(135deg, #75479C, #BD3861)',
                        borderColor: '#75479C',
                        color: 'white',
                        boxShadow: '0 3px 12px rgba(117, 71, 156, 0.3)'
                      }}
                    >
                      <FileText size={16} />
                      Open PDF
                    </Button>
                  )}
                  <Button
                    onClick={() => setIsModalOpen(false)}
                    className="font-semibold"
                    style={{
                      background: 'linear-gradient(135deg, #010741, #75479C)',
                      borderColor: '#010741',
                      color: 'white',
                      boxShadow: '0 3px 12px rgba(1, 7, 65, 0.3)'
                    }}
                  >
                    Close
                  </Button>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </RBIAnalysisDashboardLayout>
  );
};

export default RBIDashboard;