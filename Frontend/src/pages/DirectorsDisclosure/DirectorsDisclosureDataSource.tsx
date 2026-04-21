import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { FileText, Eye, Download, Loader2, AlertCircle, Users, Search } from "lucide-react";
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
  file_path: string;
}

interface DocumentSummary {
  id: number;
  director_name: string;
  din: string;
  file_path: string;
  full_text: string;
  summary: string;
  created_at: string;
  updated_at: string;
}

// Helper function to format the summary content
const formatSummaryContent = (content: string) => {
  // Remove the introductory text if present
  let formattedContent = content;
  if (formattedContent.startsWith("Here is a concise summary of the director's disclosure document:")) {
    formattedContent = formattedContent.substring("Here is a concise summary of the director's disclosure document:".length).trim();
  }

  // Split content into lines
  const lines = formattedContent.split('\n');
  let htmlContent = '';
  let inList = false;

  lines.forEach((line, index) => {
    const trimmedLine = line.trim();

    // Skip empty lines
    if (!trimmedLine) {
      // Add a break if we're not in a list
      if (!inList && htmlContent && !htmlContent.endsWith('<br>') && !htmlContent.endsWith('<ul class="list-disc pl-5 space-y-1">')) {
        htmlContent += '<br>';
      }
      return;
    }

    // Check if it's a section header (ends with colon)
    if (trimmedLine.endsWith(':')) {
      // Close previous list if open
      if (inList) {
        htmlContent += '</ul>';
        inList = false;
      }

      // Add header
      const headerText = trimmedLine.slice(0, -1); // Remove the colon
      htmlContent += `<h4 class="font-semibold text-lg mt-4 mb-2">${headerText}</h4>`;
    }
    // Check if it's a bullet point
    else if (trimmedLine.startsWith('•')) {
      // Start list if not already open
      if (!inList) {
        htmlContent += '<ul class="list-disc pl-5 space-y-1">';
        inList = true;
      }

      // Add list item
      const listItem = trimmedLine.substring(1).trim(); // Remove bullet and trim
      if (listItem) {
        htmlContent += `<li>${listItem}</li>`;
      }
    }
    // Regular paragraph (not a bullet point and not a header)
    else {
      // Close previous list if open
      if (inList) {
        htmlContent += '</ul>';
        inList = false;
      }

      // Add paragraph
      htmlContent += `<p class="mb-2">${trimmedLine}</p>`;
    }
  });

  // Close list if still open
  if (inList) {
    htmlContent += '</ul>';
  }

  return htmlContent || '<p>No summary available</p>';
};

const DirectorsDisclosureDataSource = () => {
  const [disclosures, setDisclosures] = useState<Disclosure[]>([]);
  const [filteredDisclosures, setFilteredDisclosures] = useState<Disclosure[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDisclosure, setSelectedDisclosure] = useState<Disclosure | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [documentSummary, setDocumentSummary] = useState<DocumentSummary | null>(null);
  const [loadingSummary, setLoadingSummary] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'summary' | 'full'>('summary');
  const [isFamilyInfoModalOpen, setIsFamilyInfoModalOpen] = useState<boolean>(false);
  const [selectedDirectorName, setSelectedDirectorName] = useState<string>("");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [isTemplateModalOpen, setIsTemplateModalOpen] = useState<boolean>(false);

  useEffect(() => {
    fetchDisclosures();
  }, []);

  useEffect(() => {
    if (searchTerm.trim() === "") {
      setFilteredDisclosures(disclosures);
    } else {
      const filtered = disclosures.filter(
        (disclosure) =>
          disclosure.director_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          disclosure.din.includes(searchTerm) ||
          disclosure.disclosure_date.includes(searchTerm)
      );
      setFilteredDisclosures(filtered);
    }
  }, [searchTerm, disclosures]);

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

  const handleDownloadDisclosure = async (disclosure: Disclosure) => {
    try {
      // The file_path from backend includes the filename
      const filename = disclosure.file_path.split('/').pop() || `${disclosure.director_name}_disclosure.docx`;
      const downloadUrl = `/api/directors-disclosures/${disclosure.id}/download`;

      // Create a temporary link and trigger download
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.error('Error downloading disclosure:', err);
    }
  };

  const fetchDocumentSummary = async (disclosure: Disclosure) => {
    try {
      setLoadingSummary(true);
      const response = await fetch(`/api/directors-disclosures/${disclosure.id}/summary`);

      if (!response.ok) {
        throw new Error('Failed to fetch document summary');
      }

      const data = await response.json();
      setDocumentSummary(data);
    } catch (err) {
      console.error('Error fetching document summary:', err);
      setDocumentSummary(null);
    } finally {
      setLoadingSummary(false);
    }
  };

  const handleViewDisclosure = async (disclosure: Disclosure) => {
    setSelectedDisclosure(disclosure);
    setIsModalOpen(true);
    setDocumentSummary(null);
    setActiveTab('summary');
    await fetchDocumentSummary(disclosure);
  };

  const handleViewFamilyInfo = (directorName: string) => {
    setSelectedDirectorName(directorName);
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
                  Directors' disclosures
                </CardTitle>
                <CardDescription className="text-gray-500 font-medium">
                  Complete registry of all statutory disclosures and filings
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
          </CardHeader>
          <CardContent>
            <div className="mb-4 text-sm" style={{ color: '#666666' }}>
              Showing {filteredDisclosures.length} of {disclosures.length} disclosures
            </div>
            <div className="rounded-[1.5rem] border border-gray-100 overflow-hidden shadow-sm">
              <Table>
                <TableHeader>
                  <TableRow className="bg-gray-50 active:bg-gray-50">
                    <TableHead className="py-5 pl-8 text-[10px] font-black text-gray-500 uppercase tracking-widest">Director name</TableHead>
                    <TableHead className="py-5 text-[10px] font-black text-gray-500 uppercase tracking-widest">DIN</TableHead>
                    <TableHead className="py-5 text-[10px] font-black text-gray-500 uppercase tracking-widest text-center">PAN</TableHead>
                    <TableHead className="py-5 text-[10px] font-black text-gray-500 uppercase tracking-widest text-center">Registry status</TableHead>
                    <TableHead className="py-5 text-[10px] font-black text-gray-500 uppercase tracking-widest text-center">Disclosure date</TableHead>
                    <TableHead className="py-5 pr-8 text-[10px] font-black text-gray-500 uppercase tracking-widest text-right">Actions control</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredDisclosures.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8" style={{ color: '#666666' }}>
                        {searchTerm ? 'No disclosures found matching your search' : 'No disclosures found'}
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredDisclosures.map((disclosure) => (
                      <TableRow key={disclosure.id} className="hover:bg-gray-50">
                        <TableCell className="font-semibold text-[#75479C]">{disclosure.director_name}</TableCell>
                        <TableCell className="font-mono text-xs">{disclosure.din}</TableCell>
                        <TableCell className="font-mono text-xs">{disclosure.pan || '—'}</TableCell>
                        <TableCell>
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
                        <TableCell className="font-medium">{disclosure.disclosure_date}</TableCell>
                        <TableCell className="text-center">
                          <div className="flex gap-2 justify-center">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleViewDisclosure(disclosure)}
                              className="gap-2"
                              style={{ borderColor: '#75479C', color: '#75479C' }}
                            >
                              <Eye className="h-4 w-4" />
                              View
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDownloadDisclosure(disclosure)}
                              className="gap-2"
                              style={{ borderColor: '#0B74B0', color: '#0B74B0' }}
                            >
                              <Download className="h-4 w-4" />
                              Download
                            </Button>
                          </div>
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

      {/* Disclosure Summary Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto bg-white">
          <DialogHeader className="p-8 border-b border-gray-50">
            <DialogTitle className="flex items-center gap-3 text-2xl font-black text-gray-900 tracking-tight">
              <FileText className="h-7 w-7 text-[#75479C]" />
              Director disclosure
            </DialogTitle>
            {selectedDisclosure && (
              <DialogDescription className="text-gray-500 font-medium mt-1">
                {selectedDisclosure.director_name} (DIN: {selectedDisclosure.din}) — {selectedDisclosure.disclosure_date}
              </DialogDescription>
            )}
          </DialogHeader>

          {/* Tab Navigation */}
          <div className="flex border-b mt-4">
            <button
              className={`py-2 px-4 font-medium ${activeTab === 'summary' ? 'border-b-2 border-purple-600 text-purple-600' : 'text-gray-500'}`}
              onClick={() => setActiveTab('summary')}
            >
              AI Summary
            </button>
            <button
              className={`py-2 px-4 font-medium ${activeTab === 'full' ? 'border-b-2 border-purple-600 text-purple-600' : 'text-gray-500'}`}
              onClick={() => setActiveTab('full')}
            >
              Full Text
            </button>
          </div>

          <div className="mt-4">
            {loadingSummary ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin" style={{ color: "#75479C" }} />
                <span className="ml-2">Loading disclosure...</span>
              </div>
            ) : (
              <div className="prose max-w-none">
                <div className="p-6 rounded-lg border bg-white" style={{ color: '#000000' }}>
                  {documentSummary ? (
                    <div>
                      {activeTab === 'summary' ? (
                        <div>
                          <h3 className="text-lg font-semibold mb-2">Summary</h3>
                          <div
                            className="bg-gray-50 p-4 rounded"
                            style={{
                              whiteSpace: 'normal',
                              lineHeight: '1.6',
                              fontSize: '0.95rem'
                            }}
                            dangerouslySetInnerHTML={{
                              __html: formatSummaryContent(documentSummary.summary)
                            }}
                          />
                          <p className="text-xs text-gray-500 mt-2 italic">* Showing active shareholdings only.</p>
                        </div>
                      ) : (
                        <div>
                          <h3 className="text-lg font-semibold mb-2">Full Text</h3>
                          <div className="whitespace-pre-wrap bg-gray-50 p-4 rounded max-h-96 overflow-y-auto">
                            {documentSummary.full_text}
                          </div>
                        </div>
                      )}
                      <div className="flex gap-2 mt-4">
                        <Button
                          variant="outline"
                          onClick={() => selectedDisclosure && handleDownloadDisclosure(selectedDisclosure)}
                          className="gap-2"
                          style={{ borderColor: '#0B74B0', color: '#0B74B0' }}
                        >
                          <Download className="h-4 w-4" />
                          Download Document
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <p>Disclosure information not available</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="flex justify-end mt-6">
            <Button
              onClick={() => setIsModalOpen(false)}
              style={{
                backgroundColor: '#75479C',
                borderColor: '#75479C',
                color: 'white'
              }}
            >
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>

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

            <div className="flex items-center justify-between p-4 border rounded hover:bg-gray-50 cursor-pointer" onClick={() => handleDownloadTemplate('Disclosure_with_CIN.docx')}>
              <div className="flex items-center gap-3">
                <FileText className="h-8 w-8 text-purple-500" />
                <div>
                  <h4 className="font-medium">Disclosure with CI Number</h4>
                  <p className="text-sm text-gray-500">Includes Corporate Identity Number</p>
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
    </div>
  );
};

export default DirectorsDisclosureDataSource;