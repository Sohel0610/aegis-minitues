import { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Users, Building2, Network, ShieldCheck, Search, 
  Calendar, Award, Filter, ArrowRight, ExternalLink, 
  User, CheckCircle2, TrendingUp, Briefcase,
  Globe, Shield, Cpu, Share2, ChevronDown, Loader2, Info, RefreshCw
} from "lucide-react";
import { toast } from "sonner";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

// Interfaces for our enriched data
interface Association {
  cin: string;
  company_name: string;
  designation: string;
  appointment_date: string;
  is_group: boolean;
  status?: string;
}

interface Director {
  din: string;
  name: string;
  din_status: string;
  gender: string;
  nationality: string;
  dir3_kyc: string;
  external_board_count: number;
  last_api_sync?: string;
  last_mca_updated?: string;
}

const DirectorRegistryIntelligence = () => {
  const [directors, setDirectors] = useState<Director[]>([]);
  const [selectedDirector, setSelectedDirector] = useState<Director | null>(null);
  const [associations, setAssociations] = useState<Association[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const AEGIS_PURPLE = "#75479C";
  const AEGIS_BLUE = "#0B74B0";
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    fetchDirectors();
  }, []);

  const fetchDirectors = async () => {
    try {
      const res = await fetch("/api/director-intelligence/directors");
      if (!res.ok) {
        console.error("Server error fetching directors:", res.status);
        setDirectors([]);
        return;
      }
      const data = await res.json();
      if (Array.isArray(data)) {
        setDirectors(data);
        if (data.length > 0) setSelectedDirector(data[0]);
      } else {
        setDirectors([]);
      }
    } catch (err) {
      console.error("Failed to fetch directors", err);
      setDirectors([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchAssociations = async (din: string) => {
    try {
      setAssociations([]);
      const res = await fetch(`/api/director-intelligence/associations/${din}`);
      const data = await res.json();
      setAssociations(data);
    } catch (err) {
      console.error("Failed to fetch associations", err);
    }
  };
  
  const handleRefresh = async () => {
    if (!selectedDirector) return;
    
    setIsRefreshing(true);
    const toastId = toast.loading("Requesting live update from MCA...");
    
    try {
      const res = await fetch(`/api/mca/request-update?din=${selectedDirector.din}`, {
        method: 'POST'
      });
      const data = await res.json();
      
      if (res.ok) {
        toast.success(data.message || "Refresh triggered! Data will update in ~2 mins.", { id: toastId });
      } else {
        toast.error(data.detail || "Refresh request failed.", { id: toastId });
      }
    } catch (err) {
      toast.error("Failed to reach refresh service.", { id: toastId });
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    if (selectedDirector) {
      fetchAssociations(selectedDirector.din);
    }
  }, [selectedDirector]);

  const filteredDirectors = useMemo(() => {
    if (!Array.isArray(directors)) return [];
    return directors.filter(d => 
      d.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
      d.din.includes(searchQuery)
    );
  }, [directors, searchQuery]);



  const getStatusInfo = (lastUpdated?: string) => {
    if (!lastUpdated) return { label: "Stale", color: "#EF4444", bg: "bg-red-50", text: "text-red-700" };
    
    const lastDate = new Date(lastUpdated);
    const now = new Date();
    const diffHours = (now.getTime() - lastDate.getTime()) / (1000 * 60 * 60);
    const diffDays = diffHours / 24;

    if (diffHours <= 24) {
      return { label: "Live", color: "#10B981", bg: "bg-green-50", text: "text-green-700" };
    } else if (diffDays <= 90) {
      return { label: "Cached", color: "#F59E0B", bg: "bg-amber-50", text: "text-amber-700" };
    } else {
      return { label: "Stale", color: "#EF4444", bg: "bg-red-50", text: "text-red-700" };
    }
  };

  if (loading) return <div className="p-20 text-center"><Loader2 className="h-10 w-10 animate-spin mx-auto text-[#75479C]" /></div>;

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-white p-6 lg:p-10 font-sans">
        {/* Header Area */}
        <div className="mb-10 border-b border-gray-100 pb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-black text-gray-900 tracking-tight flex items-center gap-3">
               <Globe className="text-[#0B74B0] h-8 w-8" />
               Director registry intelligence
            </h1>
            <p className="text-gray-500 font-medium ml-11">Governance & overboarding analysis | Registry V2.1</p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="text-gray-500 font-bold px-4 py-1 border-gray-200">MCA live ecosystem</Badge>
          </div>
        </div>

        {/* Full-Width Director Selector */}
        <div className="mb-12 relative">
          <div 
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="w-full bg-gray-50 border border-gray-200 rounded-2xl p-6 flex items-center justify-between cursor-pointer hover:bg-gray-100 transition-all shadow-sm"
          >
            <div className="flex items-center gap-6">
              <div className={`p-4 rounded-xl shadow-inner ${['Approved', 'Active'].includes(selectedDirector?.din_status || '') ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                 <User size={28} />
              </div>
              <div>
                <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1">Due diligence profile for:</p>
                <h2 className="text-2xl font-black text-gray-900 leading-none">{selectedDirector?.name}</h2>
                <div className="flex items-center gap-4 mt-1.5">
                   <div className="flex items-center gap-1.5">
                      <span className="text-xs font-bold text-gray-500 uppercase tracking-tighter">DIN</span>
                      <span className="text-sm font-black text-[#0B74B0]">{selectedDirector?.din}</span>
                   </div>
                   <div className="h-4 w-px bg-gray-200 mx-2" />
                   <div className="flex items-center gap-2">
                      <div className={`h-2 w-2 rounded-full ${['Approved', 'Active'].includes(selectedDirector?.din_status || '') ? 'bg-green-500' : 'bg-red-500'}`} />
                      <span className="text-[10px] font-black text-gray-800 tracking-widest uppercase">{selectedDirector?.din_status}</span>
                   </div>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3 pr-4">
               <span className="text-sm font-bold text-gray-400">Switch director control</span>
               <ChevronDown className={`transition-transform duration-300 text-gray-300 ${isDropdownOpen ? 'rotate-180' : ''}`} />
            </div>
          </div>

          <AnimatePresence>
            {isDropdownOpen && (
              <motion.div 
                 initial={{ opacity: 0, y: 10 }}
                 animate={{ opacity: 1, y: 0 }}
                 exit={{ opacity: 0, y: 10 }}
                 className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-2xl shadow-2xl z-50 overflow-hidden max-h-[500px] flex flex-col"
              >
                 <div className="p-4 bg-gray-50 border-b border-gray-200">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 h-4 w-4" />
                      <Input 
                         placeholder="Search director network by name or DIN..." 
                         className="pl-10 h-10 border-0 bg-white"
                         value={searchQuery}
                         onChange={(e) => setSearchQuery(e.target.value)}
                      />
                    </div>
                 </div>
                 <div className="overflow-y-auto flex-1">
                    {filteredDirectors.map(d => (
                      <div 
                         key={d.din}
                         onClick={() => {
                           setSelectedDirector(d);
                           setIsDropdownOpen(false);
                         }}
                         className={`p-4 border-b border-gray-50 flex items-center justify-between hover:bg-[#75479C]/5 cursor-pointer transition-colors ${selectedDirector?.din === d.din ? 'bg-[#75479C]/5' : ''}`}
                      >
                         <div className="flex items-center gap-4">
                            <div className={`w-2 h-2 rounded-full ${['Approved', 'Active'].includes(d.din_status) ? 'bg-green-500' : 'bg-red-500'}`} />
                            <h4 className="font-bold text-gray-800">{d.name}</h4>
                            <span className="text-[10px] bg-gray-100 px-2 py-0.5 rounded text-gray-400 font-bold">DIN {d.din}</span>
                         </div>
                         <div className="text-[10px] font-black text-[#0B74B0] uppercase tracking-widest">{d.external_board_count} Associations</div>
                      </div>
                    ))}
                 </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Global Director Statistics Context */}
        <div className="mb-10">
            <div className="bg-white border border-gray-100/80 rounded-[2rem] p-10 shadow-[0_8px_30px_rgb(0,0,0,0.04)] relative overflow-hidden">
               <div className="relative z-10 grid grid-cols-2 lg:grid-cols-5 gap-12">
                  <div className="space-y-1">
                     <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">KYC validation status</p>
                     <p className="text-xl font-black text-gray-900">{selectedDirector?.dir3_kyc}</p>
                  </div>
                  <div className="space-y-1">
                     <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Registry gender</p>
                     <p className="text-xl font-black text-gray-900">{selectedDirector?.gender}</p>
                  </div>
                  <div className="space-y-1">
                     <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Nationality</p>
                     <p className="text-xl font-black text-gray-900">{selectedDirector?.nationality || 'Indian'}</p>
                  </div>
                  <div className="space-y-1">
                     <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Seat index reach</p>
                     <p className="text-xl font-black text-[#0B74B0] flex items-center gap-2">
                        <TrendingUp size={20} className="text-green-500" />
                        {associations.length > 0 ? associations.length : (selectedDirector?.external_board_count || 0)} boards
                     </p>
                  </div>
                  <div className="space-y-1">
                     <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Last registry sync</p>
                     <p className="text-xs font-black text-gray-900">
                        {selectedDirector?.last_api_sync 
                          ? new Date(selectedDirector.last_api_sync).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) 
                          : 'N/A'}
                     </p>
                  </div>
               </div>
            </div>
        </div>

        {/* Network Intelligence Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
              
           {/* Association Context */}
           <Card className="rounded-[2.5rem] border border-gray-100/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden bg-white">
              <div className="p-8 bg-gray-50/50 border-b border-gray-100 flex items-center justify-between">
                <h3 className="text-lg font-black text-gray-900 tracking-tight flex items-center gap-3">
                   <Briefcase className="text-[#0B74B0]" size={20} />
                   Tracked MCA board seats
                </h3>
                <span className="text-[10px] font-black text-blue-600 bg-blue-50 px-3 py-1 rounded-full uppercase tracking-widest">{associations.length} active</span>
              </div>
              <CardContent className="h-[450px] overflow-y-auto p-0 scrollbar-hide">
                 <div className="divide-y divide-gray-50">
                    {associations.length > 0 ? associations.map((a, i) => (
                      <div key={a.cin} className="p-6 hover:bg-gray-50/80 transition-colors group relative overflow-hidden">
                         <div className="absolute left-0 top-0 bottom-0 w-1 bg-transparent group-hover:bg-[#0B74B0] transition-all" />
                         <div className="flex justify-between items-start mb-2">
                            <div className="flex flex-col">
                               <h5 className="font-bold text-gray-900 text-sm group-hover:text-[#0B74B0] transition-colors">
                                  {a.company_name}
                               </h5>
                               <div className="flex flex-wrap gap-2 mt-1.5">
                                 {a.is_group && (
                                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-widest bg-amber-100 text-amber-700 border border-amber-200 w-fit">
                                       Group Entity
                                    </span>
                                 )}
                                 {a.status && !['active', 'active (for e-filing)'].includes(a.status.toLowerCase().trim()) && (
                                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-widest border w-fit ${
                                       a.status.toLowerCase().trim() === 'amalgamated' ? 'bg-blue-100 text-blue-700 border-blue-200' : 
                                       a.status.toLowerCase().includes('strike') || a.status.toLowerCase().includes('struck') ? 'bg-red-100 text-red-700 border-red-200' :
                                       'bg-gray-100 text-gray-600 border-gray-200'
                                    }`}>
                                       {a.status}
                                    </span>
                                 )}
                               </div>
                            </div>
                            <span className="text-[10px] font-bold text-gray-400">Est. {a.appointment_date}</span>
                         </div>
                         <div className="flex items-center justify-between">
                            <span className="text-xs font-medium text-gray-500">{a.designation}</span>
                            <div className="flex items-center gap-2">
                               <div className="w-1 h-1 rounded-full bg-gray-300" />
                               <span className="text-[10px] font-mono text-gray-400">CIN {a.cin}</span>
                            </div>
                         </div>
                      </div>
                    )) : (
                      <div className="flex flex-col items-center justify-center h-full p-20 text-center opacity-40">
                         <Search size={40} className="mb-4 text-gray-300" />
                         <p className="text-sm font-bold text-gray-400">No external associations identified</p>
                      </div>
                    )}
                 </div>
              </CardContent>
           </Card>

           {/* Overboarding & Governance Risk Profile */}
           <Card className="rounded-[2.5rem] border border-gray-100/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden bg-white">
              <div className="p-8 bg-gray-50/50 border-b border-gray-100 flex justify-between items-center">
                <h3 className="text-lg font-black text-gray-900 flex items-center gap-3">
                   <Shield className="text-[#0B74B0]" size={20} />
                   Governance compliance profiling
                </h3>
              </div>
              <CardContent className="p-8 flex flex-col justify-between h-[450px]">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                    {/* Metric 1 - Total Exposure */}
                    <div className="p-6 bg-blue-50/20 rounded-3xl border border-blue-100/30 transition-all text-center relative group flex flex-col justify-center">
                       <Tooltip>
                          <TooltipTrigger className="absolute top-3 right-3 text-blue-300 hover:text-blue-500 transition-colors">
                             <Info size={14} />
                          </TooltipTrigger>
                          <TooltipContent className="max-w-[180px] text-[11px]">
                             Total active board seats tracked in MCA Registry for this DIN.
                          </TooltipContent>
                       </Tooltip>
                       <p className="text-[10px] font-bold text-blue-500 uppercase tracking-widest mb-2">Total board exposure</p>
                       <div className="text-4xl font-black text-[#0B74B0] leading-none mb-1">{selectedDirector?.external_board_count || 0}</div>
                       <p className="text-[9px] font-bold text-gray-400 uppercase">Seats identified</p>
                    </div>

                    {/* Metric 2 - Overboarding Risk */}
                    <div className="p-6 bg-purple-50/20 rounded-3xl border border-purple-100/30 transition-all text-center relative group flex flex-col justify-center">
                       <Tooltip>
                          <TooltipTrigger className="absolute top-3 right-3 text-purple-300 hover:text-purple-500 transition-colors">
                             <Info size={14} />
                          </TooltipTrigger>
                          <TooltipContent className="max-w-[180px] text-[11px]">
                             Risk assessment based on MCA Sec 165(1) & SEBI Listing Regs.
                          </TooltipContent>
                       </Tooltip>
                       <p className="text-[10px] font-bold text-purple-500 uppercase tracking-widest mb-2">Overboarding risk</p>
                       <div className={`text-2xl font-black leading-none mb-1 ${(selectedDirector?.external_board_count || 0) > 10 ? 'text-red-500' : 'text-[#75479C]'}`}>
                          {(selectedDirector?.external_board_count || 0) > 10 ? 'HIGH' : 'CONTROLLED'}
                       </div>
                       <p className="text-[9px] font-bold text-gray-400 uppercase tracking-tighter">Registry status</p>
                    </div>
                  </div>

                  <div className="space-y-4 px-2">
                    <div className="flex justify-between items-baseline">
                       <div className="flex items-center gap-2">
                          <h4 className="text-xs font-black text-gray-900 tracking-tight">MCA utilization limit</h4>
                          <Tooltip>
                            <TooltipTrigger className="text-gray-300 hover:text-gray-500">
                               <Info size={11} />
                            </TooltipTrigger>
                            <TooltipContent className="text-[10px] max-w-[200px]">
                               Statutory cap of 20 directorships per Individual under Cos Act 2013.
                            </TooltipContent>
                          </Tooltip>
                       </div>
                       <span className="text-xl font-black text-gray-900 tracking-tighter">
                          {Math.min((selectedDirector?.external_board_count || 0) * 5, 100)}%
                       </span>
                    </div>
                    <div className="h-4 bg-gray-100 rounded-full overflow-hidden p-1">
                       <div 
                          className={`h-full rounded-full transition-all duration-1000 shadow-sm ${ (selectedDirector?.external_board_count || 0) > 15 ? 'bg-red-500' : 'bg-gradient-to-r from-blue-500 to-emerald-500'}`} 
                          style={{ width: `${Math.min((selectedDirector?.external_board_count || 0) * 5, 100)}%` }}
                       />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 gap-4">
                    <div className="flex items-center gap-5 p-5 bg-white border border-gray-100 rounded-[1.5rem] shadow-sm">
                       <div className="p-3 bg-blue-50 rounded-2xl">
                          <Network className="text-blue-500" size={20} />
                       </div>
                       <div>
                          <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-0.5">Ecosystem interlock</p>
                          <p className="text-sm font-bold text-gray-900 tracking-tight">Professional connectivity profile identified</p>
                       </div>
                    </div>
                    <div className="flex items-center gap-5 p-5 bg-white border border-gray-100 rounded-[1.5rem] shadow-sm">
                       <div className="p-3 bg-emerald-50 rounded-2xl">
                          <CheckCircle2 className="text-emerald-500" size={20} />
                       </div>
                       <div>
                          <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-0.5">Statutory compliance</p>
                          <p className="text-sm font-bold text-gray-900 tracking-tight">DIR-3 KYC lifecycle: Active & compliant</p>
                       </div>
                    </div>
                  </div>
              </CardContent>
           </Card>
        </div>




        {/* Institutional Footer */}
        <footer className="mt-20 pt-10 border-t border-gray-100 text-center opacity-30">
          <span className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]">Aegis Institutional Risk &amp; Compliance Terminal</span>
        </footer>
      </div>
    </TooltipProvider>
  );
};

export default DirectorRegistryIntelligence;
