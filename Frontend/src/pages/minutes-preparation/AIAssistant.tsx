import { useState, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { DownloadIcon, FileTextIcon, HomeIcon, UploadIcon, XIcon } from 'lucide-react';
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import { getMinutesNavItems } from '@/constants/minutesNavigation';

interface Attendee {
  name: string;
  role: string;
}

interface ActionItem {
  task: string;
  assignee: string;
}

interface MoMContent {
  title: string;
  date: string;
  attendees: Attendee[];
  agenda: string[];
  decisions: string[];
  action_items: ActionItem[];
  next_meeting: string;
}

const AIAssistant = () => {
  const navigationItems = getMinutesNavItems('ai-mom');

  const [files, setFiles] = useState<File[]>([]);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [processingStatus, setProcessingStatus] = useState<'idle' | 'processing' | 'completed' | 'error'>('idle');
  const [progress, setProgress] = useState(0);
  const [momContent, setMomContent] = useState<MoMContent | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      const validTypes = [
        'text/plain',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      ];

      if (!validTypes.includes(file.type)) {
        setError('Please upload a DOCX or TXT file.');
        return;
      }

      setFiles([file]);
      setError(null);
      handleUpload([file]);
    }
  };

  const handleUpload = async (filesToUpload: File[]) => {
    if (filesToUpload.length === 0) return;

    const file = filesToUpload[0];
    setUploadStatus('uploading');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/ai-assistant/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const result = await response.json();
      setTaskId(result.task_id);
      setUploadStatus('success');
    } catch (err) {
      console.error('Upload error:', err);
      setUploadStatus('error');
      setError('Failed to upload file. Please try again.');
    }
  };

  const handleRemoveFile = () => {
    setFiles([]);
    setUploadStatus('idle');
    setTaskId(null);
    setProcessingStatus('idle');
    setProgress(0);
    setMomContent(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleGenerateMinutes = async () => {
    if (!taskId) return;

    setProcessingStatus('processing');
    setProgress(0);
    setError(null);

    try {
      const response = await fetch(`/api/ai-assistant/generate-mom?task_id=${taskId}`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to start generation');
      }

      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await fetch(`/api/ai-assistant/status/${taskId}`);
          const statusResult = await statusResponse.json();

          if (statusResult.status === 'completed') {
            clearInterval(pollInterval);
            setProcessingStatus('completed');
            setProgress(100);

            const momResponse = await fetch(`/api/ai-assistant/mom/${taskId}`);
            const momResult = await momResponse.json();
            setMomContent(momResult);
          } else if (statusResult.status === 'error') {
            clearInterval(pollInterval);
            setProcessingStatus('error');
            setError(statusResult.error || 'Failed to generate minutes');
          } else {
            setProgress(prev => Math.min(prev + 10, 90));
          }
        } catch (err) {
          console.error('Polling error:', err);
          clearInterval(pollInterval);
          setProcessingStatus('error');
          setError('Error checking generation status');
        }
      }, 2000);
    } catch (err) {
      console.error('Generation error:', err);
      setProcessingStatus('error');
      setError('Failed to generate minutes. Please try again.');
    }
  };

  const handleDownload = async () => {
    if (!taskId) return;

    try {
      const response = await fetch(`/api/ai-assistant/download/${taskId}`);
      if (!response.ok) {
        throw new Error('Download failed');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'meeting_minutes.docx';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download error:', err);
      setError('Failed to download minutes. Please try again.');
    }
  };

  return (
    <ProductDashboardLayout
      productName="Generate Minutes"
      productRoute="/minutes-preparation"
      navigationItems={navigationItems}
    >
      <div className="p-6">
        <div className="border border-slate-200 rounded-xl bg-white shadow-xs p-6 space-y-6">
          <div className="flex justify-between items-center pb-4 border-b border-slate-100">
            <div>
              <h1 className="text-xl font-bold text-slate-900">Transcript Summarization</h1>
              <p className="text-xs text-slate-500 mt-1">
                Upload meeting transcripts to automatically compile structured summaries and action points.
              </p>
            </div>
          </div>

          <div className="max-w-2xl mx-auto space-y-6 pt-4">
            <Card className="border border-slate-200 bg-white rounded-xl shadow-xs">
              <CardHeader>
                <CardTitle className="text-sm font-bold text-slate-900">Upload Transcript</CardTitle>
              </CardHeader>
              <CardContent>
                {files.length > 0 && uploadStatus !== 'success' ? (
                  <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <div className="flex items-center gap-2">
                      <FileTextIcon className="h-5 w-5 text-slate-500" />
                      <div>
                        <p className="text-xs font-semibold text-slate-800">{files[0].name}</p>
                        <p className="text-[10px] text-slate-500">{(files[0].size / 1024).toFixed(1)} KB</p>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleRemoveFile}
                      className="h-8 w-8 p-0 text-slate-400 hover:text-slate-700"
                    >
                      <XIcon className="h-4 w-4" />
                    </Button>
                  </div>
                ) : (
                  <div
                    className="border border-dashed border-slate-200 rounded-xl p-8 text-center cursor-pointer hover:border-slate-300 transition-colors bg-slate-50/50 hover:bg-slate-50"
                  >
                    <input
                      type="file"
                      accept=".txt,.docx"
                      onChange={handleFileChange}
                      className="hidden"
                      id="file-upload"
                      ref={fileInputRef}
                    />
                    <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
                      <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center mb-3">
                        <UploadIcon className="h-5 w-5 text-slate-500" />
                      </div>
                      <p className="font-semibold text-slate-800 text-sm mb-0.5">
                        Click to upload or drag and drop
                      </p>
                      <p className="text-xs text-slate-500">
                        DOCX or TXT files only
                      </p>
                    </label>
                  </div>
                )}

                {uploadStatus === 'uploading' && (
                  <div className="mt-4 flex items-center justify-center gap-2 text-xs text-slate-500">
                    <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-slate-400 border-t-transparent"></div>
                    <p>Uploading...</p>
                  </div>
                )}

                {uploadStatus === 'success' && (
                  <Alert className="mt-4 bg-slate-50 border-slate-200 py-3">
                    <AlertDescription className="text-slate-800 text-xs font-semibold flex items-center gap-2">
                      <div className="h-1.5 w-1.5 rounded-full bg-emerald-500"></div>
                      File uploaded successfully!
                    </AlertDescription>
                  </Alert>
                )}

                {uploadStatus === 'error' && (
                  <Alert variant="destructive" className="mt-4 py-3">
                    <AlertDescription className="text-xs font-semibold flex items-center gap-2">
                      <div className="h-1.5 w-1.5 rounded-full bg-red-500"></div>
                      Failed to upload file. Please try again.
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>

              {uploadStatus === 'success' && (
                <CardFooter className="flex justify-center border-t border-slate-100 p-4 bg-slate-50/30">
                  <Button
                    onClick={handleGenerateMinutes}
                    disabled={processingStatus === 'processing'}
                    className="bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs rounded-lg px-6 h-9 shadow-xs"
                  >
                    {processingStatus === 'processing' ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                        Generating Summary...
                      </>
                    ) : (
                      <>
                        <FileTextIcon className="mr-2 h-4 w-4" />
                        Generate Summary
                      </>
                    )}
                  </Button>
                </CardFooter>
              )}
            </Card>

            {processingStatus === 'processing' && (
              <Card className="border border-slate-200 bg-white rounded-xl shadow-xs">
                <CardHeader>
                  <CardTitle className="text-sm font-bold text-slate-900">Processing</CardTitle>
                  <CardDescription className="text-xs text-slate-500">
                    Analyzing transcript and compiling summary
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <Progress value={progress} className="w-full h-1 bg-slate-100" />
                    <div className="flex items-center justify-center gap-2 text-xs text-slate-500">
                      <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-400 border-t-transparent"></div>
                      <p>Analyzing transcript and generating meeting summary...</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {processingStatus === 'completed' && momContent && (
              <Card className="border border-slate-200 bg-white rounded-xl shadow-xs overflow-hidden">
                <CardHeader className="bg-slate-50/50 border-b border-slate-100 pb-4">
                  <CardTitle className="text-sm font-bold text-slate-900">
                    Generated Meeting Summary
                  </CardTitle>
                  <CardDescription className="text-xs text-slate-500">
                    Meeting details and compiled statutory agenda summary.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6 p-6 max-h-[60vh] overflow-y-auto">
                  <div className="border-l-2 border-slate-900 pl-4 py-0.5">
                    <h3 className="text-sm font-bold text-slate-900">{momContent.title}</h3>
                    <p className="text-xs text-slate-500 mt-1">Date: {momContent.date}</p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-3">
                      <div>
                        <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                          Attendees
                        </h4>
                        <ul className="list-disc pl-4 space-y-1 mt-2">
                          {momContent.attendees.map((attendee, index) => (
                            <li key={index} className="text-xs text-slate-700">
                              <span className="font-semibold">{attendee.name}</span> ({attendee.role})
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div>
                        <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                          Agenda Items
                        </h4>
                        <ul className="list-disc pl-4 space-y-1 mt-2">
                          {momContent.agenda.map((item, index) => (
                            <li key={index} className="text-xs text-slate-700">{item}</li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div>
                        <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                          Decisions Made
                        </h4>
                        <ul className="list-disc pl-4 space-y-1 mt-2">
                          {momContent.decisions.map((decision, index) => (
                            <li key={index} className="text-xs text-slate-700">{decision}</li>
                          ))}
                        </ul>
                      </div>

                      <div>
                        <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                          Action Items
                        </h4>
                        <ul className="list-disc pl-4 space-y-1 mt-2">
                          {momContent.action_items.map((action, index) => (
                            <li key={index} className="text-xs text-slate-700">
                              <span className="font-semibold">{action.task}</span> (Assigned to: <span className="font-medium">{action.assignee}</span>)
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>

                  {momContent.next_meeting && (
                    <div className="pt-4 border-t border-slate-100">
                      <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                        Next Meeting Scheduled
                      </h4>
                      <p className="text-xs text-slate-700 mt-2">{momContent.next_meeting}</p>
                    </div>
                  )}
                </CardContent>
                <CardFooter className="flex justify-center pb-6 border-t border-slate-100 pt-4 bg-slate-50/30">
                  <Button
                    onClick={handleDownload}
                    className="bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs rounded-lg px-6 h-9 shadow-xs"
                  >
                    <DownloadIcon className="h-4 w-4 mr-2" />
                    Download as DOCX
                  </Button>
                </CardFooter>
              </Card>
            )}

            {error && (
              <Alert variant="destructive" className="py-3">
                <AlertDescription className="text-xs font-semibold">{error}</AlertDescription>
              </Alert>
            )}
          </div>
        </div>
      </div>
    </ProductDashboardLayout>
  );
};

export default AIAssistant;
