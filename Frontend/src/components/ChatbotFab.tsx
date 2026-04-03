import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { X, Maximize2, Minimize2, TrendingUp } from "lucide-react";
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { InteractiveComparisonChart } from "@/components/InteractiveComparisonChart";

type Msg = {
  role: "user" | "bot";
  text?: string;
  structured?: any;
  chart_config?: any;
  database_detected?: string;  // Which database was used
  ts: number;
};

const CHART_COLORS = ["#0B74B0", "#75479C", "#BD3861", "#10B981", "#F59E0B"];

export default function ChatbotFab() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [expanded, setExpanded] = useState(false);
  const [messages, setMessages] = useState<Msg[]>([]);  // Single message array, no channels
  const [isLoading, setIsLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  // Interactive chart state
  const [showCompanySelector, setShowCompanySelector] = useState<number | null>(null); // Track which chart
  const [availableCompanies, setAvailableCompanies] = useState<string[]>([]);
  const [selectedCompanies, setSelectedCompanies] = useState<Set<string>>(new Set());
  const [interactiveChartData, setInteractiveChartData] = useState<{ labels: string[], values: number[] } | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, open]);

  const parseSampleQuestions = (text?: string) => {
    if (!text || !text.includes("Sample questions you can ask:")) {
      return { mainText: text || "", sampleQuestions: [] as string[] };
    }

    const [mainText, sampleBlock = ""] = text.split("Sample questions you can ask:");
    const sampleQuestions = sampleBlock
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => line.replace(/^\d+\.\s*/, "").trim())
      .filter(Boolean);

    return { mainText: mainText.trim(), sampleQuestions };
  };

  // Auto-detect database from query
  const detectDatabase = (query: string): string => {
    const lowerQuery = query.toLowerCase();

    // Check for explicit database mentions
    if (lowerQuery.includes("bse") || lowerQuery.includes("stock") || lowerQuery.includes("equity")) {
      return "bse";
    }
    if (lowerQuery.includes("sebi") || lowerQuery.includes("securities") || lowerQuery.includes("regulatory")) {
      return "sebi";
    }
    if (lowerQuery.includes("rbi") || lowerQuery.includes("reserve bank") || lowerQuery.includes("monetary")) {
      return "rbi";
    }

    // Default to 'all' if not specified
    return "all";
  };

  const send = async (text?: string) => {
    const content = (text ?? input).trim();
    if (!content || isLoading) return;

    const u: Msg = { role: "user", text: content, ts: Date.now() };
    setMessages((prev) => [...prev, u]);
    setInput("");
    setIsLoading(true);

    try {
      // Auto-detect database from user query
      const detectedDb = detectDatabase(content);

      // Add loading message
      const loadingMsg: Msg = {
        role: "bot",
        text: "Analyzing your query...",
        ts: Date.now() + 1
      };
      setMessages((prev) => [...prev, loadingMsg]);

      const normalize = (s: string) =>
        (s || "")
          .replace(/Â/g, "")
          .replace(/â€¢|•/g, "-")
          .replace(/â€"|–|—/g, "-")
          .replace(/â€˜/g, "'")
          .replace(/â€™/g, "'")
          .replace(/â€œ/g, "\"")
          .replace(/â€/g, "\"")
          .replace(/â€¦/g, "…");

      const res = await fetch("/api/chat/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: content,
          session_id: "session_unified",
          database: detectedDb,  // Send detected database
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();

      // Remove loading message and add actual response
      setMessages((prev) => {
        const withoutLoading = prev.slice(0, -1);

        // Parse backend response format
        let structured = null;
        let chart_config = null;
        let responseText = "";

        // CRITICAL FIX: Backend returns table/chart data in data.structured field!
        const responseData = data.structured || data;

        // Prefer nested chart_config from ChatResponse when present.
        if (responseData.chart_config) {
          chart_config = {
            chart_type: responseData.chart_config.chart_type || "bar",
            title: responseData.chart_config.title || "Chart",
            data: responseData.chart_config.data || { labels: [], values: [] }
          };
          responseText = responseData.response || data.response || responseData.chart_config.title || "";
        }
        // Handle backend-native chart response: {response_type: "chart", chart_type: "bar", data: {...}}
        else if (responseData.response_type === "chart") {
          // Backend returns chart in this format
          chart_config = {
            chart_type: responseData.chart_type || "bar",
            title: responseData.title || "Chart",
            data: responseData.data || { labels: [], values: [] }
          };
          responseText = responseData.message || responseData.title || "";
        }
        // Handle table response: {response_type: "table", columns: [...], rows: [[...]]}
        else if (responseData.response_type === "table" && responseData.columns && responseData.rows) {
          // Convert rows array to array of objects
          structured = responseData.rows.map((row: any[]) => {
            const obj: any = {};
            responseData.columns.forEach((col: string, idx: number) => {
              obj[col] = row[idx];
            });
            return obj;
          });
          responseText = responseData.title || responseData.message || `Found ${responseData.total_count || responseData.rows.length} results`;
        }
        // Handle text response
        else {
          responseText = data.response || "";
          // Don't set structured if it's the raw table/chart object
          if (responseData.response_type !== "table" && responseData.response_type !== "chart" && !responseData.chart_config) {
            structured = Array.isArray(responseData) ? responseData : null;
          }
        }

        const botMsg: Msg = {
          role: "bot",
          text: normalize(responseText),
          structured: structured,
          chart_config: chart_config,
          database_detected: detectedDb,  // Store which DB was used
          ts: Date.now(),
        };

        return [...withoutLoading, botMsg];
      });
    } catch (error) {
      setMessages((prev) => {
        const withoutLoading = prev.slice(0, -1);
        return [
          ...withoutLoading,
          {
            role: "bot",
            text: "Sorry, an error occurred while processing your request. Please try again.",
            ts: Date.now(),
          },
        ];
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch companies for interactive chart
  const fetchCompaniesForChart = async (title: string) => {
    const monthMatch = title?.match(/\((\w+)\s+(\d{4})\)/);
    const params = new URLSearchParams();
    if (monthMatch) {
      const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'];
      const monthNum = monthNames.indexOf(monthMatch[1]) + 1;
      if (monthNum > 0) params.append('month', monthNum.toString());
      params.append('year', monthMatch[2]);
    }

    try {
      const res = await fetch(`/api/companies?${params.toString()}`);
      const data = await res.json();
      setAvailableCompanies(data.companies || []);
    } catch (err) {
      console.error('Failed to fetch companies:', err);
    }
  };

  // Toggle company selection
  const toggleCompany = async (company: string, messageIndex: number, config: any) => {
    const newSelected = new Set(selectedCompanies);

    if (newSelected.has(company)) {
      newSelected.delete(company);
    } else {
      newSelected.add(company);
    }
    setSelectedCompanies(newSelected);

    // Fetch updated chart data
    const monthMatch = config.title?.match(/\((\w+)\s+(\d{4})\)/);
    const params = new URLSearchParams();
    params.append('companies', Array.from(newSelected).join(','));

    if (monthMatch) {
      const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'];
      const monthNum = monthNames.indexOf(monthMatch[1]) + 1;
      if (monthNum > 0) params.append('month', monthNum.toString());
      params.append('year', monthMatch[2]);
    }

    try {
      const res = await fetch(`/api/compare?${params.toString()}`);
      const data = await res.json();

      // Update the message with new chart data
      setMessages(prev => prev.map((msg, idx) => {
        if (idx === messageIndex && msg.chart_config) {
          return {
            ...msg,
            chart_config: {
              ...msg.chart_config,
              data: {
                labels: data.labels,
                values: data.values
              }
            }
          };
        }
        return msg;
      }));
    } catch (err) {
      console.error('Failed to update chart:', err);
    }
  };

  // Render chart function
  const renderChart = (config: any, messageIndex: number) => {
    if (!config || !config.data) return null;

    const chartData = config.data.labels?.map((label: string, idx: number) => ({
      name: label,
      value: config.data.values?.[idx] || 0,
    })) || [];

    // Check if this is a comparison chart
    const isComparison = config.title?.toLowerCase().includes('comparison');
    const isThisChartOpen = showCompanySelector === messageIndex;

    if (isComparison && config.chart_type === "bar") {
      const monthMatch = config.title?.match(/\((\w+)\s+(\d{4})\)/);
      const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'];
      const month = monthMatch ? monthNames.indexOf(monthMatch[1]) + 1 : undefined;
      const year = monthMatch ? Number(monthMatch[2]) : undefined;

      return (
        <InteractiveComparisonChart
          initialData={{
            labels: config.data.labels || [],
            values: config.data.values || [],
          }}
          title={config.title || "Notification Comparison"}
          month={month && month > 0 ? month : undefined}
          year={year}
        />
      );
    }

    return (
      <div className="w-full min-w-[600px] mt-3 bg-white p-4 rounded-lg border">
        <div className="flex justify-between items-center mb-3">
          <div className="text-sm font-semibold">{config.title || "Chart"}</div>
          {isComparison && (
            <button
              onClick={() => {
                if (isThisChartOpen) {
                  setShowCompanySelector(null);
                } else {
                  setShowCompanySelector(messageIndex);
                  setSelectedCompanies(new Set(config.data.labels || []));
                  fetchCompaniesForChart(config.title);
                }
              }}
              className="text-xs px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 transition"
            >
              {isThisChartOpen ? 'Hide' : 'Add/Remove Companies'}
            </button>
          )}
        </div>

        {isThisChartOpen && isComparison && (
          <div className="mb-4 p-3 bg-gray-50 rounded border max-h-40 overflow-y-auto">
            <div className="text-xs font-semibold mb-2">Select Companies:</div>
            <div className="grid grid-cols-2 gap-2">
              {availableCompanies.map(company => (
                <label key={company} className="flex items-center text-xs cursor-pointer hover:bg-gray-100 p-1 rounded">
                  <input
                    type="checkbox"
                    checked={selectedCompanies.has(company)}
                    onChange={() => toggleCompany(company, messageIndex, config)}
                    className="mr-2"
                  />
                  <span className="truncate" title={company}>{company}</span>
                </label>
              ))}
            </div>
          </div>
        )}

        <ResponsiveContainer width="100%" height={350}>
          {config.chart_type === "line" ? (
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 11 }}
                angle={-25}
                textAnchor="end"
                height={80}
                interval={0}
              />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #ccc', borderRadius: '4px' }} />
              <Line type="monotone" dataKey="value" stroke={CHART_COLORS[0]} strokeWidth={2} dot={{ fill: CHART_COLORS[0], r: 4 }} />
            </LineChart>
          ) : config.chart_type === "bar" ? (
            chartData.length === 0 ? (
              <div className="h-[320px] flex items-center justify-center rounded-lg border border-dashed border-slate-300 bg-slate-50 text-sm text-slate-500">
                No chart data available.
              </div>
            ) : (
              <BarChart data={chartData} margin={{ top: 5, right: 20, bottom: 60, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 11 }}
                  angle={-25}
                  textAnchor="end"
                  height={80}
                  interval={0}
                />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: 'white', border: '1px solid #ccc', borderRadius: '4px' }}
                  formatter={(value: any) => [`${value} notifications`, 'Count']}
                />
                <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                  {chartData.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            )
          ) : config.chart_type === "pie" ? (
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #ccc', borderRadius: '4px' }} />
            </PieChart>
          ) : null}
        </ResponsiveContainer>
      </div>
    );
  };

  return (
    <>
      {/* FAB */}
      <div className="fixed bottom-6 right-20 z-50 flex items-center gap-3">
        <button
          onClick={() => setOpen(true)}
          className="relative w-28 h-28 rounded-full shadow-lg flex items-center justify-center hover:scale-105 transition-transform"
          style={{
            background:
              "linear-gradient(#ffffff, #ffffff) padding-box, linear-gradient(135deg, #0B74B0, #75479C, #BD3861) border-box",
            border: "2px solid transparent",
          }}
        >
          <Avatar className="h-24 w-24">
            <AvatarImage src="/avatar.jpg" />
            <AvatarFallback>AI</AvatarFallback>
          </Avatar>
        </button>
      </div>

      {/* CHAT WINDOW */}
      {open && (
        <div className="fixed inset-0 z-50">
          <div className="absolute inset-0 bg-black/20" onClick={() => setOpen(false)} />
          <div className={expanded ? "absolute inset-4" : "absolute bottom-6 right-6 w-[480px]"}>
            <Card className="h-full rounded-2xl overflow-hidden border-2" style={{ borderColor: "#0B74B0" }}>
              <CardHeader className="relative h-20 bg-gradient-to-r from-[#0B74B0] via-[#4A5FA8] to-[#75479C] text-white shadow-lg">
                <div className="flex items-center justify-between h-full px-2">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center">
                      <TrendingUp size={24} className="text-white" />
                    </div>
                    <div>
                      <h3 className="font-bold text-xl tracking-wide">AEGIS Intelligence</h3>
                      <p className="text-xs opacity-95 font-medium">Regulatory Insights & Market Analytics</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setExpanded(!expanded)}
                      className="p-2 hover:bg-white/20 rounded-lg transition-all duration-200"
                      title={expanded ? "Minimize" : "Maximize"}
                    >
                      {expanded ? <Minimize2 size={20} /> : <Maximize2 size={20} />}
                    </button>
                    <button
                      onClick={() => setOpen(false)}
                      className="p-2 hover:bg-white/20 rounded-lg transition-all duration-200"
                      title="Close"
                    >
                      <X size={20} />
                    </button>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="pt-4 h-[calc(100%-5rem)] flex flex-col overflow-hidden">
                {/* Messages Area - FIXED: Added proper overflow scrolling */}
                <div
                  className="flex-1 overflow-y-auto overflow-x-hidden border rounded-lg p-3 mb-3 scroll-smooth"
                  style={{ background: "#f7fafc", maxHeight: expanded ? "calc(100vh - 200px)" : "400px" }}
                >
                  {messages.length === 0 && (
                    <div className="text-center text-gray-500 text-sm mt-8">
                      <div className="mb-4">
                        <TrendingUp size={48} className="mx-auto text-[#0B74B0] opacity-50" />
                      </div>
                      <p className="font-semibold mb-2">Welcome to AEGIS AI Assistant</p>
                      <p className="text-xs mb-4">I'll automatically detect which database to query</p>
                      <div className="text-left space-y-2">
                        <p className="text-xs font-semibold">Try asking:</p>
                        <button
                          onClick={() => send("Show me Adani Green notifications")}
                          className="block w-full text-left px-3 py-2 bg-white rounded hover:bg-gray-100 text-xs"
                        >
                          "Show me Adani Green notifications"
                        </button>
                        <button
                          onClick={() => send("What are the latest SEBI updates?")}
                          className="block w-full text-left px-3 py-2 bg-white rounded hover:bg-gray-100 text-xs"
                        >
                          "What are the latest SEBI updates?"
                        </button>
                        <button
                          onClick={() => send("Show RBI policy updates")}
                          className="block w-full text-left px-3 py-2 bg-white rounded hover:bg-gray-100 text-xs"
                        >
                          "Show RBI policy updates"
                        </button>
                      </div>
                    </div>
                  )}

                  {messages.map((m, i) => (
                    <div key={i} className={`mb-3 flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                      <div className={`${m.chart_config ? 'max-w-[95%]' : 'max-w-[85%]'} rounded-xl px-4 py-3 ${m.role === "user"
                        ? "bg-gradient-to-r from-[#0B74B0] to-[#75479C] text-white"
                        : "bg-white border shadow-sm"
                        }`}>
                        {(() => {
                          const { mainText, sampleQuestions } = parseSampleQuestions(m.text);

                          return (
                            <>
                              {/* Database Detection Badge */}
                              {m.role === "bot" && m.database_detected && m.database_detected !== "all" && (
                                <div className="text-xs mb-2 inline-block px-2 py-1 rounded bg-blue-100 text-blue-700 font-semibold">
                                  📊 {m.database_detected.toUpperCase()} Data
                                </div>
                              )}

                              {/* Text Content - Don't show if chart is present (to avoid duplicate title) */}
                              {mainText && !m.chart_config && (
                                <div className="text-sm whitespace-pre-wrap">{mainText}</div>
                              )}

                              {/* Clickable sample questions for unrelated-query fallback */}
                              {m.role === "bot" && sampleQuestions.length > 0 && !m.chart_config && (
                                <div className="mt-3 space-y-2">
                                  <div className="text-xs font-semibold text-slate-600">Sample questions you can ask:</div>
                                  <div className="flex flex-wrap gap-2">
                                    {sampleQuestions.map((question) => (
                                      <button
                                        key={question}
                                        onClick={() => send(question)}
                                        disabled={isLoading}
                                        className="rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-left text-xs text-slate-700 transition hover:border-[#0B74B0] hover:bg-blue-50 hover:text-[#0B74B0] disabled:cursor-not-allowed disabled:opacity-60"
                                      >
                                        {question}
                                      </button>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Table Content */}
                              {m.structured && Array.isArray(m.structured) && (
                                (() => {
                                  const rows = m.structured;
                                  const cols = Object.keys(rows[0] || {});

                                  return (
                                    <div className="overflow-auto max-h-[320px] mt-2">
                                      <table className="min-w-full text-xs border-collapse">
                                        <thead className="sticky top-0 bg-gray-100">
                                          <tr>
                                            {cols.map((c) => (
                                              <th key={c} className="px-2 py-2 border text-left font-semibold">
                                                {c}
                                              </th>
                                            ))}
                                          </tr>
                                        </thead>
                                        <tbody>
                                          {rows.map((r: any, idx: number) => (
                                            <tr key={idx} className={idx % 2 ? "bg-gray-50" : ""}>
                                              {cols.map((c) => (
                                                <td key={c} className="px-2 py-2 border whitespace-pre-wrap">
                                                  {String(r[c] ?? "")}
                                                </td>
                                              ))}
                                            </tr>
                                          ))}
                                        </tbody>
                                      </table>
                                    </div>
                                  );
                                })()
                              )}

                              {/* Chart Content */}
                              {m.chart_config && renderChart(m.chart_config, i)}
                            </>
                          );
                        })()}
                      </div>
                    </div>
                  ))}
                  <div ref={endRef} />
                </div>

                {/* Input Area */}
                <div className="flex gap-2">
                  <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
                    placeholder="Ask about BSE, SEBI, or RBI data..."
                    disabled={isLoading}
                    className="flex-1"
                  />
                  <Button
                    onClick={() => send()}
                    disabled={isLoading || !input.trim()}
                    className="bg-gradient-to-r from-[#0B74B0] to-[#75479C]"
                  >
                    {isLoading ? "..." : "Send"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </>
  );
}
