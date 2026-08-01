import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import { Building2, Search, Loader2, AlertCircle, Filter, ChevronDown, FileText, Download, CheckCircle2, XCircle, Clock } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle,
  DialogFooter 
} from "@/components/ui/dialog";

interface Company {
  name: string;
  cin: string;
  type: string;
  director_count: number;
  is_group: boolean;
}

interface CompanyComplianceStatus {
  din: string;
  name: string;
  designation?: string;
  appointment_date?: string;
  dir8_status: "Filed" | "Pending";
  mbp1_status: "Filed" | "Pending";
  dir8_file: string | null;
  mbp1_file: string | null;
  last_updated: string;
  is_adani?: boolean;
}

interface CompanyComplianceResponse {
  company_name: string;
  year: string;
  directors: CompanyComplianceStatus[];
}

const DirectorsDisclosureCompaniesMasterData = () => {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [filteredCompanies, setFilteredCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<string>("name");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");

  // Compliance Tracker State
  const [isComplianceModalOpen, setIsComplianceModalOpen] = useState<boolean>(false);
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [complianceData, setComplianceData] = useState<CompanyComplianceResponse | null>(null);
  const [complianceLoading, setComplianceLoading] = useState<boolean>(false);
  const [bulkDownloadLoading, setBulkDownloadLoading] = useState<boolean>(false);

  useEffect(() => {
    fetchCompanies();
  }, []);

  useEffect(() => {
    let result = [...companies];
    
    // Apply search filter
    if (searchTerm.trim() !== "") {
      const term = searchTerm.toLowerCase();
      result = result.filter(
        (company) =>
          company.name.toLowerCase().includes(term) ||
          company.cin.toLowerCase().includes(term) ||
          company.type.toLowerCase().includes(term)
      );
    }
    
    // Apply type filter
    if (typeFilter !== "all") {
      result = result.filter((company) => company.type === typeFilter);
    }

    // Apply category filter
    if (categoryFilter !== "all") {
      const isGroupSearch = categoryFilter === "group";
      result = result.filter((company) => company.is_group === isGroupSearch);
    }
    
    // Apply sorting
    result.sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case "name":
          comparison = a.name.localeCompare(b.name);
          break;
        case "type":
          comparison = a.type.localeCompare(b.type);
          break;
        case "director_count":
          comparison = a.director_count - b.director_count;
          break;
        default:
          comparison = 0;
      }
      
      return sortOrder === "asc" ? comparison : -comparison;
    });
    
    setFilteredCompanies(result);
  }, [searchTerm, typeFilter, categoryFilter, sortBy, sortOrder, companies]);

  const fetchCompanies = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('/api/companies-with-director-count');
      
      if (!response.ok) {
        throw new Error('Failed to fetch companies');
      }
      
      const data = await response.json();
      setCompanies(data || []);
    } catch (err) {
      console.error('Error fetching companies:', err);
      setError(err instanceof Error ? err.message : 'Failed to load companies');
    } finally {
      setLoading(false);
    }
  };

  const fetchComplianceStatus = async (company: Company) => {
    try {
      setSelectedCompany(company);
      setIsComplianceModalOpen(true);
      setComplianceLoading(true);
      
      const response = await fetch(`/api/disclosures/company/${company.cin}/status`);
      if (response.ok) {
        const data = await response.json();
        setComplianceData(data);
      } else {
        throw new Error('Failed to fetch compliance status');
      }
    } catch (err) {
      console.error('Error fetching compliance:', err);
      setComplianceData(null);
    } finally {
      setComplianceLoading(false);
    }
  };

  const handleBulkDownload = async () => {
    if (!selectedCompany) return;
    
    try {
      setBulkDownloadLoading(true);
      const response = await fetch(`/api/disclosures/company/${selectedCompany.cin}/bulk-download`);
      
      if (!response.ok) throw new Error('Download failed');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedCompany.name.replace(/\s+/g, '_')}_Compliance_Pack.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Bulk download error:', err);
      alert('Failed to generate compliance pack. Ensure documents are generated first.');
    } finally {
      setBulkDownloadLoading(false);
    }
  };

  const handleDownloadFile = (filePath: string) => {
    const url = `/api/disclosures/download/file?path=${encodeURIComponent(filePath)}`;
    window.open(url, '_blank');
  };

  const uniqueTypes = useMemo(() => {
    const types = new Set(companies.map(company => company.type));
    return Array.from(types).sort();
  }, [companies]);

  const publicCount = useMemo(() => {
    return companies.filter(company => company.type === 'Public').length;
  }, [companies]);

  const privateCount = useMemo(() => {
    return companies.filter(company => company.type.includes('Private')).length;
  }, [companies]);

  const groupCount = useMemo(() => {
    return companies.filter(company => company.is_group).length;
  }, [companies]);

  const externalCount = useMemo(() => {
    return companies.filter(company => !company.is_group).length;
  }, [companies]);

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(column);
      setSortOrder("asc");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "#ffffff" }}>
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4" style={{ color: "#75479C" }} />
          <p className="text-lg" style={{ color: "#000000" }}>Loading companies...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "#ffffff" }}>
        <div className="text-center p-6 max-w-md">
          <AlertCircle className="h-12 w-12 mx-auto mb-4" style={{ color: "#EF4444" }} />
          <h2 className="text-xl font-bold mb-2" style={{ color: "#000000" }}>Error Loading Data</h2>
          <p className="mb-4" style={{ color: "#000000" }}>{error}</p>
          <Button onClick={fetchCompanies} style={{ backgroundColor: '#75479C', color: 'white' }}>
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6" style={{ background: "#ffffff" }}>
      <motion.div
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Card className="border-0 shadow-lg" style={{ borderTop: '4px solid #75479C' }}>
          <CardHeader>
            <div className="flex items-center gap-3 mb-4">
              <Building2 className="h-8 w-8" style={{ color: "#75479C" }} />
              <div>
                <CardTitle className="text-2xl font-bold" style={{ color: "#000000" }}>
                  Companies Master List
                </CardTitle>
                <CardDescription style={{ color: '#666666' }}>
                  Complete list of all 621 companies categorized by type with director counts
                </CardDescription>
              </div>
            </div>

            {/* Filters and Search */}
            <div className="flex flex-wrap gap-4 items-center">
              <div className="flex-1 min-w-[300px] relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search by company name or CIN..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 h-11 border-gray-200 rounded-xl focus:ring-[#75479C] focus:border-[#75479C] shadow-sm bg-white"
                />
              </div>
              
              <div className="flex gap-2">
                <div className="relative">
                  <select
                    value={categoryFilter}
                    onChange={(e) => setCategoryFilter(e.target.value)}
                    className="h-11 px-4 pr-10 border border-gray-200 rounded-xl bg-white text-sm font-bold text-gray-700 appearance-none focus:outline-none focus:ring-2 focus:ring-[#75479C]/20 shadow-sm min-w-[160px]"
                  >
                    <option value="all">All Categories</option>
                    <option value="group">Group Entities</option>
                    <option value="external">External</option>
                  </select>
                  <Filter className="absolute right-3 top-1/2 -translate-y-1/2 h-3 w-3 text-gray-400 pointer-events-none" />
                </div>

                <div className="relative">
                  <select
                    value={typeFilter}
                    onChange={(e) => setTypeFilter(e.target.value)}
                    className="h-11 px-4 pr-10 border border-gray-200 rounded-xl bg-white text-sm font-bold text-gray-700 appearance-none focus:outline-none focus:ring-2 focus:ring-[#75479C]/20 shadow-sm min-w-[160px]"
                  >
                    <option value="all">All Types</option>
                    <option value="Public">Public</option>
                    <option value="Private">Private</option>
                  </select>
                  <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-3 w-3 text-gray-400 pointer-events-none" />
                </div>

                <Button
                  onClick={() => {
                    setSearchTerm("");
                    setTypeFilter("all");
                    setCategoryFilter("all");
                  }}
                  variant="ghost"
                  className="h-11 px-4 text-gray-500 hover:text-red-600 font-bold text-sm"
                >
                  Reset
                </Button>
              </div>
            </div>
          </CardHeader>

<CardContent>
              <div className="rounded-2xl border border-gray-100 overflow-hidden shadow-sm">
                <Table>
                  <TableHeader className="bg-gray-50/80">
                    <TableRow>
                      <TableHead className="py-5 pl-4 text-[10px] font-black text-gray-900 uppercase tracking-widest w-[50px]">#</TableHead>
                      <TableHead
                        className="font-black text-gray-900 cursor-pointer hover:bg-gray-100 py-4"
                        onClick={() => handleSort("name")}
                      >
                        <div className="flex items-center">
                          Company Name
                          {sortBy === "name" && (
                            <span className="ml-1">
                              {sortOrder === "asc" ? "↑" : "↓"}
                            </span>
                          )}
                        </div>
                      </TableHead>
                      <TableHead className="font-black text-gray-900">CIN</TableHead>
                      <TableHead className="font-black text-gray-900">Type</TableHead>
                      <TableHead className="font-black text-gray-900 min-w-[140px]">Category</TableHead>
                      <TableHead
                        className="font-black text-gray-900 text-right cursor-pointer hover:bg-gray-100"
                        onClick={() => handleSort("director_count")}
                      >
                        <div className="flex items-center justify-end">
                          Directors
                          {sortBy === "director_count" && (
                            <span className="ml-1">
                              {sortOrder === "asc" ? "↑" : "↓"}
                            </span>
                          )}
                        </div>
                      </TableHead>
                      <TableHead className="font-black text-gray-900 text-right pr-6">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                <TableBody>
                  {filteredCompanies.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8" style={{ color: '#666666' }}>
                        {searchTerm || typeFilter !== "all" || categoryFilter !== "all" ? 'No companies found matching your filters' : 'No companies found'}
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredCompanies.map((company, index) => (
                      <TableRow key={index} className="hover:bg-gray-50">
                        <TableCell className="font-medium" style={{ color: '#666666' }}>
                          {index + 1}
                        </TableCell>
                        <TableCell className="font-medium">{company.name}</TableCell>
                        <TableCell className="font-mono text-xs text-gray-500">{company.cin}</TableCell>
                        <TableCell>
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            company.type === 'Public' 
                              ? 'bg-blue-100 text-blue-800' 
                              : company.type === 'Private - Subsidiary of Public'
                              ? 'bg-purple-100 text-purple-800'
                              : 'bg-pink-100 text-pink-800'
                          }`}>
                            {company.type}
                          </span>
                        </TableCell>
                        <TableCell>
                          <div className="flex justify-start">
                            <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest whitespace-nowrap border ${
                              company.is_group 
                                ? 'bg-amber-50 text-amber-700 border-amber-200 shadow-sm' 
                                : 'bg-gray-50 text-gray-500 border-gray-200'
                            }`}>
                              {company.is_group ? 'Group Entity' : 'External'}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell className="text-right font-medium" style={{ color: '#75479C' }}>
                          {company.director_count}
                        </TableCell>
                        <TableCell className="text-right">
                            <Button
                              size="sm"
                              variant="ghost"
                              className="text-[#75479C] hover:bg-purple-50 font-bold"
                              onClick={() => fetchComplianceStatus(company)}
                            >
                              <FileText className="h-4 w-4 mr-2" />
                              Compliance
                            </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>

            {/* Summary Stats */}
            <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card className="bg-purple-50/50 border-purple-100 shadow-sm">
                <CardContent className="pt-6">
                  <div className="text-center">
                    <div className="text-2xl font-black text-[#75479C]">
                      {groupCount}
                    </div>
                    <div className="text-[10px] font-black text-gray-500 uppercase tracking-widest mt-1">
                      Group Entities
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-gray-50/50 border-gray-100 shadow-sm">
                <CardContent className="pt-6">
                  <div className="text-center">
                    <div className="text-2xl font-black text-gray-700">
                      {externalCount}
                    </div>
                    <div className="text-[10px] font-black text-gray-500 uppercase tracking-widest mt-1">
                      External Associates
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-blue-50/50 border-blue-100 shadow-sm">
                <CardContent className="pt-6">
                  <div className="text-center">
                    <div className="text-2xl font-black text-[#0B74B0]">
                      {publicCount}
                    </div>
                    <div className="text-[10px] font-black text-gray-500 uppercase tracking-widest mt-1">
                      Public Listed
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-pink-50/50 border-pink-100 shadow-sm">
                <CardContent className="pt-6">
                  <div className="text-center">
                    <div className="text-2xl font-black text-[#BD3861]">
                      {privateCount}
                    </div>
                    <div className="text-[10px] font-black text-gray-500 uppercase tracking-widest mt-1">
                      Private / Subs
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Compliance Tracker Modal */}
      <Dialog open={isComplianceModalOpen} onOpenChange={setIsComplianceModalOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto bg-white">
          <DialogHeader className="border-b pb-4">
            <div className="flex items-center justify-between">
              <div>
                <DialogTitle className="text-2xl font-black text-gray-900">
                  Compliance Tracker
                </DialogTitle>
                <DialogDescription className="text-gray-500">
                  {selectedCompany?.name} • FY 2024-25
                </DialogDescription>
              </div>
              {selectedCompany?.is_group && complianceData && (
                <Button 
                  onClick={handleBulkDownload} 
                  disabled={bulkDownloadLoading}
                  className="bg-[#75479C] hover:bg-[#633b85] text-white"
                >
                  {bulkDownloadLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  ) : (
                    <Download className="h-4 w-4 mr-2" />
                  )}
                  Bulk Download ZIP
                </Button>
              )}
            </div>
          </DialogHeader>

          {complianceLoading ? (
            <div className="py-20 text-center">
              <Loader2 className="h-10 w-10 animate-spin mx-auto text-[#75479C] mb-4" />
              <p className="text-gray-500">Scanning disclosure repository...</p>
            </div>
          ) : complianceData ? (
            <div className="py-4">
              {selectedCompany?.is_group && (
                <div className="bg-purple-50/50 p-4 rounded-xl border border-purple-100 mb-6 flex items-center justify-between">
                  <div className="flex gap-8">
                    <div>
                      <p className="text-[10px] uppercase font-black text-purple-400 tracking-wider">Board Size</p>
                      <p className="text-xl font-black text-purple-900">{complianceData.directors.length}</p>
                    </div>
                    <div>
                      <p className="text-[10px] uppercase font-black text-purple-400 tracking-wider">Filed</p>
                      <p className="text-xl font-black text-green-600">
                        {complianceData.directors.filter(d => d.dir8_status === 'Filed' && d.mbp1_status === 'Filed').length}
                      </p>
                    </div>
                    <div>
                      <p className="text-[10px] uppercase font-black text-purple-400 tracking-wider">Pending</p>
                      <p className="text-xl font-black text-red-500">
                        {complianceData.directors.filter(d => d.dir8_status === 'Pending' || d.mbp1_status === 'Pending').length}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <div className="rounded-xl border border-gray-200 overflow-hidden shadow-sm">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-gray-50">
                      <TableHead className="font-bold">Director Name</TableHead>
                      <TableHead className="font-bold text-center">DIR-8</TableHead>
                      <TableHead className="font-bold text-center">MBP-1</TableHead>
                      <TableHead className="font-bold text-center">Last Updated</TableHead>
                      <TableHead className="text-right font-bold">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {complianceData.directors.map((d) => (
                      <TableRow key={d.din} className="hover:bg-gray-50 transition-colors">
                        <TableCell>
                          <div>
                            <div className="flex items-center gap-2">
                              <p className="font-bold text-gray-900">{d.name}</p>
                              <span className={`px-1.5 py-0.5 rounded text-[8px] font-black uppercase tracking-wider ${
                                d.is_adani 
                                  ? 'bg-amber-50 text-amber-700 border border-amber-200' 
                                  : 'bg-gray-50 text-gray-400 border border-gray-100'
                              }`}>
                                {d.is_adani ? 'Group' : 'External'}
                              </span>
                            </div>
                            <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[10px] text-gray-400 mt-0.5">
                              <span className="font-mono">DIN: {d.din}</span>
                              {d.designation && (
                                <>
                                  <span className="text-gray-300 font-normal">•</span>
                                  <span className="font-medium text-purple-600 bg-purple-50 px-1 py-0.25 rounded">{d.designation}</span>
                                </>
                              )}
                              {d.appointment_date && d.appointment_date !== "N/A" && (
                                <>
                                  <span className="text-gray-300 font-normal">•</span>
                                  <span>Appointed: {d.appointment_date}</span>
                                </>
                              )}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell className="text-center">
                          {d.is_adani ? (
                            <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-[10px] font-black uppercase tracking-tight ${
                              d.dir8_status === 'Filed' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'
                            }`}>
                              {d.dir8_status === 'Filed' ? <CheckCircle2 className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                              {d.dir8_status}
                            </span>
                          ) : (
                            <span className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">N/A</span>
                          )}
                        </TableCell>
                        <TableCell className="text-center">
                          {d.is_adani ? (
                            <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-[10px] font-black uppercase tracking-tight ${
                              d.mbp1_status === 'Filed' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'
                            }`}>
                              {d.mbp1_status === 'Filed' ? <CheckCircle2 className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                              {d.mbp1_status}
                            </span>
                          ) : (
                            <span className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">N/A</span>
                          )}
                        </TableCell>
                        <TableCell className="text-center text-gray-500 text-xs">
                          {d.is_adani ? (
                            <div className="flex items-center justify-center gap-1">
                              <Clock className="h-3 w-3 opacity-40" />
                              {d.last_updated}
                            </div>
                          ) : (
                            <span className="text-gray-400">—</span>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1">
                            {d.is_adani ? (
                              <>
                                {d.dir8_file && (
                                  <Button 
                                    size="sm" 
                                    variant="ghost" 
                                    className="h-8 w-8 p-0 text-blue-600"
                                    title="Download DIR-8"
                                    onClick={() => handleDownloadFile(d.dir8_file!)}
                                  >
                                    <Download className="h-4 w-4" />
                                  </Button>
                                )}
                                {d.mbp1_file && (
                                  <Button 
                                    size="sm" 
                                    variant="ghost" 
                                    className="h-8 w-8 p-0 text-green-600"
                                    title="Download MBP-1"
                                    onClick={() => handleDownloadFile(d.mbp1_file!)}
                                  >
                                    <Download className="h-4 w-4" />
                                  </Button>
                                )}
                              </>
                            ) : (
                              <span className="text-[10px] text-gray-400 italic">View Only</span>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          ) : (
            <div className="py-20 text-center">
              <AlertCircle className="h-10 w-10 mx-auto text-amber-500 mb-4" />
              <p className="text-gray-900 font-bold">No Records Found</p>
              <p className="text-gray-500 text-sm max-w-xs mx-auto">
                No disclosure documents have been generated for this company's board yet.
              </p>
            </div>
          )}

          <DialogFooter className="border-t pt-4">
            <Button variant="outline" onClick={() => setIsComplianceModalOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <footer className="mt-20 pt-10 border-t border-gray-100 text-center opacity-30">
        <span className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]">Aegis Institutional Risk & Compliance Terminal</span>
      </footer>
    </div>
  );
};

export default DirectorsDisclosureCompaniesMasterData;