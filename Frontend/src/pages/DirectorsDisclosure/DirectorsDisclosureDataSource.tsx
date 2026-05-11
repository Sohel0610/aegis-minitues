import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { FileText, Eye, Download, Loader2, AlertCircle, Users, Search, Check, ChevronDown, Building, History, Calendar, Clock, ArrowRight } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import FamilyInfoModal from "./FamilyInfoModal";

interface Disclosure {
  id: number;
  director_name: string;
  din: string;
  pan?: string;
  din_status?: string;
  disclosure_date: string;
  disclosure_type: string;
  is_kmp?: boolean;
  file_path: string;
  all_files?: {
    path: string;
    company_hint: string;
    folder_name: string;
    type: string;
    date: string;
  }[];
}


const DirectorsDisclosureDataSource = () => {
  const [disclosures, setDisclosures] = useState<Disclosure[]>([]);
  const [filteredDisclosures, setFilteredDisclosures] = useState<Disclosure[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDisclosure, setSelectedDisclosure] = useState<Disclosure | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [isFamilyInfoModalOpen, setIsFamilyInfoModalOpen] = useState<boolean>(false);
  const [isHistoryModalOpen, setIsHistoryModalOpen] = useState<boolean>(false);
  const [historyDisclosure, setHistoryDisclosure] = useState<Disclosure | null>(null);
  const [selectedDirectorName, setSelectedDirectorName] = useState<string>("");
  const [selectedDirectorDin, setSelectedDirectorDin] = useState<string>("");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [isTemplateModalOpen, setIsTemplateModalOpen] = useState<boolean>(false);
  const [kmpFilter, setKmpFilter] = useState<'all' | 'yes' | 'no'>('all');

  useEffect(() => {
    fetchDisclosures();
  }, []);

  useEffect(() => {
    let result = [...disclosures];
    
    // Apply search filter
    if (searchTerm.trim() !== "") {
      const term = searchTerm.toLowerCase();
      result = result.filter(
        (disclosure) =>
          disclosure.director_name.toLowerCase().includes(term) ||
          disclosure.din.includes(term) ||
          disclosure.disclosure_date.includes(term)
      );
    }

    // Apply KMP filter
    if (kmpFilter === 'yes') {
      result = result.filter(d => d.is_kmp);
    } else if (kmpFilter === 'no') {
      result = result.filter(d => !d.is_kmp);
    }
    
    // Default Alphabetical Sort (A-Z)
    result.sort((a, b) => a.director_name.localeCompare(b.director_name));
    
    setFilteredDisclosures(result);
  }, [searchTerm, disclosures, kmpFilter]);

  const fetchDisclosures = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('/api/directors-disclosures');

      if (!response.ok) {
        throw new Error('Failed to fetch disclosures');
      }

      const data = await response.json();
      setDisclosures(data.data || []);
      setFilteredDisclosures(data.data || []);
    } catch (err) {
      console.error('Error fetching disclosures:', err);
      setError(err instanceof Error ? err.message : 'Failed to load disclosures');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadDisclosure = async (disclosure: Disclosure, specificPath?: string) => {
    try {
      const filePath = specificPath || disclosure.file_path;
      if (!filePath) {
        throw new Error('No file path associated with this record.');
      }

      // Encode the file path for the direct downloader
      const downloadUrl = `/api/disclosures/download/file?path=${encodeURIComponent(filePath)}`;
      
      // We use the same fetch/blob method for deployment reliability
      const response = await fetch(downloadUrl);
      
      if (!response.ok) {
        throw new Error('File not found on server. Ensure it has been generated.');
      }

      const blob = await response.blob();
      const filename = filePath.split(/[\\/]/).pop() || `${disclosure.director_name}_disclosure.docx`;
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error downloading disclosure:', err);
      alert(err instanceof Error ? err.message : 'Could not download file.');
    }
  };


  const handleViewHistory = (disclosure: Disclosure) => {
    setHistoryDisclosure(disclosure);
    setIsHistoryModalOpen(true);
  };

  const handleViewFamilyInfo = (directorName: string, din: string) => {
    setSelectedDirectorName(directorName);
    setSelectedDirectorDin(din);
    setIsFamilyInfoModalOpen(true);
  };

  const handleDownloadTemplate = async (templateName: string) => {
    try {
      const downloadUrl = `/api/directors-disclosures/templates/${templateName}`;

      // Create a temporary link and trigger download
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = templateName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.error('Error downloading template:', err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "#ffffff" }}>
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4" style={{ color: "#75479C" }} />
          <p className="text-lg" style={{ color: "#000000" }}>Loading disclosures...</p>
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
          <Button
            onClick={fetchDisclosures}
            style={{
              backgroundColor: '#75479C',
              borderColor: '#75479C',
              color: 'white'
            }}
          >
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
        <Card className="rounded-[2rem] border border-gray-100/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden bg-white mb-8">
          <CardHeader className="p-8 border-b border-gray-50 bg-gray-50/10">
            <div className="flex items-center gap-4 mb-8">
              <FileText className="h-9 w-9 text-[#75479C]" />
              <div>
                <CardTitle className="text-3xl font-black text-gray-900 tracking-tight">
                  Disclosure Repository
                </CardTitle>
                <CardDescription className="text-gray-500 font-medium">
                  Central archives of all statutory filings, AI summaries, and registry snapshots
                </CardDescription>
              </div>
            </div>

            <div className="flex flex-col md:flex-row items-center gap-4">
              <Button
                variant="outline"
                onClick={() => setIsTemplateModalOpen(true)}
                className="h-14 px-8 rounded-2xl border-gray-100 text-[#75479C] font-bold flex gap-3 hover:bg-gray-50 transition-all w-full md:w-auto"
              >
                <Download size={20} />
                Download templates
              </Button>
              <div className="relative flex-1 w-full">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <Input
                  placeholder="Search disclosures by name, DIN or date..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-12 h-14 rounded-2xl border-gray-100 bg-gray-50 focus:bg-white transition-all text-lg"
                />
              </div>
            </div>

            {/* KMP Filter Toggles */}
            <div className="flex items-center gap-2 mt-6">
              <span className="text-[10px] font-black uppercase text-gray-400 tracking-widest mr-2">Filter by KMP:</span>
              <div className="flex bg-gray-100/50 p-1 rounded-xl border border-gray-100">
                <button
                  onClick={() => setKmpFilter('all')}
                  className={`px-4 py-1.5 rounded-lg text-[10px] font-black tracking-widest uppercase transition-all ${
                    kmpFilter === 'all' 
                      ? 'bg-white text-[#75479C] shadow-sm' 
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  All
                </button>
                <button
                  onClick={() => setKmpFilter('yes')}
                  className={`px-4 py-1.5 rounded-lg text-[10px] font-black tracking-widest uppercase transition-all ${
                    kmpFilter === 'yes' 
                      ? 'bg-purple-600 text-white shadow-md' 
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  KMP (Yes)
                </button>
                <button
                  onClick={() => setKmpFilter('no')}
                  className={`px-4 py-1.5 rounded-lg text-[10px] font-black tracking-widest uppercase transition-all ${
                    kmpFilter === 'no' 
                      ? 'bg-white text-gray-900 shadow-sm border border-gray-200' 
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Non-KMP (No)
                </button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="mb-4 text-sm" style={{ color: '#666666' }}>
              Showing {filteredDisclosures.length} of {disclosures.length} disclosures
            </div>
            <div className="rounded-[1.5rem] border border-gray-100 overflow-hidden shadow-sm">
              <Table>
                <TableHeader>
                  <TableRow className="bg-gray-50 active:bg-gray-50">
                    <TableHead className="py-5 pl-8 text-[10px] font-black text-gray-900 uppercase tracking-widest w-[60px]">#</TableHead>
                    <TableHead className="py-5 text-[10px] font-black text-gray-900 uppercase tracking-widest">Director name</TableHead>
                    <TableHead className="py-5 text-[10px] font-black text-gray-900 uppercase tracking-widest">DIN</TableHead>
                    <TableHead className="py-5 text-[10px] font-black text-gray-900 uppercase tracking-widest text-center">Whether already a KMP?</TableHead>
                    <TableHead className="py-5 text-[10px] font-black text-gray-900 uppercase tracking-widest">Document type</TableHead>
                    <TableHead className="py-5 text-[10px] font-black text-gray-900 uppercase tracking-widest text-center">Status</TableHead>
                    <TableHead className="py-5 text-[10px] font-black text-gray-900 uppercase tracking-widest text-center">Last Updated</TableHead>
                    <TableHead className="py-5 pr-8 text-[10px] font-black text-gray-900 uppercase tracking-widest text-right">Controls</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredDisclosures.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center py-8" style={{ color: '#666666' }}>
                        {searchTerm ? 'No disclosures found matching your search' : 'No disclosures found'}
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredDisclosures.map((disclosure, index) => (
                      <TableRow key={disclosure.id} className="hover:bg-gray-50">
                        <TableCell className="pl-8 text-xs font-bold text-gray-400">{index + 1}</TableCell>
                        <TableCell className="font-semibold text-gray-900">{disclosure.director_name}</TableCell>
                        <TableCell className="font-mono text-xs text-gray-500">{disclosure.din}</TableCell>
                        <TableCell className="text-center">
                          <div className={`inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-black tracking-widest uppercase shadow-sm border ${
                            disclosure.is_kmp
                              ? 'bg-purple-50 text-purple-700 border-purple-200' 
                              : 'bg-gray-50 text-gray-500 border-gray-200'
                          }`}>
                            {disclosure.is_kmp ? (
                              <><span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-purple-500"></span>YES</>
                            ) : (
                              'Non-KMP'
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <span className={`px-2 py-1 rounded text-[10px] font-black uppercase tracking-wider ${
                            disclosure.disclosure_type === 'Registry Sync' 
                              ? 'bg-blue-50 text-blue-700' 
                              : 'bg-purple-50 text-purple-700'
                          }`}>
                            {disclosure.disclosure_type}
                          </span>
                        </TableCell>
                        <TableCell className="text-center">
                          {disclosure.din_status && disclosure.din_status !== 'Sync Pending' ? (
                            <Badge 
                              variant="outline" 
                              className={['Approved', 'Active'].includes(disclosure.din_status) 
                                ? 'bg-green-50 text-green-700 border-green-200' 
                                : 'bg-red-50 text-red-700 border-red-200'}
                            >
                              {disclosure.din_status}
                            </Badge>
                          ) : (
                            <span className="text-gray-400 italic text-xs">Sync Pending</span>
                          )}
                        </TableCell>
                        <TableCell className="font-medium text-center text-gray-600">{disclosure.disclosure_date}</TableCell>
                        <TableCell className="text-right pr-8">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => disclosure.all_files && disclosure.all_files.length > 1 
                              ? handleViewHistory(disclosure) 
                              : handleDownloadDisclosure(disclosure)}
                            disabled={!disclosure.file_path}
                            className={`gap-2 font-bold ${
                              disclosure.file_path 
                                ? 'text-[#0B74B0] hover:text-[#0B74B0] hover:bg-blue-50' 
                                : 'text-gray-300 cursor-not-allowed'
                            }`}
                          >
                            <Download className="h-4 w-4" />
                            {disclosure.all_files && disclosure.all_files.length > 1 
                              ? `View History (${Array.from(new Set(disclosure.all_files.map(f => f.folder_name))).length})` 
                              : (disclosure.file_path ? 'Download' : 'No File')}
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </motion.div>


      <footer className="mt-20 pt-10 border-t border-gray-100 text-center opacity-30">
        <span className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]">Aegis Institutional Risk & Compliance Terminal</span>
      </footer>

      {/* Template Download Modal */}
      <Dialog open={isTemplateModalOpen} onOpenChange={setIsTemplateModalOpen}>
        <DialogContent className="max-w-md bg-white">
          <DialogHeader>
            <DialogTitle style={{ color: '#75479C' }}>Download Templates</DialogTitle>
            <DialogDescription>
              Select a template to download
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="flex items-center justify-between p-4 border rounded hover:bg-gray-50 cursor-pointer" onClick={() => handleDownloadTemplate('MBP-1.docx')}>
              <div className="flex items-center gap-3">
                <FileText className="h-8 w-8 text-blue-500" />
                <div>
                  <h4 className="font-medium">MBP-1 Form</h4>
                  <p className="text-sm text-gray-500">Standard Disclosure Form</p>
                </div>
              </div>
              <Download className="h-5 w-5 text-gray-400" />
            </div>

            <div className="flex items-center justify-between p-4 border rounded hover:bg-gray-50 cursor-pointer" onClick={() => handleDownloadTemplate('DIR-8.docx')}>
              <div className="flex items-center gap-3">
                <FileText className="h-8 w-8 text-green-500" />
                <div>
                  <h4 className="font-medium">DIR-8 Form</h4>
                  <p className="text-sm text-gray-500">Director Declaration Form</p>
                </div>
              </div>
              <Download className="h-5 w-5 text-gray-400" />
            </div>
          </div>
          <div className="flex justify-end">
            <Button variant="outline" onClick={() => setIsTemplateModalOpen(false)}>Close</Button>
          </div>
        </DialogContent>
      </Dialog>

      <FamilyInfoModal 
        isOpen={isFamilyInfoModalOpen}
        onClose={() => setIsFamilyInfoModalOpen(false)}
        directorName={selectedDirectorName}
        din={selectedDirectorDin}
      />

      {/* Disclosure History Modal */}
      <Dialog open={isHistoryModalOpen} onOpenChange={setIsHistoryModalOpen}>
        <DialogContent className="max-w-4xl bg-white rounded-[2rem] p-0 overflow-hidden border-none shadow-2xl">
          <DialogHeader className="p-8 pb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="h-14 w-14 rounded-2xl bg-purple-50 flex items-center justify-center">
                  <History className="h-7 w-7 text-[#75479C]" />
                </div>
                <div>
                  <DialogTitle className="text-2xl font-black text-gray-900 tracking-tight">
                    Disclosure History
                  </DialogTitle>
                  <p className="text-sm text-gray-500 font-medium uppercase tracking-widest">
                    {historyDisclosure?.director_name} • DIN: {historyDisclosure?.din}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest block mb-1">Active Cycle</span>
                <Badge variant="outline" className="rounded-lg font-bold border-gray-100">FY 2024-25</Badge>
              </div>
            </div>
          </DialogHeader>

          <div className="px-8 py-6 bg-gray-50">
            {/* Stats Bar */}
            <div className="grid grid-cols-3 gap-6 p-6 rounded-[1.5rem] bg-white border border-gray-100 shadow-sm mb-8">
              <div className="border-r border-gray-50">
                <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest block mb-2">Total Companies</span>
                <span className="text-3xl font-black text-[#75479C]">
                  {Array.from(new Set(historyDisclosure?.all_files?.map(f => f.folder_name))).length || 0}
                </span>
              </div>
              <div className="border-r border-gray-50">
                <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest block mb-2">MBP-1 Forms</span>
                <span className="text-3xl font-black text-[#75479C]">
                  {historyDisclosure?.all_files?.filter(f => f.type === 'MBP-1').length || 0}
                </span>
              </div>
              <div>
                <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest block mb-2">DIR-8 Forms</span>
                <span className="text-3xl font-black text-[#75479C]">
                  {historyDisclosure?.all_files?.filter(f => f.type === 'DIR-8').length || 0}
                </span>
              </div>
            </div>

            {/* History Table */}
            <div className="rounded-2xl border border-gray-100 bg-white overflow-hidden shadow-sm max-h-[400px] overflow-y-auto">
              <Table>
                <TableHeader className="bg-gray-100 sticky top-0 z-10">
                  <TableRow>
                    <TableHead className="text-[10px] font-black uppercase tracking-widest text-gray-400 pl-6 py-4">Company Name</TableHead>
                    <TableHead className="text-[10px] font-black uppercase tracking-widest text-gray-400 py-4 text-center">MBP-1 Form</TableHead>
                    <TableHead className="text-[10px] font-black uppercase tracking-widest text-gray-400 py-4 text-center">DIR-8 Form</TableHead>
                    <TableHead className="text-[10px] font-black uppercase tracking-widest text-gray-400 py-4 text-center">Status</TableHead>
                    <TableHead className="text-[10px] font-black uppercase tracking-widest text-gray-400 py-4 text-center">Last Update</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(() => {
                    // Group files by company (folder_name)
                    const groups: Record<string, any> = {};
                    historyDisclosure?.all_files?.forEach(file => {
                      const name = file.folder_name || "General";
                      if (!groups[name]) {
                        groups[name] = { 
                          name, 
                          mbp1: null, 
                          dir8: null, 
                          date: file.date 
                        };
                      }
                      if (file.type === 'MBP-1') groups[name].mbp1 = file;
                      if (file.type === 'DIR-8') groups[name].dir8 = file;
                      // Keep latest date
                      if (file.date > groups[name].date) groups[name].date = file.date;
                    });

                    return Object.values(groups).map((group, idx) => (
                      <TableRow key={idx} className="hover:bg-blue-50/30 transition-colors border-gray-100">
                        <TableCell className="py-4 pl-6">
                          <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-xl bg-gray-50 flex items-center justify-center">
                              <Building className="h-5 w-5 text-gray-400" />
                            </div>
                            <div>
                              <div className="text-sm font-bold text-gray-900 capitalize leading-tight">
                                {group.name.toLowerCase()}
                              </div>
                              <div className="text-[10px] text-gray-400 font-medium uppercase tracking-tighter">Statutory Filling</div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell className="text-center">
                          {group.mbp1 ? (
                            <Button 
                              size="sm" 
                              variant="ghost" 
                              className="h-9 gap-2 text-[10px] font-black uppercase bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-lg px-3"
                              onClick={() => handleDownloadDisclosure(historyDisclosure!, group.mbp1.path)}
                            >
                              <Download className="h-3.5 w-3.5" /> MBP-1
                            </Button>
                          ) : (
                            <span className="text-[10px] font-bold text-gray-300">N/A</span>
                          )}
                        </TableCell>
                        <TableCell className="text-center">
                          {group.dir8 ? (
                            <Button 
                              size="sm" 
                              variant="ghost" 
                              className="h-9 gap-2 text-[10px] font-black uppercase bg-purple-50 text-purple-700 hover:bg-purple-100 rounded-lg px-3"
                              onClick={() => handleDownloadDisclosure(historyDisclosure!, group.dir8.path)}
                            >
                              <Download className="h-3.5 w-3.5" /> DIR-8
                            </Button>
                          ) : (
                            <span className="text-[10px] font-bold text-gray-300">N/A</span>
                          )}
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge className="bg-green-50 text-green-700 border-green-100 font-bold rounded-full text-[10px] gap-1 px-3">
                            <Check className="h-3 w-3" /> READY
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          <div className="flex items-center justify-center gap-2 text-xs font-medium text-gray-500">
                            <Calendar className="h-3.5 w-3.5 text-gray-300" />
                            {group.date}
                          </div>
                        </TableCell>
                      </TableRow>
                    ));
                  })()}
                </TableBody>
              </Table>
            </div>
          </div>
          <div className="p-4 bg-gray-50 border-t border-gray-100 text-center">
            <span className="text-[9px] font-black text-gray-300 uppercase tracking-widest">Secure Document Terminal • Aegis Disclosure Intelligence</span>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DirectorsDisclosureDataSource;