import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  RefreshCw, 
  FileText, 
  Database, 
  Upload, 
  CheckCircle2, 
  AlertCircle, 
  Search, 
  Building2, 
  User, 
  ArrowRight,
  Download,
  Loader2,
  Table,
  Check
} from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const RegistryManagement = () => {
  const [activeTab, setActiveTab] = useState("din");
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [unsyncedCins, setUnsyncedCins] = useState<any[]>([]);
  const [directors, setDirectors] = useState<any[]>([]);
  const [companies, setCompanies] = useState<any[]>([]);
  
  // Form states
  const [dinInput, setDinInput] = useState("");
  const [cinInput, setCinInput] = useState("");
  const [selectedDin, setSelectedDin] = useState("");
  const [selectedCins, setSelectedCins] = useState<string[]>([]);
  const [statusMessages, setStatusMessages] = useState<Record<string, string>>({});
  const [filteredCompanies, setFilteredCompanies] = useState<any[]>([]);

  useEffect(() => {
    fetchUnsyncedCins();
    fetchDropdownData();
  }, []);

  // Filter companies when a director is selected for document generation
  useEffect(() => {
    if (selectedDin && (activeTab === "mbp1" || activeTab === "dir8")) {
      fetch(`/api/registry/companies-by-director/${selectedDin}`)
        .then(res => res.json())
        .then(data => {
          setFilteredCompanies(data || []);
          // Reset selected CINs
          setSelectedCins([]);
        })
        .catch(err => console.error("Failed to filter companies", err));
    } else {
      setFilteredCompanies([]);
    }
  }, [selectedDin, activeTab]);

  const fetchUnsyncedCins = async () => {
    try {
      const response = await fetch("/api/registry/unsynced-cins");
      const data = await response.json();
      setUnsyncedCins(data.items || []);
    } catch (error) {
      console.error("Failed to fetch unsynced CINs", error);
    }
  };

  const fetchDropdownData = async () => {
    try {
      const [dirsRes, cosRes] = await Promise.all([
        fetch("/api/registry/directors"),
        fetch("/api/registry/companies")
      ]);
      const [dirs, cos] = await Promise.all([dirsRes.json(), cosRes.json()]);
      setDirectors(dirs || []);
      setCompanies(cos || []);
    } catch (error) {
      console.error("Failed to fetch dropdown data", error);
    }
  };

  const [progress, setProgress] = useState<Record<string, { current: number, total: number, status: string, active: boolean }>>({});
  const prevProgressRef = useRef<Record<string, boolean>>({});

  // Polling for progress
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    // We poll regardless of loading state to catch background tasks
    interval = setInterval(async () => {
      try {
        const types = ["din", "cin", "mbp1", "dir8"];
        const updates: any = {};
        
        for (const type of types) {
          const res = await fetch(`/api/registry/sync/progress?type=${type}`);
          const data = await res.json();
          updates[type] = data;

          const wasActive = prevProgressRef.current[type];
          const isNowActive = data.active;
          
          // Case 1: Just finished (was active, now inactive)
          // Case 2: Inactive but UI thinks it's loading
          const needsCleanup = (wasActive && !isNowActive) || (!isNowActive && Object.keys(loading).some(k => k.startsWith(type) && loading[k]));

          if (needsCleanup && data.total > 0) {
            const label = type.toUpperCase().replace('1', '-1').replace('8', '-8');
            
            // Only show toast if it was actually running (wasActive)
            if (wasActive) {
              toast.success(`${label} Process Completed Successfully!`, {
                duration: 3000,
                description: `Processed ${data.total} items.`
              });
            }
            
            // Clean up loading states related to this type
            setLoading(prev => {
              const next = { ...prev };
              let changed = false;
              Object.keys(next).forEach(key => {
                if (key.startsWith(type) && next[key]) {
                  next[key] = false;
                  changed = true;
                }
              });
              return changed ? next : prev;
            });
          }
          prevProgressRef.current[type] = isNowActive;
        }
        
        setProgress(updates);
        
        // Update status messages based on current progress
        Object.keys(loading).forEach(key => {
          if (!loading[key]) return;
          
          const type = key.split('-')[0];
          const data = updates[type];
          if (data && data.total > 0) {
            setStatusMessages(prev => ({ 
              ...prev, 
              [key]: data.active 
                ? `Processing: [${data.current}/${data.total}] - ${data.status}`
                : `Task finished [${data.total}/${data.total}].`
            }));
          }
        });

      } catch (e) {
        console.error("Progress polling failed", e);
      }
    }, 2000);
    
    return () => clearInterval(interval);
  }, [loading]);

  const handleSync = async (type: "din" | "cin", items: string[]) => {
    const key = items.length === 1 ? `${type}-${items[0]}` : `${type}-bulk`;
    setLoading(prev => ({ ...prev, [key]: true }));
    setStatusMessages(prev => ({ ...prev, [key]: "Initializing sync..." }));
    
    try {
      const response = await fetch(`/api/registry/sync/${type}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items })
      });
      
      const data = await response.json();
      toast.success(data.message);
      setStatusMessages(prev => ({ ...prev, [key]: "Task Queued in background..." }));
      
      // If it's a single item, we might not get extensive progress logs, 
      // so we set a timeout to clear the loading spinner if polling doesn't catch it.
      if (items.length === 1) {
        setTimeout(() => {
          setLoading(prev => ({ ...prev, [key]: false }));
          setStatusMessages(prev => ({ ...prev, [key]: "Sync task initiated." }));
        }, 5000);
      }
    } catch (error) {
      toast.error(`Failed to start ${type.toUpperCase()} sync`);
      setStatusMessages(prev => ({ ...prev, [key]: "Sync failed." }));
      setLoading(prev => ({ ...prev, [key]: false }));
    }
  };

  const handleSyncAll = async (type: "din" | "cin") => {
    const key = `${type}-all`;
    setLoading(prev => ({ ...prev, [key]: true }));
    
    try {
      setStatusMessages(prev => ({ ...prev, [key]: "Starting full database sync..." }));
      
      const response = await fetch(`/api/registry/sync/${type}/all`, {
        method: "POST"
      });
      
      const data = await response.json();
      toast.success(data.message);
    } catch (error) {
      toast.error(`Failed to start full ${type.toUpperCase()} sync`);
      setStatusMessages(prev => ({ ...prev, [key]: "Batch sync failed." }));
      setLoading(prev => ({ ...prev, [key]: false }));
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const key = "din-upload";
    setLoading(prev => ({ ...prev, [key]: true }));
    setStatusMessages(prev => ({ ...prev, [key]: `Uploading ${file.name}...` }));

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("/api/registry/sync/din/upload", {
        method: "POST",
        body: formData
      });

      const data = await response.json();
      if (response.ok) {
        toast.success(data.message);
      } else {
        toast.error(data.detail || "Upload failed");
      }
    } catch (error) {
      toast.error("Failed to upload file");
      setStatusMessages(prev => ({ ...prev, [key]: "Upload failed." }));
    } finally {
      setLoading(prev => ({ ...prev, [key]: false }));
      // The progress polling will take over for status messages
      if (event.target) event.target.value = "";
    }
  };

  const handleGenerate = async (type: "mbp1" | "dir8", all: boolean = false) => {
    const key = `${type}-${all ? 'all' : 'single'}`;
    setLoading(prev => ({ ...prev, [key]: true }));
    setStatusMessages(prev => ({ ...prev, [key]: `Preparing document generation...` }));
    
    try {
      const body: any = { all_directors: all, year: "2024-25" }; // Default to current fiscal year
      if (!all) {
        body.din = selectedDin;
        body.cins = selectedCins;
        if (!body.din || !body.cins || body.cins.length === 0) {
          toast.error("Please select a Director and at least one Company");
          setLoading(prev => ({ ...prev, [key]: false }));
          setStatusMessages(prev => ({ ...prev, [key]: "" }));
          return;
        }
      }

      setStatusMessages(prev => ({ ...prev, [key]: `Generating ${type.toUpperCase()} Word document...` }));
      
      const response = await fetch(`/api/registry/generate/${type}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      
      const data = await response.json();
      toast.success(data.message);
      setStatusMessages(prev => ({ ...prev, [key]: `Generation task queued successfully.` }));
    } catch (error) {
      toast.error(`Failed to start ${type.toUpperCase()} generation`);
      setStatusMessages(prev => ({ ...prev, [key]: `Error: Generation failed.` }));
    } finally {
      setLoading(prev => ({ ...prev, [key]: false }));
      setTimeout(() => setStatusMessages(prev => ({ ...prev, [key]: "" })), 5000);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto p-4">
      <div className="flex flex-col space-y-2">
        <h1 className="text-4xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-3">
          <RefreshCw className="h-10 w-10 text-indigo-600" />
          Registry Control Center
        </h1>
        <p className="text-slate-500 text-lg">
          Manage MCA registry synchronization and regulatory document generation.
        </p>
      </div>

      <Tabs defaultValue="din" className="w-full" onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4 p-1 bg-slate-100 dark:bg-slate-800 rounded-xl mb-8">
          <TabsTrigger value="din" className="rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm">DIN Sync</TabsTrigger>
          <TabsTrigger value="cin" className="rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm">CIN Sync</TabsTrigger>
          <TabsTrigger value="mbp1" className="rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm">MBP-1 Generator</TabsTrigger>
          <TabsTrigger value="dir8" className="rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm">DIR-8 Generator</TabsTrigger>
        </TabsList>

        <AnimatePresence mode="wait">
          {/* DIN SYNC TAB */}
          <TabsContent value="din">
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="grid grid-cols-1 md:grid-cols-2 gap-6"
            >
              <Card className="border-slate-200 shadow-md hover:shadow-lg transition-shadow duration-300">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <User className="h-5 w-5 text-indigo-500" />
                    Single DIN Sync
                  </CardTitle>
                  <CardDescription>Enter a Director's DIN to fetch their latest registry profile and associations.</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-2">
                    <Input 
                      placeholder="Enter 8-digit DIN" 
                      value={dinInput}
                      onChange={(e) => setDinInput(e.target.value)}
                      className="font-mono"
                    />
                    <Button 
                      onClick={() => handleSync("din", [dinInput])}
                      disabled={loading[`din-${dinInput}`] || !dinInput}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white"
                    >
                      {loading[`din-${dinInput}`] ? <Loader2 className="h-4 w-4 animate-spin" /> : "Sync"}
                    </Button>
                  </div>
                  {statusMessages[`din-${dinInput}`] && (
                    <p className="mt-2 text-xs text-indigo-600 font-medium animate-pulse">
                      {statusMessages[`din-${dinInput}`]}
                    </p>
                  )}
                </CardContent>
              </Card>

              <Card className="border-slate-200 shadow-md hover:shadow-lg transition-shadow duration-300 bg-slate-50/50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Upload className="h-5 w-5 text-indigo-500" />
                    Bulk DIN Sync
                  </CardTitle>
                  <CardDescription>Upload an Excel file containing a list of DINs to sync in bulk.</CardDescription>
                </CardHeader>
                <CardContent className="flex flex-col items-center justify-center p-8 border-2 border-dashed border-slate-300 rounded-lg m-4 mt-0 bg-white">
                  <input 
                    type="file" 
                    id="din-upload-input" 
                    className="hidden" 
                    accept=".xlsx,.xls,.csv"
                    onChange={handleFileUpload}
                  />
                  <Upload className="h-8 w-8 text-slate-400 mb-2" />
                  <p className="text-sm text-slate-500 mb-4 text-center">Select an Excel file with a 'DIN' column.</p>
                  
                  <div className="flex flex-col w-full gap-3">
                    <Button 
                      className="bg-indigo-600 hover:bg-indigo-700 text-white w-full"
                      onClick={() => document.getElementById('din-upload-input')?.click()}
                      disabled={loading["din-upload"]}
                    >
                      {loading["din-upload"] ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Upload className="h-4 w-4 mr-2" />}
                      Upload Excel & Sync
                    </Button>
                    
                    <div className="flex items-center gap-2">
                      <div className="h-px bg-slate-200 flex-1" />
                      <span className="text-[10px] text-slate-400 uppercase font-bold">OR</span>
                      <div className="h-px bg-slate-200 flex-1" />
                    </div>

                    <Button 
                      variant="outline" 
                      className="text-slate-600 border-slate-200 hover:bg-slate-100 w-full"
                      onClick={() => handleSyncAll("din")}
                      disabled={loading["din-all"]}
                    >
                      {loading["din-all"] ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
                      Sync Full Database
                    </Button>
                  </div>

                  {(statusMessages["din-upload"] || statusMessages["din-all"] || progress.din?.active) && (
                    <div className="mt-6 w-full space-y-2">
                      <div className="flex justify-between text-[10px] font-bold text-slate-500 uppercase">
                        <span>{progress.din?.status || "Syncing..."}</span>
                        <span>{progress.din ? Math.round((progress.din.current / progress.din.total) * 100) : 0}%</span>
                      </div>
                      <Progress value={progress.din ? (progress.din.current / progress.din.total) * 100 : 0} className="h-1.5" />
                      <p className="text-[10px] text-center text-slate-400">
                        Processed {progress.din?.current || 0} of {progress.din?.total || 0} directors
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          </TabsContent>

          {/* CIN SYNC TAB */}
          <TabsContent value="cin">
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="space-y-6"
            >
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="md:col-span-1 border-slate-200 shadow-md">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <Building2 className="h-5 w-5 text-indigo-500" />
                      Single CIN Sync
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-col gap-3">
                      <Input 
                        placeholder="Enter 21-character CIN" 
                        value={cinInput}
                        onChange={(e) => setCinInput(e.target.value)}
                        className="font-mono text-xs"
                      />
                      <Button 
                        onClick={() => handleSync("cin", [cinInput])}
                        disabled={loading[`cin-${cinInput}`] || !cinInput}
                        className="w-full bg-indigo-600 hover:bg-indigo-700"
                      >
                        {loading[`cin-${cinInput}`] ? <Loader2 className="h-4 w-4 animate-spin" /> : "Sync Company"}
                      </Button>
                      {statusMessages[`cin-${cinInput}`] && (
                        <p className="text-xs text-indigo-600 font-medium animate-pulse text-center">
                          {statusMessages[`cin-${cinInput}`]}
                        </p>
                      )}
                    </div>
                  </CardContent>
                </Card>

                <Card className="md:col-span-2 border-slate-200 shadow-md overflow-hidden">
                  <CardHeader className="bg-slate-50/50 border-b">
                    <div className="flex justify-between items-center">
                      <div>
                        <CardTitle className="flex items-center gap-2">
                          <Table className="h-5 w-5 text-orange-500" />
                          Pending CIN Syncs
                        </CardTitle>
                        <CardDescription>New companies found during DIN sync that are not yet in our database.</CardDescription>
                      </div>
                      <Badge variant="outline" className="bg-orange-50 text-orange-700 border-orange-200 px-3 py-1">
                        {unsyncedCins.length} New Discovered
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="p-0">
                    <ScrollArea className="h-[300px]">
                      {unsyncedCins.length > 0 ? (
                        <div className="divide-y divide-slate-100">
                          {unsyncedCins.map((item) => (
                            <div key={item.cin} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                              <div className="flex flex-col">
                                <span className="font-semibold text-slate-900">{item.company_name}</span>
                                <span className="text-xs font-mono text-slate-500">{item.cin}</span>
                              </div>
                              <Button 
                                variant="ghost" 
                                size="sm" 
                                onClick={() => handleSync("cin", [item.cin])}
                                className="text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50"
                              >
                                Sync Detail <ArrowRight className="ml-2 h-3 w-3" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="h-full flex flex-col items-center justify-center p-12 text-slate-400">
                          <CheckCircle2 className="h-12 w-12 text-green-500 mb-2 opacity-20" />
                          <p>All discovered companies are synced!</p>
                        </div>
                      )}
                    </ScrollArea>
                  </CardContent>
                  {unsyncedCins.length > 0 && (
                    <CardFooter className="bg-slate-50 border-t p-4 flex justify-end">
                      <Button 
                        onClick={() => handleSync("cin", unsyncedCins.map(i => i.cin))}
                        className="bg-indigo-600"
                        disabled={loading[`cin-${unsyncedCins.map(i => i.cin).join(',')}`]}
                      >
                         {loading[`cin-${unsyncedCins.map(i => i.cin).join(',')}`] ? 
                          <Loader2 className="h-4 w-4 animate-spin mr-2" /> : 
                          <RefreshCw className="h-4 w-4 mr-2" />
                        }
                        Sync All {unsyncedCins.length} New Companies
                      </Button>
                      {statusMessages[`cin-${unsyncedCins.map(i => i.cin).join(',')}`] && (
                        <p className="text-xs text-white/90 font-medium mt-2">
                          {statusMessages[`cin-${unsyncedCins.map(i => i.cin).join(',')}`]}
                        </p>
                      )}
                    </CardFooter>
                  )}
                </Card>
              </div>
            </motion.div>
          </TabsContent>

          {/* MBP-1 GENERATOR TAB */}
          <TabsContent value="mbp1">
             <motion.div 
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.98 }}
              className="grid grid-cols-1 md:grid-cols-2 gap-6"
            >
              <Card className="border-slate-200 shadow-md">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5 text-indigo-500" />
                    Individual MBP-1 Generation
                  </CardTitle>
                  <CardDescription>Generate Form MBP-1 for a specific director in a specific group company.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">Director</label>
                    <Select onValueChange={setSelectedDin}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select Director" />
                      </SelectTrigger>
                      <SelectContent>
                        {directors.map(d => (
                          <SelectItem key={d.din} value={d.din}>{d.name} ({d.din})</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <label className="text-sm font-medium text-slate-700 uppercase tracking-wider text-[10px]">Target Companies</label>
                      {filteredCompanies.length > 0 && (
                        <div className="flex items-center gap-2 cursor-pointer" onClick={() => {
                          if (selectedCins.length === filteredCompanies.length) {
                            setSelectedCins([]);
                          } else {
                            setSelectedCins(filteredCompanies.map(c => c.cin));
                          }
                        }}>
                          <span className="text-[10px] font-bold text-indigo-600 uppercase">Select All</span>
                          <Checkbox 
                            checked={selectedCins.length === filteredCompanies.length && filteredCompanies.length > 0}
                          />
                        </div>
                      )}
                    </div>
                    
                    <div className="border border-slate-100 rounded-xl bg-white overflow-hidden">
                      <ScrollArea className="h-[200px]">
                        {filteredCompanies.length > 0 ? (
                          <div className="divide-y divide-slate-50">
                            {filteredCompanies.map(c => (
                              <div key={c.cin} className="flex items-center gap-3 p-3 hover:bg-slate-50 transition-colors">
                                <Checkbox 
                                  id={`mbp1-${c.cin}`}
                                  checked={selectedCins.includes(c.cin)}
                                  onCheckedChange={(checked) => {
                                    if (checked) {
                                      setSelectedCins(prev => [...prev, c.cin]);
                                    } else {
                                      setSelectedCins(prev => prev.filter(id => id !== c.cin));
                                    }
                                  }}
                                />
                                <label 
                                  htmlFor={`mbp1-${c.cin}`}
                                  className="text-xs font-medium text-slate-700 cursor-pointer flex-1"
                                >
                                  {c.name}
                                </label>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="h-full flex items-center justify-center p-8 text-slate-400 text-xs italic">
                            {selectedDin ? "No active board seats found" : "Select a director first"}
                          </div>
                        )}
                      </ScrollArea>
                    </div>
                  </div>

                  <Button 
                    className="w-full bg-indigo-600 py-6 text-lg"
                    onClick={() => handleGenerate("mbp1")}
                    disabled={loading["mbp1-single"]}
                  >
                    {loading["mbp1-single"] ? <Loader2 className="h-5 w-5 animate-spin" /> : "Generate MBP-1 Word Document"}
                  </Button>
                  {statusMessages["mbp1-single"] && (
                    <p className="text-sm text-indigo-600 font-medium text-center">
                      {statusMessages["mbp1-single"]}
                    </p>
                  )}
                </CardContent>
              </Card>

              <Card className="border-indigo-100 shadow-md bg-indigo-50/30 border-2">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Database className="h-5 w-5 text-indigo-600" />
                    Batch Generation (Universal)
                  </CardTitle>
                  <CardDescription>Triggers a system-wide run to generate MBP-1 forms for ALL directors across ALL companies in the database.</CardDescription>
                </CardHeader>
                <CardContent className="flex flex-col items-center justify-center py-10 space-y-6">
                  <div className="h-20 w-20 rounded-full bg-indigo-100 flex items-center justify-center">
                    <FileText className="h-10 w-10 text-indigo-600" />
                  </div>
                  <div className="text-center max-w-xs">
                    <p className="text-slate-600 text-sm mb-4">This process will run in the background. Approximately 1200+ documents will be generated.</p>
                    <Button 
                      variant="default" 
                      className="bg-slate-900 text-white w-full py-6"
                      onClick={() => handleGenerate("mbp1", true)}
                      disabled={loading["mbp1-all"]}
                    >
                      {loading["mbp1-all"] ? <Loader2 className="h-5 w-5 animate-spin mr-2" /> : <Download className="h-5 w-5 mr-2" />}
                      Start Batch Process
                    </Button>
                    {statusMessages["mbp1-all"] && (
                      <p className="text-sm text-slate-600 font-medium text-center mt-4">
                        {statusMessages["mbp1-all"]}
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </TabsContent>

          {/* DIR-8 GENERATOR TAB */}
          <TabsContent value="dir8">
            <motion.div 
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.98 }}
              className="grid grid-cols-1 md:grid-cols-2 gap-6"
            >
              <Card className="border-slate-200 shadow-md">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5 text-indigo-500" />
                    Individual DIR-8 Intimation
                  </CardTitle>
                  <CardDescription>Generate Form DIR-8 intimation for a specific director.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">Director</label>
                    <Select onValueChange={setSelectedDin}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select Director" />
                      </SelectTrigger>
                      <SelectContent>
                        {directors.map(d => (
                          <SelectItem key={d.din} value={d.din}>{d.name} ({d.din})</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <label className="text-sm font-medium text-slate-700 uppercase tracking-wider text-[10px]">Target Companies</label>
                      {filteredCompanies.length > 0 && (
                        <div className="flex items-center gap-2 cursor-pointer" onClick={() => {
                          if (selectedCins.length === filteredCompanies.length) {
                            setSelectedCins([]);
                          } else {
                            setSelectedCins(filteredCompanies.map(c => c.cin));
                          }
                        }}>
                          <span className="text-[10px] font-bold text-indigo-600 uppercase">Select All</span>
                          <Checkbox 
                            checked={selectedCins.length === filteredCompanies.length && filteredCompanies.length > 0}
                          />
                        </div>
                      )}
                    </div>
                    
                    <div className="border border-slate-100 rounded-xl bg-white overflow-hidden">
                      <ScrollArea className="h-[200px]">
                        {filteredCompanies.length > 0 ? (
                          <div className="divide-y divide-slate-50">
                            {filteredCompanies.map(c => (
                              <div key={c.cin} className="flex items-center gap-3 p-3 hover:bg-slate-50 transition-colors">
                                <Checkbox 
                                  id={`dir8-${c.cin}`}
                                  checked={selectedCins.includes(c.cin)}
                                  onCheckedChange={(checked) => {
                                    if (checked) {
                                      setSelectedCins(prev => [...prev, c.cin]);
                                    } else {
                                      setSelectedCins(prev => prev.filter(id => id !== c.cin));
                                    }
                                  }}
                                />
                                <label 
                                  htmlFor={`dir8-${c.cin}`}
                                  className="text-xs font-medium text-slate-700 cursor-pointer flex-1"
                                >
                                  {c.name}
                                </label>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="h-full flex items-center justify-center p-8 text-slate-400 text-xs italic">
                            {selectedDin ? "No active board seats found" : "Select a director first"}
                          </div>
                        )}
                      </ScrollArea>
                    </div>
                  </div>

                  <Button 
                    className="w-full bg-indigo-600 py-6 text-lg"
                    onClick={() => handleGenerate("dir8")}
                    disabled={loading["dir8-single"]}
                  >
                    {loading["dir8-single"] ? <Loader2 className="h-5 w-5 animate-spin" /> : "Generate DIR-8 Document"}
                  </Button>
                  {statusMessages["dir8-single"] && (
                    <p className="text-sm text-indigo-600 font-medium text-center">
                      {statusMessages["dir8-single"]}
                    </p>
                  )}
                </CardContent>
              </Card>

              <Card className="border-indigo-100 shadow-md bg-indigo-50/30 border-2">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Database className="h-5 w-5 text-indigo-600" />
                    Universal DIR-8 Batch
                  </CardTitle>
                  <CardDescription>Batch generation of DIR-8 forms for all director-company associations currently tracked.</CardDescription>
                </CardHeader>
                <CardContent className="flex flex-col items-center justify-center py-10 space-y-6">
                  <div className="h-20 w-20 rounded-full bg-indigo-100 flex items-center justify-center">
                    <FileText className="h-10 w-10 text-indigo-600" />
                  </div>
                  <div className="text-center max-w-xs">
                    <p className="text-slate-600 text-sm mb-4">Files will be saved in the repository under 'Output_Disclosures/2024-25'.</p>
                    <Button 
                      variant="default" 
                      className="bg-slate-900 text-white w-full py-6"
                      onClick={() => handleGenerate("dir8", true)}
                      disabled={loading["dir8-all"]}
                    >
                      {loading["dir8-all"] ? <Loader2 className="h-5 w-5 animate-spin mr-2" /> : <Download className="h-5 w-5 mr-2" />}
                      Start Batch DIR-8
                    </Button>
                    {statusMessages["dir8-all"] && (
                      <p className="text-sm text-slate-600 font-medium text-center mt-4">
                        {statusMessages["dir8-all"]}
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </TabsContent>
        </AnimatePresence>
      </Tabs>
      
      <div className="bg-slate-50 rounded-xl p-6 border border-slate-200">
        <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2 mb-2">
          <AlertCircle className="h-4 w-4 text-amber-500" />
          Pro-Tip: Workflow Sequence
        </h3>
        <p className="text-sm text-slate-600 leading-relaxed">
          For the most accurate disclosures, follow this sequence: 
          <span className="font-bold text-indigo-600"> 1. Sync DINs</span> to discover all current associations → 
          <span className="font-bold text-indigo-600"> 2. Sync Pending CINs</span> to fetch full details of any new companies found → 
          <span className="font-bold text-indigo-600"> 3. Generate Documents</span> to ensure all form data is fresh from the registry.
        </p>
      </div>
    </div>
  );
};

export default RegistryManagement;
