import React, { useState, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell, ResponsiveContainer, ScatterChart, Scatter } from 'recharts';
import { Users, Building2, Network, TrendingUp, FileText } from 'lucide-react';

const DirectorAnalyticsDashboard = () => {
  // Sample data structure based on the document format
  const [sampleData] = useState([
    {
      name: "Abdul Ishad Khan",
      din: "11280634",
      companies: [
        { name: "ADANI RENEWABLE ENERGY (RJ) LIMITED", type: "Public", position: "Whole-time Director", date: "08/10/2025" },
        { name: "ADANI GREEN ENERGY SIX LIMITED", type: "Public", position: "Additional Director", date: "07/10/2025" },
        { name: "ADANI RENEWABLE ENERGY HOLDING ELEVEN LIMITED", type: "Public", position: "Additional Director", date: "07/10/2025" },
        { name: "ADANI RENEWABLE ENERGY HOLDING SIX LIMITED", type: "Public", position: "Additional Director", date: "07/10/2025" },
        { name: "ADANI HYBRID ENERGY JAISALMER THREE LIMITED", type: "Public", position: "Additional Director", date: "07/10/2025" },
        { name: "ADANI GREEN ENERGY EIGHT LIMITED", type: "Public", position: "Additional Director", date: "07/10/2025" },
        { name: "ADANI HYBRID ENERGY JAISALMER TWO LIMITED", type: "Public", position: "Additional Director", date: "07/10/2025" },
        { name: "ADANI RENEWABLE ENERGY HOLDING SEVEN LIMITED", type: "Public", position: "Additional Director", date: "07/10/2025" },
        { name: "ADANI SOLAR ENERGY FOUR LIMITED", type: "Public", position: "Additional Director", date: "07/10/2025" }
      ]
    },
    {
      name: "Rajesh Kumar",
      din: "11280635",
      companies: [
        { name: "ADANI GREEN ENERGY SIX LIMITED", type: "Public", position: "Additional Director", date: "05/09/2025" },
        { name: "ADANI RENEWABLE ENERGY HOLDING ELEVEN LIMITED", type: "Public", position: "Additional Director", date: "05/09/2025" },
        { name: "ADANI HYBRID ENERGY JAISALMER THREE LIMITED", type: "Public", position: "Whole-time Director", date: "01/08/2025" },
        { name: "ADANI POWER LIMITED", type: "Public", position: "Additional Director", date: "15/07/2025" },
        { name: "ADANI INFRASTRUCTURE LIMITED", type: "Private", position: "Director", date: "20/06/2025" }
      ]
    },
    {
      name: "Priya Sharma",
      din: "11280636",
      companies: [
        { name: "ADANI GREEN ENERGY EIGHT LIMITED", type: "Public", position: "Additional Director", date: "10/10/2025" },
        { name: "ADANI SOLAR ENERGY FOUR LIMITED", type: "Public", position: "Whole-time Director", date: "12/09/2025" },
        { name: "ADANI RENEWABLE ENERGY (RJ) LIMITED", type: "Public", position: "Additional Director", date: "08/10/2025" }
      ]
    },
    {
      name: "Amit Patel",
      din: "11280637",
      companies: [
        { name: "ADANI POWER LIMITED", type: "Public", position: "Whole-time Director", date: "15/07/2025" },
        { name: "ADANI INFRASTRUCTURE LIMITED", type: "Private", position: "Additional Director", date: "20/06/2025" },
        { name: "ADANI GREEN ENERGY SIX LIMITED", type: "Public", position: "Additional Director", date: "05/09/2025" }
      ]
    },
    {
      name: "Sunita Reddy",
      din: "11280638",
      companies: [
        { name: "ADANI RENEWABLE ENERGY HOLDING SEVEN LIMITED", type: "Public", position: "Additional Director", date: "07/10/2025" },
        { name: "ADANI HYBRID ENERGY JAISALMER TWO LIMITED", type: "Public", position: "Additional Director", date: "07/10/2025" }
      ]
    }
  ]);

  const [activeView, setActiveView] = useState('overview');

  // Analytics calculations
  const analytics = useMemo(() => {
    // Total directors and companies
    const totalDirectors = sampleData.length;
    const allCompanies = new Set();
    const companyDirectorCount = {};
    const directorCompanyCount = {};
    const positionTypes = {};
    const companyTypes = { Public: 0, Private: 0 };
    const wholetimeDirectors = {};
    const directorConnections = {};

    sampleData.forEach(director => {
      directorCompanyCount[director.name] = director.companies.length;
      wholetimeDirectors[director.name] = 0;

      director.companies.forEach(company => {
        allCompanies.add(company.name);
        
        // Count directors per company
        companyDirectorCount[company.name] = (companyDirectorCount[company.name] || 0) + 1;
        
        // Count position types
        positionTypes[company.position] = (positionTypes[company.position] || 0) + 1;
        
        // Count company types
        companyTypes[company.type]++;
        
        // Count whole-time positions
        if (company.position === "Whole-time Director") {
          wholetimeDirectors[director.name]++;
        }
      });
    });

    // Director clustering - find directors who share companies
    sampleData.forEach(director => {
      directorConnections[director.name] = {};
      director.companies.forEach(company => {
        sampleData.forEach(otherDirector => {
          if (director.name !== otherDirector.name) {
            const sharedCompany = otherDirector.companies.find(c => c.name === company.name);
            if (sharedCompany) {
              directorConnections[director.name][otherDirector.name] = 
                (directorConnections[director.name][otherDirector.name] || 0) + 1;
            }
          }
        });
      });
    });

    return {
      totalDirectors,
      totalCompanies: allCompanies.size,
      companyDirectorCount,
      directorCompanyCount,
      positionTypes,
      companyTypes,
      wholetimeDirectors,
      directorConnections
    };
  }, [sampleData]);

  // Prepare chart data
  const crossDirectorshipData = Object.entries(analytics.directorCompanyCount)
    .map(([name, count]) => ({ name: name.split(' ').slice(0, 2).join(' '), companies: count }))
    .sort((a, b) => b.companies - a.companies);

  const companyDirectorData = Object.entries(analytics.companyDirectorCount)
    .map(([name, count]) => ({ 
      name: name.length > 30 ? name.substring(0, 30) + '...' : name, 
      directors: count,
      fullName: name
    }))
    .sort((a, b) => b.directors - a.directors)
    .slice(0, 10);

  const positionTypeData = Object.entries(analytics.positionTypes)
    .map(([type, count]) => ({ name: type, value: count }));

  const companyTypeData = [
    { name: 'Public', value: analytics.companyTypes.Public },
    { name: 'Private', value: analytics.companyTypes.Private }
  ];

  const wholetimeData = Object.entries(analytics.wholetimeDirectors)
    .filter(([_, count]) => count > 0)
    .map(([name, count]) => ({ name: name.split(' ').slice(0, 2).join(' '), positions: count }))
    .sort((a, b) => b.positions - a.positions);

  const networkData = useMemo(() => {
    const nodes = [];
    const links = [];
    
    sampleData.forEach(director => {
      nodes.push({ id: director.name, type: 'director', companies: director.companies.length });
      
      director.companies.forEach(company => {
        if (!nodes.find(n => n.id === company.name)) {
          nodes.push({ id: company.name, type: 'company' });
        }
        links.push({ source: director.name, target: company.name });
      });
    });
    
    return { nodes, links };
  }, [sampleData]);

  const clusteringData = useMemo(() => {
    const clusters = [];
    Object.entries(analytics.directorConnections).forEach(([director, connections]) => {
      Object.entries(connections).forEach(([connectedDirector, sharedCount]) => {
        clusters.push({
          director1: director.split(' ').slice(0, 2).join(' '),
          director2: connectedDirector.split(' ').slice(0, 2).join(' '),
          sharedCompanies: sharedCount
        });
      });
    });
    return clusters.sort((a, b) => b.sharedCompanies - a.sharedCompanies).slice(0, 15);
  }, [analytics.directorConnections]);

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Director Network Analytics</h1>
          <p className="text-blue-200">Comprehensive analysis of {analytics.totalDirectors} directors across {analytics.totalCompanies} companies</p>
        </div>

        {/* Navigation */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {[
            { id: 'overview', label: 'Overview', icon: TrendingUp },
            { id: 'cross-directorship', label: 'Cross-Directorship', icon: Network },
            { id: 'clustering', label: 'Director Clustering', icon: Users },
            { id: 'companies', label: 'Company Analysis', icon: Building2 },
            { id: 'positions', label: 'Position Analysis', icon: FileText }
          ].map(view => (
            <button
              key={view.id}
              onClick={() => setActiveView(view.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all whitespace-nowrap ${
                activeView === view.id
                  ? 'bg-blue-500 text-white shadow-lg'
                  : 'bg-white/10 text-white hover:bg-white/20'
              }`}
            >
              <view.icon size={18} />
              {view.label}
            </button>
          ))}
        </div>

        {/* Overview */}
        {activeView === 'overview' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
                <Users className="text-blue-400 mb-2" size={32} />
                <div className="text-3xl font-bold text-white">{analytics.totalDirectors}</div>
                <div className="text-blue-200 text-sm">Total Directors</div>
              </div>
              <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
                <Building2 className="text-green-400 mb-2" size={32} />
                <div className="text-3xl font-bold text-white">{analytics.totalCompanies}</div>
                <div className="text-blue-200 text-sm">Total Companies</div>
              </div>
              <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
                <Network className="text-purple-400 mb-2" size={32} />
                <div className="text-3xl font-bold text-white">
                  {(analytics.totalCompanies / analytics.totalDirectors).toFixed(1)}
                </div>
                <div className="text-blue-200 text-sm">Avg Companies/Director</div>
              </div>
              <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
                <FileText className="text-yellow-400 mb-2" size={32} />
                <div className="text-3xl font-bold text-white">{analytics.companyTypes.Public}</div>
                <div className="text-blue-200 text-sm">Public Companies</div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
                <h3 className="text-xl font-bold text-white mb-4">Company Type Distribution</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={companyTypeData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }) => `${name}: ${value}`}
                      outerRadius={100}
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

              <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
                <h3 className="text-xl font-bold text-white mb-4">Position Type Distribution</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={positionTypeData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }) => `${name.split(' ')[0]}: ${value}`}
                      outerRadius={100}
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
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
            <h3 className="text-xl font-bold text-white mb-4">Directors Serving Multiple Companies</h3>
            <p className="text-blue-200 mb-6">Shows which directors serve on multiple Adani group companies</p>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={crossDirectorshipData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" />
                <XAxis dataKey="name" stroke="#fff" angle={-45} textAnchor="end" height={100} />
                <YAxis stroke="#fff" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                  labelStyle={{ color: '#fff' }}
                />
                <Bar dataKey="companies" fill="#3b82f6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <div className="mt-6 text-white">
              <h4 className="font-bold mb-2">Key Insights:</h4>
              <ul className="list-disc list-inside space-y-1 text-blue-200">
                <li>Most connected director: {crossDirectorshipData[0]?.name} ({crossDirectorshipData[0]?.companies} companies)</li>
                <li>Average directorships per person: {(analytics.totalCompanies / analytics.totalDirectors).toFixed(1)}</li>
              </ul>
            </div>
          </div>
        )}

        {/* Director Clustering */}
        {activeView === 'clustering' && (
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
            <h3 className="text-xl font-bold text-white mb-4">Director Clustering - Shared Companies</h3>
            <p className="text-blue-200 mb-6">Identifies directors who share common companies (potential collaboration networks)</p>
            <div className="overflow-x-auto">
              <table className="w-full text-white">
                <thead>
                  <tr className="border-b border-white/20">
                    <th className="text-left py-3 px-4">Director 1</th>
                    <th className="text-left py-3 px-4">Director 2</th>
                    <th className="text-left py-3 px-4">Shared Companies</th>
                  </tr>
                </thead>
                <tbody>
                  {clusteringData.map((cluster, idx) => (
                    <tr key={idx} className="border-b border-white/10 hover:bg-white/5">
                      <td className="py-3 px-4">{cluster.director1}</td>
                      <td className="py-3 px-4">{cluster.director2}</td>
                      <td className="py-3 px-4">
                        <span className="bg-blue-500 px-3 py-1 rounded-full text-sm">
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
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
              <h3 className="text-xl font-bold text-white mb-4">Companies by Director Count</h3>
              <p className="text-blue-200 mb-6">Shows which companies have the most/least directors</p>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={companyDirectorData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" />
                  <XAxis type="number" stroke="#fff" />
                  <YAxis dataKey="name" type="category" stroke="#fff" width={200} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                    labelStyle={{ color: '#fff' }}
                    formatter={(value, name, props) => [value, props.payload.fullName]}
                  />
                  <Bar dataKey="directors" fill="#10b981" radius={[0, 8, 8, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
              <h3 className="text-xl font-bold text-white mb-4">Network Visualization Preview</h3>
              <p className="text-blue-200 mb-4">Interconnections between directors and companies</p>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div className="bg-blue-500/20 border border-blue-500 rounded-lg p-4">
                  <div className="text-2xl font-bold text-white">{networkData.nodes.filter(n => n.type === 'director').length}</div>
                  <div className="text-blue-200 text-sm">Director Nodes</div>
                </div>
                <div className="bg-green-500/20 border border-green-500 rounded-lg p-4">
                  <div className="text-2xl font-bold text-white">{networkData.nodes.filter(n => n.type === 'company').length}</div>
                  <div className="text-blue-200 text-sm">Company Nodes</div>
                </div>
                <div className="bg-purple-500/20 border border-purple-500 rounded-lg p-4">
                  <div className="text-2xl font-bold text-white">{networkData.links.length}</div>
                  <div className="text-blue-200 text-sm">Total Connections</div>
                </div>
              </div>
              <div className="mt-4 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                <p className="text-yellow-200 text-sm">
                  💡 <strong>Recommendation:</strong> Use D3.js or Cytoscape.js for advanced force-directed network visualization
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Position Analysis */}
        {activeView === 'positions' && (
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
            <h3 className="text-xl font-bold text-white mb-4">Whole-time Director Positions</h3>
            <p className="text-blue-200 mb-6">Directors with the most whole-time positions (indicates higher responsibility)</p>
            {wholetimeData.length > 0 ? (
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={wholetimeData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" />
                  <XAxis dataKey="name" stroke="#fff" angle={-45} textAnchor="end" height={100} />
                  <YAxis stroke="#fff" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                    labelStyle={{ color: '#fff' }}
                  />
                  <Bar dataKey="positions" fill="#f59e0b" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center py-12 text-blue-200">
                No whole-time director positions found in current dataset
              </div>
            )}
            <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(analytics.positionTypes).map(([type, count]) => (
                <div key={type} className="bg-white/5 rounded-lg p-4 border border-white/10">
                  <div className="text-2xl font-bold text-white">{count}</div>
                  <div className="text-blue-200 text-sm">{type}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 text-center">
          <p className="text-blue-200 text-sm">
            📊 Data based on Form MBP-1 documents | Analysis for {analytics.totalDirectors} directors
          </p>
          <p className="text-blue-300 text-xs mt-2">
            Scale this to 100+ directors by parsing all documents with the same structure
          </p>
        </div>
      </div>
    </div>
  );
};

export default DirectorAnalyticsDashboard;