import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { FileText, Loader2, AlertCircle, Users, Building2, Network, TrendingUp, Lightbulb } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

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
  companies: number;
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
  const [activeView, setActiveView] = useState('overview');
  const [directors, setDirectors] = useState<Director[]>([]);
  const [companyCount, setCompanyCount] = useState<CompanyCount | null>(null);
  const [crossDirectorship, setCrossDirectorship] = useState<CrossDirectorship[]>([]);
  const [clustering, setClustering] = useState<Clustering[]>([]);
  const [network, setNetwork] = useState<NetworkData | null>(null);
  const [wtdCount, setWtdCount] = useState<WTDCount[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch all required data in parallel
      const [
        directorsRes,
        companyCountRes,
        crossDirectorshipRes,
        clusteringRes,
        networkRes,
        wtdCountRes,
        analyticsRes
      ] = await Promise.all([
        fetch('/api/directors'),
        fetch('/api/company-count'),
        fetch('/api/cross-directorship'),
        fetch('/api/clustering'),
        fetch('/api/network'),
        fetch('/api/wtd-count'),
        fetch('/api/directors-disclosures/analytics')
      ]);

      // Check if all responses are ok
      if (!directorsRes.ok || !companyCountRes.ok || !crossDirectorshipRes.ok ||
        !clusteringRes.ok || !networkRes.ok || !wtdCountRes.ok || !analyticsRes.ok) {
        throw new Error('Failed to fetch one or more data sets');
      }

      // Parse all data
      const directorsData = await directorsRes.json();
      const companyCountData = await companyCountRes.json();
      const crossDirectorshipData = await crossDirectorshipRes.json();
      const clusteringData = await clusteringRes.json();
      const networkData = await networkRes.json();
      const wtdCountData = await wtdCountRes.json();
      const analyticsData = await analyticsRes.json();

      // Set all state
      setDirectors(directorsData);
      setCompanyCount(companyCountData);
      setCrossDirectorship(crossDirectorshipData);
      setClustering(clusteringData);
      setNetwork(networkData);
      setWtdCount(wtdCountData);
      setAnalytics(analyticsData);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  // Calculate insights dynamically
  const getTopInsights = () => {
    const insights = [];

    // Most connected director
    if (crossDirectorship.length > 0) {
      const topDirector = crossDirectorship[0];
      insights.push({
        title: "Most Connected Director",
        value: `${topDirector.name} with ${topDirector.companies} companies`,
        icon: Users
      });
    }

    // Percentage of public companies
    if (companyCount && companyCount.total > 0) {
      const publicPercentage = ((companyCount.public / companyCount.total) * 100).toFixed(1);
      insights.push({
        title: "Public Companies",
        value: `${publicPercentage}% of companies are public`,
        icon: Building2
      });
    }

    // Directors who share the most companies
    if (clustering.length > 0) {
      const topCluster = clustering[0];
      insights.push({
        title: "Most Shared Companies",
        value: `${topCluster.director1} and ${topCluster.director2} share ${topCluster.sharedCompanies} companies`,
        icon: Network
      });
    }

    // Company with highest board size
    if (network && network.links.length > 0) {
      // Count directors per company
      const companyDirectorCount = new Map();
      network.links.forEach(link => {
        const count = companyDirectorCount.get(link.target) || 0;
        companyDirectorCount.set(link.target, count + 1);
      });

      // Find company with highest count
      let maxCompanyId = "";
      let maxCount = 0;
      companyDirectorCount.forEach((count, companyId) => {
        if (count > maxCount) {
          maxCount = count;
          maxCompanyId = companyId;
        }
      });

      if (maxCompanyId) {
        // Find the company name from nodes
        const companyNode = network.nodes.find(n => n.id === maxCompanyId);
        const companyName = companyNode?.label || maxCompanyId;
        
        insights.push({
          title: "Largest Board Size",
          value: `${companyName} has ${maxCount} directors`,
          icon: TrendingUp
        });
      }
    }

    return insights;
  };

  const COLORS = ['#75479C', '#0B74B0', '#FF9800', '#4CAF50', '#8884D8', '#82CA9D'];

  // Prepare chart data
  const companyTypeData = companyCount ? [
    { name: 'Public', value: companyCount.public },
    { name: 'Private', value: companyCount.private }
  ] : [];

  const positionTypeData = wtdCount && wtdCount.length > 0 ? [
    { name: 'Whole-time Director', value: wtdCount.reduce((sum, item) => sum + item.positions, 0) },
    { name: 'Other Positions', value: (companyCount?.total || 0) - wtdCount.reduce((sum, item) => sum + item.positions, 0) }
  ] : [];

  const topInsights = getTopInsights();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "#ffffff" }}>
        <div className="text-center">
          <Loader2 className="h-10 w-10 animate-spin mx-auto mb-3" style={{ color: "#75479C" }} />
          <p className="text-base" style={{ color: "#000000" }}>Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "#ffffff" }}>
        <div className="text-center p-5 max-w-md">
          <AlertCircle className="h-10 w-10 mx-auto mb-3" style={{ color: "#EF4444" }} />
          <h2 className="text-lg font-semibold mb-2" style={{ color: "#000000" }}>Error Loading Analytics</h2>
          <p className="mb-3 text-sm" style={{ color: "#000000" }}>{error}</p>
          <button
            onClick={fetchAllData}
            className="px-3 py-1.5 bg-[#75479C] text-white rounded text-sm hover:bg-[#5a357a] transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 md:p-6" style={{ background: "#ffffff" }}>
      <div className="mb-5">
        <Card className="border-0 shadow-none bg-transparent">
          <CardHeader className="px-0 pb-3">
            <div className="flex items-center gap-2.5">
              <FileText className="h-7 w-7" style={{ color: "#75479C" }} />
              <div>
                <CardTitle className="text-xl font-semibold" style={{ color: "#000000" }}>
                  Director Analytics
                </CardTitle>
                <CardDescription className="text-sm" style={{ color: '#666666' }}>
                  Comprehensive analysis of {directors.length} directors across {companyCount?.total || 0} companies
                </CardDescription>
              </div>
            </div>
          </CardHeader>
        </Card>
      </div>

      {/* Top Insights Summary */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Lightbulb className="h-6 w-6 text-[#75479C]" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-gray-900">Key Intelligence</h3>
            <p className="text-sm text-gray-500">Automated insights from across the disclosure network</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {topInsights.map((insight, index) => (
            <motion.div
              key={index}
              whileHover={{ y: -5 }}
              className="bg-white border border-gray-100 rounded-xl p-5 shadow-sm hover:shadow-md transition-all"
            >
              <div className="flex items-center gap-4 mb-4">
                <div className="p-2 bg-gray-50 rounded-lg">
                  <insight.icon className="h-5 w-5 text-[#75479C]" />
                </div>
                <h4 className="font-semibold text-sm text-gray-800 leading-tight">{insight.title}</h4>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-sm font-bold text-[#75479C] text-center">{insight.value}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Navigation - Premium modern tabs */}
      <div className="flex justify-center mb-8">
        <div className="inline-flex p-1 bg-gray-100/80 backdrop-blur-sm rounded-xl border border-gray-200 shadow-inner">
          {[
            { id: 'overview', label: 'Overview', icon: TrendingUp },
            { id: 'cross-directorship', label: 'Cross-Directorship', icon: Network },
            { id: 'clustering', label: 'Clustering', icon: Users },
            { id: 'companies', label: 'Companies', icon: Building2 },
            { id: 'positions', label: 'Positions', icon: FileText }
          ].map(view => (
            <button
              key={view.id}
              onClick={() => setActiveView(view.id)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-lg font-bold text-sm transition-all duration-200 ${activeView === view.id
                ? 'bg-white text-[#75479C] shadow-sm'
                : 'text-gray-500 hover:text-gray-700 hover:bg-white/50'
                }`}
            >
              <view.icon className="h-4 w-4" />
              {view.label}
            </button>
          ))}
        </div>
      </div>

      {/* Overview */}
      {activeView === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <motion.div
              whileHover={{ scale: 1.02 }}
              className="bg-white border border-purple-100 rounded-xl p-6 shadow-sm flex flex-col items-center text-center"
            >
              <div className="p-3 bg-purple-50 rounded-full mb-3">
                <Users className="text-[#75479C]" size={28} />
              </div>
              <div className="text-3xl font-extrabold text-gray-900">{directors.length}</div>
              <div className="text-gray-500 text-xs font-bold uppercase tracking-wider">Total Directors</div>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.02 }}
              className="bg-white border border-blue-100 rounded-xl p-6 shadow-sm flex flex-col items-center text-center"
            >
              <div className="p-3 bg-blue-50 rounded-full mb-3">
                <Building2 className="text-[#0B74B0]" size={28} />
              </div>
              <div className="text-3xl font-extrabold text-gray-900">{companyCount?.total || 0}</div>
              <div className="text-gray-500 text-xs font-bold uppercase tracking-wider">Total Companies</div>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.02 }}
              className="bg-white border border-green-100 rounded-xl p-6 shadow-sm flex flex-col items-center text-center"
            >
              <div className="p-3 bg-green-50 rounded-full mb-3">
                <Network className="text-[#4CAF50]" size={28} />
              </div>
              <div className="text-3xl font-extrabold text-gray-900">
                {directors.length > 0 ? ((companyCount?.total || 0) / directors.length).toFixed(1) : 0}
              </div>
              <div className="text-gray-500 text-xs font-bold uppercase tracking-wider">Avg Per Director</div>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.02 }}
              className="bg-white border border-orange-100 rounded-xl p-6 shadow-sm flex flex-col items-center text-center"
            >
              <div className="p-3 bg-orange-50 rounded-full mb-3">
                <FileText className="text-[#FF9800]" size={28} />
              </div>
              <div className="text-3xl font-extrabold text-gray-900">{companyCount?.public || 0}</div>
              <div className="text-gray-500 text-xs font-bold uppercase tracking-wider">Public Companies</div>
            </motion.div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white border rounded-md p-5 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Company Type Distribution</h3>
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={companyTypeData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={90}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {companyTypeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-white border rounded-md p-5 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Position Type Distribution</h3>
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={positionTypeData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => name ? `${name.split(' ')[0]}: ${(percent * 100).toFixed(0)}%` : ''}
                    outerRadius={90}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {positionTypeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Cross-Directorship Mapping */}
      {activeView === 'cross-directorship' && (
        <div className="bg-white border rounded-md p-5 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Directors Serving Multiple Companies</h3>
          <p className="text-gray-600 text-sm mb-5">Shows which directors serve on multiple companies</p>
          <ResponsiveContainer width="100%" height={450}>
            <BarChart data={crossDirectorship.slice(0, 10)} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
              <XAxis type="number" stroke="#666" fontSize={12} />
              <YAxis
                dataKey="name"
                type="category"
                stroke="#666"
                width={150}
                tick={{ fontSize: 11 }}
                tickFormatter={(value) => value.length > 20 ? `${value.substring(0, 20)}...` : value}
              />
              <Tooltip
                contentStyle={{ backgroundColor: '#fff', border: '1px solid #ddd', borderRadius: '6px', fontSize: '12px' }}
                labelStyle={{ color: '#000', fontSize: '12px' }}
              />
              <Bar dataKey="companies" fill="#75479C" radius={[0, 6, 6, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-5 text-gray-900">
            <h4 className="font-medium text-sm mb-2">Key Insights:</h4>
            <ul className="list-none list-inside space-y-1 text-gray-600 text-sm">
              {crossDirectorship.length > 0 && (
                <li>Most connected director: {crossDirectorship[0]?.name} ({crossDirectorship[0]?.companies} companies)</li>
              )}
              <li>Average directorships per person: {directors.length > 0 ? ((companyCount?.total || 0) / directors.length).toFixed(1) : 0}</li>
            </ul>
          </div>
        </div>
      )}

      {/* Director Clustering */}
      {activeView === 'clustering' && (
        <div className="bg-white border rounded-md p-5 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Director Clustering - Shared Companies</h3>
          <p className="text-gray-600 text-sm mb-5">Identifies directors who share common companies (potential collaboration networks)</p>
          <div className="overflow-x-auto rounded-xl border border-gray-100 shadow-sm">
            <table className="w-full text-gray-900 text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-100">
                  <th className="text-left py-4 px-6 font-bold uppercase tracking-wider text-[11px] text-gray-500">Director 1</th>
                  <th className="text-left py-4 px-6 font-bold uppercase tracking-wider text-[11px] text-gray-500">Director 2</th>
                  <th className="text-left py-4 px-6 font-bold uppercase tracking-wider text-[11px] text-gray-500">Shared Companies</th>
                </tr>
              </thead>
              <tbody>
                {clustering.slice(0, 10).map((cluster, idx) => (
                  <tr key={idx} className="border-b border-gray-50 hover:bg-purple-50/30 transition-colors">
                    <td className="py-4 px-6 font-medium">{cluster.director1}</td>
                    <td className="py-4 px-6 font-medium">{cluster.director2}</td>
                    <td className="py-4 px-6">
                      <span className="bg-purple-600 text-white font-bold px-4 py-1.5 rounded-full text-xs shadow-sm">
                        {cluster.sharedCompanies}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Company Analysis */}
      {activeView === 'companies' && (
        <div className="space-y-6">
          <div className="bg-white border rounded-md p-5 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Companies by Director Count</h3>
            <p className="text-gray-600 text-sm mb-5">Shows which companies have the most/least directors</p>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart
                data={Array.from(
                  new Map(
                    (network?.links || []).map(link => {
                      const companyId = link.target;
                      const companyNode = network?.nodes.find(n => n.id === companyId);
                      const companyName = companyNode?.label || companyId;
                      return [companyId, { name: companyName, directors: (network?.links.filter(l => l.target === companyId).length || 0) }];
                    })
                  ).values()
                ).sort((a, b) => b.directors - a.directors).slice(0, 10)}
                layout="vertical"
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                <XAxis type="number" stroke="#666" fontSize={12} />
                <YAxis
                  dataKey="name"
                  type="category"
                  stroke="#666"
                  width={150}
                  tick={{ fontSize: 11 }}
                  tickFormatter={(value) => value.length > 20 ? `${value.substring(0, 20)}...` : value}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#fff', border: '1px solid #ddd', borderRadius: '6px', fontSize: '12px' }}
                  labelStyle={{ color: '#000', fontSize: '12px' }}
                />
                <Bar dataKey="directors" fill="#0B74B0" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white border rounded-md p-5 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Company Network Statistics</h3>
            <p className="text-gray-600 text-sm mb-4">Interconnections between directors and companies</p>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="bg-[#75479C]/10 border border-[#75479C]/20 rounded-md p-4">
                <div className="text-2xl font-semibold text-gray-900">{network?.nodes.filter(n => n.type === 'director').length || 0}</div>
                <div className="text-gray-600 text-xs">Directors</div>
              </div>
              <div className="bg-[#0B74B0]/10 border border-[#0B74B0]/20 rounded-md p-4">
                <div className="text-2xl font-semibold text-gray-900">{network?.nodes.filter(n => n.type === 'company').length || 0}</div>
                <div className="text-gray-600 text-xs">Companies</div>
              </div>
              <div className="bg-[#4CAF50]/10 border border-[#4CAF50]/20 rounded-md p-4">
                <div className="text-2xl font-semibold text-gray-900">{network?.links.length || 0}</div>
                <div className="text-gray-600 text-xs">Connections</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Position Analysis */}
      {activeView === 'positions' && (
        <div className="bg-white border rounded-md p-5 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Whole-time Director Positions</h3>
          <p className="text-gray-600 text-sm mb-5">Directors with the most whole-time positions (indicates higher responsibility)</p>
          {wtdCount.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={wtdCount.slice(0, 10)} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                <XAxis type="number" stroke="#666" fontSize={12} />
                <YAxis
                  dataKey="name"
                  type="category"
                  stroke="#666"
                  width={150}
                  tick={{ fontSize: 11 }}
                  tickFormatter={(value) => value.length > 20 ? `${value.substring(0, 20)}...` : value}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#fff', border: '1px solid #ddd', borderRadius: '6px', fontSize: '12px' }}
                  labelStyle={{ color: '#000', fontSize: '12px' }}
                />
                <Bar dataKey="positions" fill="#FF9800" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center py-10 text-gray-600 text-sm">
              No whole-time director positions found in current dataset
            </div>
          )}
          <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-50 rounded-md p-4 border border-gray-200">
              <div className="text-2xl font-semibold text-gray-900">{wtdCount.reduce((sum, item) => sum + item.positions, 0)}</div>
              <div className="text-gray-600 text-xs">Total WTD Positions</div>
            </div>
            <div className="bg-gray-50 rounded-md p-4 border border-gray-200">
              <div className="text-2xl font-semibold text-gray-900">{wtdCount.length}</div>
              <div className="text-gray-600 text-xs">Directors with WTD</div>
            </div>
            <div className="bg-gray-50 rounded-md p-4 border border-gray-200">
              <div className="text-2xl font-semibold text-gray-900">
                {wtdCount.length > 0 ? (wtdCount.reduce((sum, item) => sum + item.positions, 0) / wtdCount.length).toFixed(1) : 0}
              </div>
              <div className="text-gray-600 text-xs">Avg WTD per Director</div>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="mt-8 text-center">
        <p className="text-gray-600 text-sm">
          📊 Data based on Form MBP-1 documents | Analysis for {directors.length} directors
        </p>
      </div>
    </div>
  );
};

export default DirectorsDisclosureAnalytics;