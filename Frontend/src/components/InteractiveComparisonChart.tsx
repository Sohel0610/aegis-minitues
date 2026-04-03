import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface InteractiveComparisonChartProps {
    initialData: { labels: string[]; values: number[] };
    title: string;
    month?: number;
    year?: number;
}

const CHART_COLORS = ['#0B74B0', '#75479C', '#BD3861', '#10B981', '#F59E0B', '#14B8A6'];

export const InteractiveComparisonChart: React.FC<InteractiveComparisonChartProps> = ({
    initialData,
    title,
    month,
    year
}) => {
    const [chartData, setChartData] = useState<{ name: string; value: number; color: string }[]>([]);
    const [allCompanies, setAllCompanies] = useState<string[]>([]);
    const [selectedCompanies, setSelectedCompanies] = useState<Set<string>>(new Set());
    const [isLoading, setIsLoading] = useState(false);
    const [showSelector, setShowSelector] = useState(false);

    // Initialize chart data
    useEffect(() => {
        const labels = Array.isArray(initialData?.labels) ? initialData.labels : [];
        const values = Array.isArray(initialData?.values) ? initialData.values : [];
        const data = labels.map((label, idx) => ({
            name: label,
            value: Number(values[idx] ?? 0),
            color: CHART_COLORS[idx % CHART_COLORS.length]
        }));
        setChartData(data);
        setSelectedCompanies(new Set(labels));
    }, [initialData]);

    // Fetch all available companies
    useEffect(() => {
        const fetchCompanies = async () => {
            try {
                const params = new URLSearchParams();
                if (month) params.append('month', month.toString());
                if (year) params.append('year', year.toString());

                const res = await fetch(`/api/companies?${params.toString()}`);
                if (res.ok) {
                    const data = await res.json();
                    setAllCompanies(data.companies || []);
                }
            } catch (error) {
                console.error('Failed to fetch companies:', error);
            }
        };
        fetchCompanies();
    }, [month, year]);

    const toggleCompany = async (companyName: string) => {
        const newSelected = new Set(selectedCompanies);

        if (newSelected.has(companyName)) {
            // Remove company
            newSelected.delete(companyName);
            setSelectedCompanies(newSelected);
            setChartData(prev => prev.filter(d => d.name !== companyName));
        } else {
            // Add company
            setIsLoading(true);
            try {
                const params = new URLSearchParams({
                    companies: companyName,
                    ...(month && { month: month.toString() }),
                    ...(year && { year: year.toString() })
                });

                const res = await fetch(`/api/compare?${params.toString()}`);
                if (res.ok) {
                    const data = await res.json();
                    const newValue = data.values[0] || 0;

                    newSelected.add(companyName);
                    setSelectedCompanies(newSelected);
                    setChartData(prev => [
                        ...prev,
                        {
                            name: companyName,
                            value: newValue,
                            color: CHART_COLORS[prev.length % CHART_COLORS.length]
                        }
                    ]);
                }
            } catch (error) {
                console.error('Failed to add company:', error);
            } finally {
                setIsLoading(false);
            }
        }
    };

    return (
        <div className="w-full mt-3 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex justify-between items-center mb-3">
                <div className="text-sm font-semibold text-slate-800">{title}</div>
                <button
                    onClick={() => setShowSelector(!showSelector)}
                    className="text-xs px-3 py-1 rounded-md text-white transition"
                    style={{ background: 'linear-gradient(135deg, #0B74B0, #75479C)' }}
                >
                    {showSelector ? 'Hide' : 'Add/Remove Companies'}
                </button>
            </div>

            {showSelector && (
                <div className="mb-4 p-3 bg-gray-50 rounded border max-h-40 overflow-y-auto">
                    <div className="text-xs font-semibold mb-2">Select Companies:</div>
                    <div className="grid grid-cols-2 gap-2">
                        {allCompanies.map(company => (
                            <label key={company} className="flex items-center text-xs cursor-pointer hover:bg-gray-100 p-1 rounded">
                                <input
                                    type="checkbox"
                                    checked={selectedCompanies.has(company)}
                                    onChange={() => toggleCompany(company)}
                                    disabled={isLoading}
                                    className="mr-2"
                                />
                                <span className="truncate" title={company}>{company}</span>
                            </label>
                        ))}
                    </div>
                </div>
            )}

            {chartData.length === 0 ? (
                <div className="h-[320px] flex items-center justify-center rounded-lg border border-dashed border-slate-300 bg-slate-50 text-sm text-slate-500">
                    No comparison data available for the selected companies.
                </div>
            ) : (
                <ResponsiveContainer width="100%" height={350}>
                    <BarChart data={chartData} margin={{ top: 5, right: 20, bottom: 80, left: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis
                            dataKey="name"
                            tick={{ fontSize: 11 }}
                            angle={-35}
                            textAnchor="end"
                            height={90}
                            interval={0}
                        />
                        <YAxis tick={{ fontSize: 11 }} />
                        <Tooltip
                            contentStyle={{ backgroundColor: 'white', border: '1px solid #cbd5e1', borderRadius: '8px' }}
                            formatter={(value: any) => [`${value} notifications`, 'Count']}
                        />
                        <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                            {chartData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            )}

            <div className="mt-2 text-xs text-gray-500 text-center">
                Showing {chartData.length} {chartData.length === 1 ? 'company' : 'companies'}
            </div>
        </div>
    );
};
