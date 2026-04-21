import { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, 
  Legend, ResponsiveContainer, AreaChart, Area, PieChart as RechartsPieChart, Pie as RechartsPie, Cell as RechartsCell
} from "recharts";
import * as Highcharts from 'highcharts';
import HighchartsReact from 'highcharts-react-official';
import drilldown from 'highcharts/modules/drilldown';
import { 
  FileText, Loader2, AlertCircle, Users, Building2, Network, TrendingUp, 
  Lightbulb, Shield, Globe, Cpu, ArrowUpRight, Briefcase 
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

// Initialize Highcharts modules
if (typeof Highcharts === 'object') {
  // Resilient module initialization for Vite/Production builds
  if (typeof drilldown === 'function') {
    (drilldown as any)(Highcharts);
  } else if (drilldown && typeof (drilldown as any).default === 'function') {
    (drilldown as any).default(Highcharts);
  }
  
  // Custom fan animation for pie charts as requested
  (function (H: any) {
    if (H && H.seriesTypes && H.seriesTypes.pie) {
      H.seriesTypes.pie.prototype.animate = function (init: boolean) {
          const series = this,
              chart = series.chart,
              points = series.points,
              { animation } = series.options,
              { startAngleRad } = series;

          function fanAnimate(point: any, startAngleRad: number) {
              const graphic = point.graphic,
                  args = point.shapeArgs;

              if (graphic && args) {
                  graphic
                      .attr({
                          start: startAngleRad,
                          end: startAngleRad,
                          opacity: 1
                      })
                      .animate({
                          start: args.start,
                          end: args.end
                      }, {
                          duration: ((animation as any).duration || 1000) / points.length
                      }, function () {
                          if (points[point.index + 1]) {
                              fanAnimate(points[point.index + 1], args.end);
                          }
                          if (point.index === series.points.length - 1) {
                              if (series.dataLabelsGroup) {
                                series.dataLabelsGroup.animate({ opacity: 1 }, undefined, function () {
                                  points.forEach((point: any) => { point.opacity = 1; });
                                  series.update({ enableMouseTracking: true }, false);
                                  chart.update({
                                      plotOptions: {
                                          pie: {
                                              innerSize: '65%',
                                              borderRadius: 12
                                          }
                                      }
                                  });
                                });
                              }
                          }
                      });
              }
          }

          if (init) {
              points.forEach((point: any) => { point.opacity = 0; });
          } else {
              fanAnimate(points[0], startAngleRad);
          }
      };
    }
  })(Highcharts);
}
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

// Define TypeScript interfaces for our data
interface Director {
  din: string;
  name: string;
  source_file: string;
}

interface CompanyCount {
  total: number;
  public: number;
  private: number;
}

interface CrossDirectorship {
  name: string;
  din: string;
  company_count: number;
}

interface Association {
  cin: string;
  company_name: string;
  designation: string;
  appointment_date: string;
}

interface Clustering {
  director1: string;
  director2: string;
  sharedCompanies: number;
}

interface NetworkNode {
  id: string;
  type: string;
  label: string;
}

interface NetworkLink {
  source: string;
  target: string;
}

interface NetworkData {
  nodes: NetworkNode[];
  links: NetworkLink[];
}

interface WTDCount {
  name: string;
  positions: number;
}

interface AnalyticsData {
  total_disclosures: number;
  by_type: Array<{ type: string; count: number }>;
  by_month: Array<{ month: string; count: number }>;
  by_director: Array<{ director: string; count: number }>;
}

const DirectorsDisclosureAnalytics = () => {
  const toTitleCase = (str: string = "") => {
    return str.toLowerCase().split(' ').map(word => {
      return word.charAt(0).toUpperCase() + word.slice(1);
    }).join(' ');
  };

  const [activeView, setActiveView] = useState('overview');
  const [directors, setDirectors] = useState<Director[]>([]);
  const [companyCount, setCompanyCount] = useState<CompanyCount | null>(null);
  const [crossDirectorship, setCrossDirectorship] = useState<CrossDirectorship[]>([]);
  const [clustering, setClustering] = useState<Clustering[]>([]);
  const [network, setNetwork] = useState<NetworkData | null>(null);
  const [wtdCount, setWtdCount] = useState<WTDCount[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [registrySummary, setRegistrySummary] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Derived KPI Stats from Live Data
  const kycData = useMemo(() => {
    if (!registrySummary?.kyc) return [
      { name: 'Completed', value: 0, color: '#10B981' },
      { name: 'Pending', value: 0, color: '#F59E0B' },
    ];
    
    const grouped = registrySummary.kyc.reduce((acc: any, item: any) => {
      const isCompleted = ['COMPLIANT', 'YES', 'APPROVED', 'DONE'].includes((item.status || "").toUpperCase());
      const bucket = isCompleted ? 'Completed' : 'Pending';
      acc[bucket] = (acc[bucket] || 0) + item.count;
      return acc;
    }, { Completed: 0, Pending: 0 });

    return [
      { name: 'Completed', value: grouped.Completed, color: '#10B981' },
      { name: 'Pending', value: grouped.Pending, color: '#F59E0B' }
    ];
  }, [registrySummary]);

  const freshnessData = useMemo(() => {
    if (!analytics?.by_month) return [];
    // Transform month data for velocity matrix
    return analytics.by_month.slice(-7).map(item => ({
      day: item.month.split(' ')[0],
      value: item.count
    }));
  }, [analytics]);

  const totalKycApproved = useMemo(() => {
    return kycData.find(d => d.name === 'Completed')?.value || 0;
  }, [kycData]);

  const totalKycPending = useMemo(() => {
    return kycData.find(d => d.name === 'Pending')?.value || 0;
  }, [kycData]);

  // Popout state for Cross Directorship details
  const [selectedDirectorDetail, setSelectedDirectorDetail] = useState<{ name: string, din: string } | null>(null);
  const [selectedAssociations, setSelectedAssociations] = useState<Association[]>([]);
  const [isPopOpen, setIsPopOpen] = useState(false);
  const [isDetailLoading, setIsDetailLoading] = useState(false);

  const AEGIS_PURPLE = "#75479C";
  const AEGIS_BLUE = "#0B74B0";

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [
        directorsRes,
        companyCountRes,
        crossDirectorshipRes,
        clusteringRes,
        networkRes,
        wtdCountRes,
        analyticsRes,
        registryRes
      ] = await Promise.all([
        fetch('/api/directors'),
        fetch('/api/company-count'),
        fetch('/api/cross-directorship'),
        fetch('/api/clustering'),
        fetch('/api/network'),
        fetch('/api/wtd-count'),
        fetch('/api/directors-disclosures/analytics'),
        fetch('/api/director-intelligence/summary')
      ]);

      if (!directorsRes.ok || !companyCountRes.ok || !crossDirectorshipRes.ok ||
        !clusteringRes.ok || !networkRes.ok || !wtdCountRes.ok || !analyticsRes.ok || !registryRes.ok) {
        throw new Error('Failed to fetch one or more data sets');
      }

      setDirectors(await directorsRes.json());
      setCompanyCount(await companyCountRes.json());
      setCrossDirectorship(await crossDirectorshipRes.json());
      setClustering(await clusteringRes.json());
      setNetwork(await networkRes.json());
      setWtdCount(await wtdCountRes.json());
      setAnalytics(await analyticsRes.json());
      setRegistrySummary(await registryRes.json());
    } catch (err) {
      console.error('Error fetching data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleBarClick = async (data: any) => {
    if (data && data.name && data.din) {
      setSelectedDirectorDetail({ name: data.name, din: data.din });
      setIsPopOpen(true);
      setIsDetailLoading(true);
      try {
        const res = await fetch(`/api/director-intelligence/associations/${data.din}`);
        const associations = await res.json();
        setSelectedAssociations(associations);
      } catch (err) {
        console.error("Failed to fetch associations", err);
      } finally {
        setIsDetailLoading(false);
      }
    }
  };

  // Category Detail state
  const [selectedCategory, setSelectedCategory] = useState<any>(null);
  const [isCategoryModalOpen, setIsCategoryModalOpen] = useState(false);

  const handleCategoryClick = (data: any, total: number) => {
    if (data && data.name) {
      const percentage = ((data.value / total) * 100).toFixed(0);
      let insight = "";

      // Generate insights based on category type
      if (data.name === 'Listed') insight = "Listed entities represent the group's primary regulatory and SEBI compliance perimeter.";
      else if (data.name === 'Unlisted') insight = "Private associations often indicate holding structures or diverse business interests under MCA jurisdiction.";
      else if (data.name.toUpperCase() === 'MALE') insight = "Traditional board representation profile; target for continued governance balance.";
      else if (data.name.toUpperCase() === 'FEMALE') insight = "Strategic diversity metric reflecting social responsibility and inclusive board maturity.";

      setSelectedCategory({
        ...data,
        percentage,
        insight
      });
      setIsCategoryModalOpen(true);
    }
  };

  const getTopInsights = () => {
    const insights = [];
    if (crossDirectorship.length > 0) {
      insights.push({
        title: "Most Connected",
        value: crossDirectorship[0].name,
        subValue: `${crossDirectorship[0].company_count} Companies`,
        icon: Users,
        color: "text-[#75479C]"
      });
    }
    if (companyCount && companyCount.total > 0) {
      const publicPercentage = ((companyCount.public / companyCount.total) * 100).toFixed(1);
      insights.push({
        title: "Public Entities",
        value: `${publicPercentage}%`,
        subValue: `${companyCount.public || 0} Listed Boards`,
        icon: Building2,
        color: "text-[#0B74B0]"
      });
    }
    if (clustering.length > 0) {
      insights.push({
        title: "Board Cluster",
        value: `${clustering[0].sharedCompanies} Shared`,
        subValue: `${clustering[0].director1.split(' ')[0]} & ${clustering[0].director2.split(' ')[0]}`,
        icon: Network,
        color: "text-orange-500"
      });
    }
    if (registrySummary?.total_external_boards) {
      insights.push({
        title: "Registry Reach",
        value: registrySummary.total_external_boards,
        subValue: "Total External Seats",
        icon: Globe,
        color: "text-green-600"
      });
    }
    return insights;
  };

  const topInsights = getTopInsights();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <Loader2 className="h-10 w-10 animate-spin text-[#75479C]" />
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6 bg-white overflow-x-hidden">
      {/* Premium Header - Reverted Clean White */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10 border-b border-gray-100 pb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight flex items-center gap-3">
            <FileText className="h-8 w-8 text-[#75479C]" />
            Director Intelligence Analytics
          </h1>
          <p className="text-gray-500 font-medium ml-11">Comprehensive Board Network Analysis & Registry Insights</p>
        </div>

        <div className="flex items-center gap-6">
          <div className="text-right">
            <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Enriched Profiles</p>
            <p className="text-2xl font-black text-[#75479C]">{directors.length}</p>
          </div>
          <div className="h-10 w-px bg-gray-200" />
          <div className="text-right">
            <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Data freshness</p>
            <p className="text-2xl font-black text-[#0B74B0]">{registrySummary?.total_external_boards || 0}</p>
          </div>
        </div>
      </div>

      {/* Insight Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {topInsights.map((insight, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-2xl p-6 border border-gray-100/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] transition-shadow"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className={`p-2 rounded-lg bg-gray-50 ${insight.color}`}>
                <insight.icon size={20} />
              </div>
              <h3 className="text-gray-400 font-bold text-[10px] uppercase tracking-widest">{insight.title}</h3>
            </div>
            <p className="text-xl font-black text-gray-900 mb-1">{insight.value}</p>
            <p className="text-xs font-bold text-gray-400">{insight.subValue}</p>
          </motion.div>
        ))}
      </div>

      {/* Analysis Module Selector - Reverted to Horizontal Style as requested */}
      <div className="flex flex-wrap gap-2 mb-10 bg-gray-50 p-2 rounded-2xl border border-gray-100">
        {[
          { id: 'overview', label: 'Network Overview', icon: TrendingUp },
          { id: 'cross-directorship', label: 'Cross-Directorship', icon: Network },
          { id: 'clustering', label: 'Board Collaboration', icon: Users },
          { id: 'companies', label: 'Entity Density', icon: Building2 },
          { id: 'positions', label: 'Board Designations', icon: FileText }
        ].map(item => (
          <button
            key={item.id}
            onClick={() => setActiveView(item.id)}
            className={`flex items-center gap-2.5 px-6 py-3 rounded-xl transition-all font-bold text-sm ${activeView === item.id
                ? 'bg-[#75479C] text-white shadow-md'
                : 'text-gray-500 hover:bg-white hover:text-[#75479C]'
              }`}
          >
            <item.icon size={16} />
            {item.label}
          </button>
        ))}
      </div>

      {/* Main Analysis Display - Full Width */}
      <div className="w-full">
        <AnimatePresence mode="wait">
          {activeView === 'overview' && (   
            <motion.div key="ov" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-10">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Filing Velocity & Recency Matrix */}
                <Card className="rounded-[2.5rem] border-2 border-[#0B74B0] shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden bg-white">
                  <CardHeader className="p-8 border-b border-gray-50 flex flex-row items-center justify-between">
                    <div>
                      <CardTitle className="text-xl font-black text-gray-900">Governance Freshness Index</CardTitle>
                      <CardDescription className="text-gray-500 font-medium">Weekly Filing Velocity and Submission Matrix</CardDescription>
                    </div>
                    <TrendingUp className="text-[#0B74B0]" size={24} />
                  </CardHeader>
                  <CardContent className="p-10">
                    <div className="h-[300px] w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={freshnessData}>
                          <defs>
                            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#0B74B0" stopOpacity={0.1}/>
                              <stop offset="95%" stopColor="#0B74B0" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                          <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{fill: '#94a3b8', fontSize: 12}} />
                          <YAxis axisLine={false} tickLine={false} tick={{fill: '#94a3b8', fontSize: 12}} />
                          <RechartsTooltip
                            contentStyle={{borderRadius: '15px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)'}}
                          />
                          <Area type="monotone" dataKey="value" stroke="#0B74B0" strokeWidth={4} fillOpacity={1} fill="url(#colorValue)" />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="mt-8 flex items-center justify-between p-6 bg-blue-50/30 rounded-3xl border border-blue-100/30">
                      <div className="flex items-center gap-3">
                        <div className="w-3 h-3 rounded-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]" />
                        <span className="text-xs font-bold text-blue-900">Current velocity: High</span>
                      </div>
                      <span className="text-[10px] font-black text-blue-600">Target: 45 Filings / Day</span>
                    </div>
                  </CardContent>
                </Card>

                {/* DIR-3 KYC Completion Pipeline */}
                <Card className="rounded-[2.5rem] border-2 border-[#75479C] shadow-[0_8px_30_rgb(0,0,0,0.04)] overflow-hidden bg-white">
                  <CardHeader className="p-8 border-b border-gray-50 flex flex-row items-center justify-between">
                    <div>
                      <CardTitle className="text-xl font-black text-gray-900">DIR-3 KYC Completion Pipeline</CardTitle>
                      <CardDescription className="text-gray-500 font-medium">Statutory Identity Verification Status Across Perimeter</CardDescription>
                    </div>
                    <Shield className="text-[#75479C]" size={24} />
                  </CardHeader>
                  <CardContent className="p-10">
                    <div className="h-[300px] w-full">
                      <HighchartsReact
                        highcharts={Highcharts}
                        options={{
                          chart: { 
                            type: 'pie', 
                            height: 300, 
                            backgroundColor: 'transparent',
                            events: {
                                load: function() {
                                    const chart = this;
                                    // Ensure the chart initial state is no innerSize for the fan animation
                                }
                            }
                          },
                          title: { text: '' },
                          tooltip: {
                            headerFormat: '',
                            pointFormat: '<span style="color:{point.color}">\u25cf</span> {point.name}: <b>{point.y}</b> ({point.percentage:.1f}%)'
                          },
                          plotOptions: {
                            pie: {
                              allowPointSelect: true,
                              cursor: 'pointer',
                              dataLabels: [{
                                enabled: true,
                                distance: 25,
                                format: '<span style="color:#64748b;font-weight:bold">{point.name}</span>',
                                style: { textOutline: 'none' }
                              }, {
                                enabled: true,
                                distance: -35,
                                format: '{point.percentage:.0f}%',
                                style: { fontSize: '12px', textOutline: 'none', color: '#fff', fontWeight: '500' },
                                filter: { operator: '>', property: 'percentage', value: 10 }
                              }],
                              showInLegend: false,
                              borderWidth: 2,
                              borderColor: '#fff',
                              animation: { duration: 1500 }
                            }
                          },
                          credits: { enabled: false },
                          series: [{
                            name: 'Status',
                            colorByPoint: true,
                            innerSize: '0%', // Start as 0 for fan animation update in prototype
                            data: kycData.map((d, i) => ({ 
                                name: d.name, 
                                y: d.value, 
                                color: d.color,
                                sliced: i === 1 && d.value > 0 // Slice the pending one if exists
                            }))
                          }]
                        }}
                      />
                    </div>
                    <div className="mt-8 flex items-center justify-center gap-10 p-6 bg-gray-50/50 rounded-3xl border border-gray-100/50">
                      <div className="text-center">
                        <p className="text-[10px] font-bold text-gray-400 mb-1">Approved</p>
                        <p className="text-2xl font-black text-gray-900">{totalKycApproved}</p>
                      </div>
                      <div className="w-px h-10 bg-gray-200" />
                      <div className="text-center">
                        <p className="text-[10px] font-bold text-gray-400 mb-1">Pending action</p>
                        <p className="text-2xl font-black text-amber-600">{totalKycPending}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <Card className="rounded-[2.5rem] border-2 border-[#818CF8] shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden bg-white">
                  <CardHeader className="p-8 border-b border-gray-50 flex flex-row items-center justify-between">
                    <div>
                      <CardTitle className="text-xl font-black text-gray-900">Board Portfolio Exposure</CardTitle>
                      <CardDescription className="text-gray-500 font-medium">Breakdown of Listed vs Unlisted Entities</CardDescription>
                    </div>
                    <Building2 className="text-[#818CF8]" size={24} />
                  </CardHeader>
                  <CardContent className="p-10">
                    <div className="h-[320px] relative">
                      <HighchartsReact
                        highcharts={Highcharts}
                        options={{
                          chart: { type: 'pie', height: 320, backgroundColor: 'transparent' },
                          title: { 
                            text: `<div style="text-align: center"><span style="font-size: 14px; color: #94a3b8; font-weight: 800; text-transform: uppercase; letter-spacing: 1px">Total Units</span><br/><span style="font-size: 32px; color: #0f172a; font-weight: 900">${companyCount?.total || 0}</span></div>`,
                            align: 'center',
                            verticalAlign: 'middle',
                            useHTML: true,
                            y: 5
                          },
                          tooltip: {
                            pointFormat: '{series.name}: <b>{point.y}</b>'
                          },
                          plotOptions: {
                            pie: {
                              dataLabels: {
                                enabled: true,
                                distance: 15,
                                format: '<span style="color:#64748b;">{point.name}</span><br/><span style="color:#94a3b8">{point.percentage:.1f}%</span>',
                                style: { fontSize: '10px', textOutline: 'none' }
                              },
                              innerSize: '0%', // Start as 0 for fan animation
                              borderWidth: 2,
                              borderColor: '#fff',
                              animation: { duration: 1500 }
                            }
                          },
                          credits: { enabled: false },
                          series: [{
                            name: 'Entities',
                            colorByPoint: true,
                            data: [
                              { name: 'Listed', y: companyCount?.public || 0, color: AEGIS_BLUE },
                              { name: 'Unlisted', y: companyCount?.private || 0, color: '#818CF8' } // Light Indigo
                            ]
                          }]
                        }}
                      />
                    </div>
                  </CardContent>
                </Card>

                <Card className="rounded-[2.5rem] border-2 border-[#22D3EE] shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden bg-white">
                  <CardHeader className="p-8 border-b border-gray-50 flex flex-row items-center justify-between">
                    <div>
                      <CardTitle className="text-xl font-black text-gray-900">Ecosystem Diversity</CardTitle>
                      <CardDescription className="text-gray-500 font-medium">Gender Parity Across Group Directorships</CardDescription>
                    </div>
                    <Users className="text-[#22D3EE]" size={24} />
                  </CardHeader>
                  <CardContent className="p-10">
                    <div className="h-[320px] relative">
                      <HighchartsReact
                        highcharts={Highcharts}
                        options={{
                          chart: { type: 'pie', height: 320, backgroundColor: 'transparent' },
                          title: { 
                            text: `<div style="text-align: center"><span style="font-size: 12px; color: #94a3b8; font-weight: 800; text-transform: uppercase;">Perimeter</span><br/><span style="font-size: 28px; color: #0f172a; font-weight: 900">${registrySummary?.gender?.reduce((acc: any, curr: any) => acc + curr.count, 0) || 0}</span></div>`,
                            align: 'center',
                            verticalAlign: 'middle',
                            useHTML: true,
                            y: 5
                          },
                          tooltip: {
                            pointFormat: '{point.name}: <b>{point.percentage:.1f}%</b>'
                          },
                          plotOptions: {
                            pie: {
                              dataLabels: {
                                enabled: true,
                                distance: 20,
                                format: '<span style="color:#64748b;">{point.name}</span>',
                                style: { textOutline: 'none' }
                              },
                              innerSize: '0%', // Start as 0 for fan animation
                              borderWidth: 2,
                              borderColor: '#fff',
                              animation: { duration: 1500 }
                            }
                          },
                          credits: { enabled: false },
                          series: [{
                            name: 'Gender Share',
                            colorByPoint: true,
                            data: (registrySummary?.gender || []).map((entry: any) => ({
                              name: entry.gender,
                              y: entry.count,
                              color: (entry.gender || "").toUpperCase() === 'FEMALE' ? '#22D3EE' : AEGIS_BLUE // Cyan
                            }))
                          }]
                        }}
                      />
                    </div>
                  </CardContent>
                </Card>
              </div>

              <Card className="rounded-[2.5rem] border border-gray-100/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden bg-white">
                <CardHeader className="p-8 border-b border-gray-50">
                  <div>
                    <CardTitle className="text-xl font-black text-gray-900">Association Intensity Trend</CardTitle>
                    <CardDescription className="text-gray-500 font-medium">Historical Filing Velocity and Density Patterns</CardDescription>
                  </div>
                </CardHeader>
                <CardContent className="p-10">
                  <ResponsiveContainer width="100%" height={320}>
                    <AreaChart data={analytics?.by_month || []}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                      <XAxis dataKey="month" stroke="#94a3b8" fontSize={11} />
                      <YAxis stroke="#94a3b8" fontSize={11} />
                      <RechartsTooltip 
                        contentStyle={{borderRadius: '15px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)'}}
                      />
                      <Legend verticalAlign="top" height={36} />
                      <Area name="Filing Intensity" type="monotone" dataKey="count" stroke={AEGIS_PURPLE} fill={AEGIS_PURPLE} fillOpacity={0.05} strokeWidth={3} />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {activeView === 'cross-directorship' && (
            <motion.div key="cd" className="bg-white border border-gray-100/80 rounded-[2rem] p-10 shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden">
              <div className="flex justify-between items-center mb-8 border-b border-gray-50 pb-4">
                <h3 className="text-xl font-bold text-gray-900">Board Connectivity Ranking</h3>
                <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">Click bar for company details</p>
              </div>
              <ResponsiveContainer width="100%" height={500}>
                <BarChart data={crossDirectorship.slice(0, 15)} layout="vertical" margin={{ left: 20, right: 40 }}>
                  <XAxis type="number" hide />
                  <YAxis 
                    dataKey="name" 
                    type="category" 
                    axisLine={false} 
                    tickLine={false} 
                    fontSize={12} 
                    width={180} 
                    tick={{ fontWeight: 800, fill: '#111' }} 
                    tickFormatter={(val) => toTitleCase(val)}
                  />
                  <RechartsTooltip cursor={{ fill: '#f8f8f8' }} />
                  <Bar
                    dataKey="company_count"
                    fill={AEGIS_PURPLE}
                    radius={[0, 6, 6, 0]}
                    barSize={24}
                    onClick={handleBarClick}
                    className="cursor-pointer hover:opacity-80 transition-opacity"
                  />
                </BarChart>
              </ResponsiveContainer>
            </motion.div>
          )}

          {activeView === 'clustering' && (
            <motion.div key="cl" className="bg-white border border-gray-100/80 rounded-[2rem] overflow-hidden shadow-[0_8px_30px_rgb(0,0,0,0.04)]">
              <div className="p-8 bg-gray-50 border-b border-gray-100 flex justify-between items-center">
                <h3 className="text-xl font-black text-gray-900 tracking-tight">Board Collaboration Insights</h3>
                <Users className="text-[#75479C]" size={24} />
              </div>
              <div className="p-0 overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b border-gray-100 bg-gray-50/50">
                      <th className="p-6 pl-10 text-[10px] font-black text-gray-500">Primary director</th>
                      <th className="p-6 text-[10px] font-black text-gray-500 text-center">Interlocked entities</th>
                      <th className="p-6 pr-10 text-[10px] font-black text-gray-500 text-right">Counterpart director</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {clustering.slice(0, 15).map((c, i) => (
                      <tr key={i} className="hover:bg-gray-50/50 transition-colors">
                        <td className="p-6 pl-10 font-bold text-gray-800 text-sm">{toTitleCase(c.director1)}</td>
                        <td className="p-6 text-center">
                          <div className="inline-flex flex-col items-center">
                            <span className="px-5 py-1.5 bg-[#75479C] text-white rounded-full text-[10px] font-black shadow-sm">{c.sharedCompanies} shared</span>
                            <div className="w-12 h-1 bg-gray-100 rounded-full mt-2 overflow-hidden">
                              <div className="h-full bg-[#75479C]" style={{ width: `${(c.sharedCompanies / clustering[0].sharedCompanies) * 100}%` }} />
                            </div>
                          </div>
                        </td>
                        <td className="p-6 pr-10 font-bold text-gray-800 text-sm text-right">{toTitleCase(c.director2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {activeView === 'companies' && (
            <motion.div key="comp" className="bg-white border border-gray-100/80 rounded-[2rem] p-10 shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden">
              <h3 className="text-xl font-black text-gray-900 mb-8 border-b border-gray-50 pb-4 tracking-tight">Legal entity board density</h3>
              <ResponsiveContainer width="100%" height={500}>
                <BarChart
                  data={network?.links ? Array.from(
                    new Map(network.links.map(l => [l.target, network.links.filter(x => x.target === l.target).length])),
                    ([id, val]) => {
                      const label = network?.nodes.find(n => n.id === id)?.label || id;
                      return { name: label, directors: val };
                    }
                  ).sort((a, b) => b.directors - a.directors).slice(0, 12) : []}
                  layout="vertical"
                  margin={{ left: 20, right: 40 }}
                >
                  <XAxis type="number" hide />
                  <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} fontSize={10} width={200} tick={{ fontWeight: 800, fill: '#111' }} />
                  <RechartsTooltip cursor={{ fill: '#f8f8f8' }} />
                  <Bar dataKey="directors" fill={AEGIS_BLUE} radius={[0, 6, 6, 0]} barSize={24} />
                </BarChart>
              </ResponsiveContainer>
            </motion.div>
          )}

          {activeView === 'positions' && (
            <motion.div key="pos" className="grid grid-cols-1 md:grid-cols-2 gap-10">
              <Card className="rounded-[2rem] border border-gray-100/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden bg-white">
                <div className="p-8 bg-[#75479C] text-white flex justify-between items-center">
                  <h3 className="font-bold text-lg">Top board position depth</h3>
                  <Briefcase className="opacity-40" />
                </div>
                <CardContent className="p-0">
                  <div className="divide-y divide-gray-50">
                    {wtdCount.slice(0, 15).map((d, i) => (
                      <div key={i} className="flex items-center justify-between p-6 hover:bg-gray-50 transition-colors">
                        <span className="font-bold text-gray-800 text-sm">{d.name}</span>
                        <div className="flex items-center gap-6">
                          <span className="text-xl font-black text-[#75479C]">{d.positions}</span>
                          <div className="w-12 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                            <div className="h-full bg-[#75479C]" style={{ width: `${(d.positions / (wtdCount[0]?.positions || 1)) * 100}%` }} />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <div className="space-y-8">
                <div className="bg-white rounded-[2rem] p-10 border border-gray-100/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] relative overflow-hidden group">
                  <h4 className="font-bold text-lg mb-8 flex items-center gap-3 text-gray-900">
                    <Shield className="text-[#0B74B0]" size={22} />
                    Network resilience
                  </h4>
                  <div className="space-y-8">
                    <div>
                      <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">Total ecosystem directorships</p>
                      <p className="text-5xl font-black text-[#0B74B0] tracking-tight hover:scale-105 transition-transform duration-300 origin-left">
                        {wtdCount.reduce((a, b) => a + b.positions, 0)}
                      </p>
                      <p className="text-xs font-bold text-gray-500 mt-2">Active board positions across synced entities</p>
                    </div>
                    <div className="h-px bg-gray-50" />
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Detail Modal for Cross Directorship */}
      <Dialog open={isPopOpen} onOpenChange={setIsPopOpen}>
        <DialogContent className="max-w-[800px] rounded-[2rem] p-0 overflow-hidden border-none shadow-2xl">
          <DialogHeader className="p-8 bg-gray-900 text-white">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-white/10 rounded-2xl">
                <Building2 className="text-[#0B74B0]" size={24} />
              </div>
              <div>
                <DialogTitle className="text-2xl font-black tracking-tight">{selectedDirectorDetail?.name}</DialogTitle>
                <DialogDescription className="text-gray-400 font-bold uppercase text-[10px] tracking-widest">
                  Registry board profile | DIN: {selectedDirectorDetail?.din}
                </DialogDescription>
              </div>
            </div>
          </DialogHeader>

          <div className="p-8 max-h-[500px] overflow-y-auto bg-white scrollbar-hide">
            {isDetailLoading ? (
              <div className="flex flex-col items-center justify-center p-20 gap-4">
                <Loader2 className="h-10 w-10 animate-spin text-[#75479C]" />
                <p className="text-sm font-bold text-gray-400 uppercase tracking-widest">Pulling registry records...</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4">
                {selectedAssociations.map((assoc, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    className="flex items-center justify-between p-6 bg-gray-50 rounded-2xl border border-gray-100 group hover:border-[#0B74B0] hover:bg-white transition-all shadow-sm"
                  >
                    <div className="space-y-1">
                      <h4 className="font-black text-gray-800 group-hover:text-[#0B74B0] transition-colors">{assoc.company_name}</h4>
                      <p className="text-xs font-bold text-gray-400 uppercase tracking-tighter">{assoc.designation}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-[10px] font-black text-[#75479C] uppercase tracking-widest mb-1">Since {assoc.appointment_date}</p>
                      <p className="text-[9px] font-mono text-gray-300">CIN {assoc.cin}</p>
                    </div>
                  </motion.div>
                ))}
                {selectedAssociations.length === 0 && (
                  <div className="text-center p-10 text-gray-400 font-bold italic">
                    No board associations found in the current registry sync.
                  </div>
                )}
              </div>
            )}
          </div>
          <div className="p-4 bg-gray-50 border-t border-gray-100 text-center">
            <p className="text-[9px] font-black text-gray-300">Aegis intelligence terminal | External registry data</p>
          </div>
        </DialogContent>
      </Dialog>

      {/* Category Intelligence Modal */}
      <Dialog open={isCategoryModalOpen} onOpenChange={setIsCategoryModalOpen}>
        <DialogContent className="max-w-[500px] rounded-[2rem] p-0 overflow-hidden border-none shadow-2xl">
          <DialogHeader className="p-8 bg-[#75479C] text-white">
            <div className="flex flex-col gap-2">
              <span className="text-[10px] font-black text-white/50">Category intelligence</span>
              <DialogTitle className="text-3xl font-black tracking-tighter truncate">{selectedCategory?.name} associations</DialogTitle>
            </div>
          </DialogHeader>
          <div className="p-8 bg-white">
            <div className="grid grid-cols-2 gap-6 mb-8">
              <div className="p-6 bg-gray-50 rounded-[1.5rem] border border-gray-100">
                <div>
                  <h3 className="text-xl font-black text-gray-900 tracking-tight">Category intelligence</h3>
                  <p className="text-gray-500 font-medium text-sm">Cross-functional governance distributions</p>
                </div>
                <p className="text-[10px] font-bold text-gray-400 mb-1">Concentration</p>
                <p className="text-2xl font-black text-gray-900">{selectedCategory?.value}</p>
                <p className="text-[10px] font-bold text-gray-400 mt-1">Total seats</p>
              </div>
              <div className="p-6 bg-gray-50 rounded-[1.5rem] border border-gray-100">
                <p className="text-[10px] font-bold text-gray-400 mb-1">Contribution</p>
                <p className="text-2xl font-black text-[#0B74B0]">{selectedCategory?.percentage}%</p>
                <p className="text-[10px] font-bold text-gray-400 mt-1">Ecosystem weight</p>
              </div>
            </div>
            <div className="p-6 bg-indigo-50/50 rounded-[1.5rem] border border-indigo-100 flex gap-4 items-start">
              <Lightbulb className="text-[#75479C] mt-1 shrink-0" size={20} />
              <div>
                <p className="text-[10px] font-black text-[#75479C] mb-1">Strategic insight</p>
                <p className="text-sm font-bold text-gray-700 leading-relaxed">
                  {selectedCategory?.insight}
                </p>
              </div>
            </div>
          </div>
          <div className="p-4 bg-gray-50 border-t border-gray-100 text-center">
            <p className="text-[9px] font-black text-gray-300">Aegis Discovery Terminal | System Intelligence</p>
          </div>
        </DialogContent>
      </Dialog>

          <footer className="mt-12 pt-8 border-t border-gray-50 text-center opacity-30">
            <span className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]">Aegis Institutional Risk & Compliance Terminal</span>
          </footer>
    </div>
  );
};

export default DirectorsDisclosureAnalytics;