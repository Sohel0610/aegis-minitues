import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { ArrowLeft, ArrowRight, Download, Building, Calendar, Users, Hash, Clock, CheckCircle, Upload, BookOpen, Home, FileText, Plus, FileSpreadsheet, History, MessageSquare } from 'lucide-react';
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import Stepper from '@/components/Stepper';
import PlaceSelector from '@/components/PlaceSelector';
import MultiDirectorSelector from '@/components/MultiDirectorSelector';
import { isAdmin } from '@/utils/adminAuth';
import { toast } from '@/components/ui/use-toast';
import { getMinutesNavItems } from '@/constants/minutesNavigation';
import { Step0TemplateCompany, Step2Attendance, Step8Resolutions } from './components/form-steps';

// Helper function to convert numbers to ordinals (1st, 2nd, 3rd, etc.)
const numberToOrdinal = (num: number): string => {
  const suffixes = ["th", "st", "nd", "rd"];
  const remainder = num % 100;
  return num + (suffixes[(remainder - 20) % 10] || suffixes[remainder] || suffixes[0]);
};

// Use the same Director interface as MultiDirectorSelector
interface Director {
  name: string;
  din: string;
  status?: string;
}

// Convert numbers to Indian Rupees words
const numberToWords = (num: number): string => {
  if (num === 0) return "";

  const a = ['', 'One ', 'Two ', 'Three ', 'Four ', 'Five ', 'Six ', 'Seven ', 'Eight ', 'Nine ', 'Ten ', 'Eleven ', 'Twelve ', 'Thirteen ', 'Fourteen ', 'Fifteen ', 'Sixteen ', 'Seventeen ', 'Eighteen ', 'Nineteen '];
  const b = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'];

  const inWords = (n: number): string => {
    if (n < 20) return a[n];
    if (n < 100) return b[Math.floor(n / 10)] + (n % 10 !== 0 ? ' ' + a[n % 10] : '');
    if (n < 1000) return a[Math.floor(n / 100)] + 'Hundred ' + (n % 100 !== 0 ? 'and ' + inWords(n % 100) : '');
    if (n < 100000) return inWords(Math.floor(n / 1000)) + 'Thousand ' + (n % 1000 !== 0 ? inWords(n % 1000) : '');
    if (n < 10000000) return inWords(Math.floor(n / 100000)) + 'Lakh ' + (n % 100000 !== 0 ? inWords(n % 100000) : '');
    return inWords(Math.floor(n / 10000000)) + 'Crore ' + (n % 10000000 !== 0 ? inWords(n % 10000000) : '');
  };

  return inWords(num).trim() + " Only";
};

// Section 184 Subject Lines and corresponding text
const section184SubjectLines = [
  {
    subject: "General Notice of Disclosure of Interest",
    text: "The Chairman informed the Board that the Company has received general notices of disclosure of interest from all the Directors of the Company in Form MBP-1 pursuant to Section 184(1) of the Companies Act, 2013 read with Rule 9(1) of the Companies (Meetings of Board and its Powers) Rules, 2014."
  },
  {
    subject: "Disclosure of Interest in specific contract",
    text: "The Chairman informed the Board that a notice of disclosure of interest has been received from the concerned Directors regarding any specific contracts or arrangements in which they may be interested, as required under Section 184(2) of the Companies Act, 2013."
  },
  {
    subject: "Renewal of interest disclosures",
    text: "The Board took on record the annual/periodic renewal of disclosure of interests received from the Directors in Form MBP-1, satisfying the requirements of Section 184 of the Companies Act, 2013."
  }
];

interface FormData {
  template: string;
  companyName: string;
  meetingNumber: string;
  meetingType: string;
  committeeName: string;
  meetingDate: string;
  meetingDay: string;
  timeCommenced: string;
  timeConcluded: string;
  meetingPlace: string;
  presentDirectors: Director[];
  chairmanName: string;
  // Attendance block
  inAttendance: { name: string; role: string }[];
  companySecretary: string;
  // Quorum & minutes confirmation
  previousMinutesDate: string;
  interestDisclosures: Director[];
  disqualificationDeclarations: Director[];
  hasSection184Disclosure: boolean;
  section184Subject: string;
  section184Text: string;
  // Statutory auditor's payment
  auditorPaymentNumber: number;
  auditorPaymentWords: string;
  auditorPaymentYear: number;
  // Financial statements approval
  fsYear: number;
  rptFinYearRangeFrom: number;
  rptFinYearRangeTo: number;
  signatory1Name: string;
  signatory1Role: string;
  signatory1Din: string;
  signatory2Name: string;
  signatory2Role: string;
  signatory2Din: string;
  // Directors' Report approval
  directorsReportYear: number;
  // AGM notice & meeting details
  agmNumber: string;
  agmDayName: string;
  agmMonthName: string;
  agmYear: number | null;
  agmMonth: number | null;
  agmDay: number | null;
  agmTime: string;
  registeredOfficeAddress: string;
  chairmanShortName: string;
  // Sign-off block
  recordingDate: string;
  signingDate: string;
  signingPlace: string;
  signingChairmanName: string;
  resolutions: string;
  selectedResolutions?: any[];
  customTemplateFilename?: string;
}

const FormBasedGenerator: React.FC = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [formData, setFormData] = useState<FormData>({
    template: '',
    companyName: '',
    meetingNumber: '',
    meetingType: 'Board Meeting',
    committeeName: '',
    meetingDate: '',
    meetingDay: '',
    timeCommenced: '',
    timeConcluded: '',
    meetingPlace: 'Adani Corporate House, Ahmedabad',
    presentDirectors: [],
    chairmanName: '',
    inAttendance: [],
    companySecretary: '',
    previousMinutesDate: '',
    interestDisclosures: [],
    disqualificationDeclarations: [],
    hasSection184Disclosure: false,
    section184Subject: '',
    section184Text: '',
    auditorPaymentNumber: 0,
    auditorPaymentWords: '',
    auditorPaymentYear: new Date().getFullYear(),
    fsYear: new Date().getFullYear(),
    rptFinYearRangeFrom: new Date().getFullYear() - 1,
    rptFinYearRangeTo: new Date().getFullYear(),
    signatory1Name: '',
    signatory1Role: '',
    signatory1Din: '',
    signatory2Name: '',
    signatory2Role: '',
    signatory2Din: '',
    directorsReportYear: new Date().getFullYear(),
    agmNumber: '',
    agmDayName: '',
    agmMonthName: '',
    agmYear: null,
    agmMonth: null,
    agmDay: null,
    agmTime: '',
    registeredOfficeAddress: 'Adani Corporate House, Ahmedabad',
    chairmanShortName: '',
    recordingDate: '',
    signingDate: '',
    signingPlace: 'Ahmedabad',
    signingChairmanName: '',
    resolutions: '',
    customTemplateFilename: '',
  });

  const location = useLocation();
  const navigationItems = getMinutesNavItems('dashboard');

  useEffect(() => {
    if (location.state) {
      const updates = { ...location.state };

      // Calculate meetingDay if meetingDate is present
      if (updates.meetingDate) {
        const date = new Date(updates.meetingDate);
        if (!isNaN(date.getTime())) {
          updates.meetingDay = date.toLocaleDateString('en-US', { weekday: 'long' });
        }
      }

      // Check if the passed company name is in presets
      if (updates.companyName) {
        const isPreset = companyPresets.some(c => c.name === updates.companyName);
        if (!isPreset && updates.companyName.trim() !== '') {
          setIsOtherCompany(true);
        }
      }

      setFormData(prev => ({
        ...prev,
        ...updates
      }));
    }
  }, [location.state]);

  const [resolutionTemplates, setResolutionTemplates] = useState<{ id: number; template_name: string; resolution_text: string }[]>([]);
  const [resTemplateName, setResTemplateName] = useState('');
  const [isUploadingTemplate, setIsUploadingTemplate] = useState(false);
  const [resSearch, setResSearch] = useState('');

  const moveResolutionUp = (index: number) => {
    if (index === 0) return;
    const items = [...(formData.selectedResolutions || [])];
    const temp = items[index];
    items[index] = items[index - 1];
    items[index - 1] = temp;
    
    setFormData(prev => ({
      ...prev,
      selectedResolutions: items,
      resolutions: items.map((i: any) => i.text).join('\n\n')
    }));
  };

  const moveResolutionDown = (index: number) => {
    const items = [...(formData.selectedResolutions || [])];
    if (index === items.length - 1) return;
    const temp = items[index];
    items[index] = items[index + 1];
    items[index + 1] = temp;

    setFormData(prev => ({
      ...prev,
      selectedResolutions: items,
      resolutions: items.map((i: any) => i.text).join('\n\n')
    }));
  };

  const removeResolution = (index: number) => {
    const items = [...(formData.selectedResolutions || [])];
    items.splice(index, 1);
    setFormData(prev => ({
      ...prev,
      selectedResolutions: items,
      resolutions: items.map((i: any) => i.text).join('\n\n')
    }));
  };

  const addResolutionTemplate = (template: any) => {
    const items = [...(formData.selectedResolutions || [])];
    items.push({
      id: Date.now() + Math.random(),
      template_id: template.id,
      title: template.template_name,
      text: template.resolution_text
    });
    setFormData(prev => ({
      ...prev,
      selectedResolutions: items,
      resolutions: items.map((i: any) => i.text).join('\n\n')
    }));
  };

  const handleResolutionTextChange = (index: number, text: string) => {
    const items = [...(formData.selectedResolutions || [])];
    items[index].text = text;
    setFormData(prev => ({
      ...prev,
      selectedResolutions: items,
      resolutions: items.map((i: any) => i.text).join('\n\n')
    }));
  };

  const handleCustomTemplateUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.docx')) {
      toast({ title: "Invalid File", description: "Please upload a .docx file", variant: "destructive" });
      return;
    }

    setIsUploadingTemplate(true);
    const formDataUpload = new FormData();
    formDataUpload.append('file', file);

    try {
      const res = await fetch('/api/upload-template', {
        method: 'POST',
        body: formDataUpload
      });

      if (res.ok) {
        const data = await res.json();
        setFormData(prev => ({
          ...prev,
          template: 'custom',
          customTemplateFilename: data.filename
        }));
        toast({ title: "Success", description: "Template uploaded successfully!" });
      } else {
        const err = await res.json();
        toast({ title: "Upload Failed", description: err.detail || 'Unknown error', variant: "destructive" });
      }
    } catch (err) {
      console.error("Template upload error:", err);
      toast({ title: "Upload Error", description: "Failed to upload template", variant: "destructive" });
    } finally {
      setIsUploadingTemplate(false);
    }
  };

  const handleResetForm = () => {
    sessionStorage.removeItem('minutes_form_draft');
    setCurrentStep(0);
    setFormData({
      template: '',
      companyName: '',
      meetingNumber: '',
      meetingType: 'Board Meeting',
      committeeName: '',
      meetingDate: '',
      meetingDay: '',
      timeCommenced: '',
      timeConcluded: '',
      meetingPlace: '',
      presentDirectors: [],
      chairmanName: '',
      inAttendance: [],
      companySecretary: '',
      previousMinutesDate: '',
      interestDisclosures: [],
      disqualificationDeclarations: [],
      hasSection184Disclosure: false,
      section184Subject: '',
      section184Text: '',
      auditorPaymentNumber: 0,
      auditorPaymentWords: '',
      auditorPaymentYear: new Date().getFullYear(),
      fsYear: new Date().getFullYear(),
      rptFinYearRangeFrom: new Date().getFullYear() - 1,
      rptFinYearRangeTo: new Date().getFullYear(),
      signatory1Name: '',
      signatory1Role: '',
      signatory1Din: '',
      signatory2Name: '',
      signatory2Role: '',
      signatory2Din: '',
      directorsReportYear: new Date().getFullYear(),
      agmNumber: '',
      agmDayName: '',
      agmMonthName: '',
      agmYear: null,
      agmMonth: null,
      agmDay: null,
      agmTime: '',
      registeredOfficeAddress: '',
      chairmanShortName: '',
      recordingDate: '',
      signingDate: '',
      signingPlace: '',
      signingChairmanName: '',
      resolutions: '',
      customTemplateFilename: '',
    });
    toast({ title: "Form Reset", description: "All form fields have been cleared." });
  };

  // Auto-restore draft from sessionStorage on page load/reload unless reset requested
  useEffect(() => {
    if (location.state?.resetDraft) {
      sessionStorage.removeItem('minutes_form_draft');
      return;
    }

    try {
      const savedDraft = sessionStorage.getItem('minutes_form_draft');
      if (savedDraft) {
        const parsed = JSON.parse(savedDraft);
        if (parsed.formData) {
          setFormData(prev => ({ ...prev, ...parsed.formData }));
        }
        if (typeof parsed.currentStep === 'number') {
          setCurrentStep(parsed.currentStep);
        }
      }
    } catch (e) {
      console.error("Failed to restore form draft", e);
    }
  }, [location.state]);

  // Auto-save draft to sessionStorage on formData or currentStep change
  useEffect(() => {
    try {
      if (formData.template || formData.companyName) {
        sessionStorage.setItem('minutes_form_draft', JSON.stringify({ currentStep, formData }));
      }
    } catch (e) {
      console.error("Failed to save form draft", e);
    }
  }, [formData, currentStep]);

  const [dbTemplates, setDbTemplates] = useState<any[]>([]);

  useEffect(() => {
    const fetchDbTemplates = async () => {
      try {
        const res = await fetch('/api/templates');
        if (res.ok) {
          const data = await res.json();
          setDbTemplates(data.data || []);
        }
      } catch (err) {
        console.error("Failed to fetch templates", err);
      }
    };
    fetchDbTemplates();
  }, []);

  useEffect(() => {
    const fetchResTemplates = async () => {
      try {
        const res = await fetch('/api/resolutions');
        if (res.ok) {
          const data = await res.json();
          setResolutionTemplates(data.data || []);
        }
      } catch (err) {
        console.error("Failed to fetch resolutions", err);
      }
    };
    fetchResTemplates();
  }, []);

  // Auto-populate AGM details from meeting details
  useEffect(() => {
    if (formData.meetingDate) {
      const date = new Date(formData.meetingDate);
      if (!isNaN(date.getTime())) {
        const day = date.getDate();
        const month = date.getMonth() + 1;
        const year = date.getFullYear();
        const monthName = date.toLocaleDateString('en-US', { month: 'long' });
        const dayName = date.toLocaleDateString('en-US', { weekday: 'long' });

        setFormData(prev => ({
          ...prev,
          agmDay: day,
          agmMonth: month,
          agmYear: year,
          agmMonthName: monthName,
          agmDayName: dayName,
          agmDate: formData.meetingDate,
          agmTime: prev.agmTime || formData.timeCommenced
        }));
      }
    }
  }, [formData.meetingDate, formData.timeCommenced]);

  // Auto-populate amount in words when payment amount changes
  useEffect(() => {
    if (formData.auditorPaymentNumber > 0) {
      setFormData(prev => ({
        ...prev,
        auditorPaymentWords: numberToWords(formData.auditorPaymentNumber)
      }));
    }
  }, [formData.auditorPaymentNumber]);

  const companyPresets = [
    {
      name: "Adani Enterprises Limited",
      address: "World Trade Centre, Tower 14, 17th Floor, Cuffe Parade, Mumbai - 400005",
      directors: [
        { name: "Gautam Adani", din: "00222019" },
        { name: "Vinod Adani", din: "00222020" },
        { name: "Ashish Kundra", din: "00222021" }
      ]
    },
    {
      name: "Adani Green Energy Limited",
      address: "World Trade Centre, Tower 14, 17th Floor, Cuffe Parade, Mumbai - 400005",
      directors: [
        { name: "Gautam Adani", din: "00222019" },
        { name: "Vinod Adani", din: "00222020" },
        { name: "Ashish Kundra", din: "00222021" }
      ]
    },
    {
      name: "Adani Ports and SEZ Limited",
      address: "Adani Corporate House, Shantigram, Near Vaishno Devi Circle, S. G. Highway, Khodiyar, Ahmedabad - 382421",
      directors: [
        { name: "Gautam Adani", din: "00222019" },
        { name: "Karan Adani", din: "00222022" }
      ]
    }
  ];

  const [verticals, setVerticals] = useState<any[]>([]);
  const [selectedVertical, setSelectedVertical] = useState<string>('');
  const [companies, setCompanies] = useState<any[]>([]);
  const [loadingCompanies, setLoadingCompanies] = useState(false);
  const [companySearch, setCompanySearch] = useState('');

  // Fetch verticals on mount
  useEffect(() => {
    const fetchVerticals = async () => {
      try {
        const res = await fetch('/api/verticals');
        if (res.ok) {
          const data = await res.json();
          setVerticals(data.data || []);
          if (data.data && data.data.length > 0) {
            setSelectedVertical(data.data[0].id.toString());
          }
        }
      } catch (err) {
        console.error("Failed to fetch verticals", err);
      }
    };
    fetchVerticals();
  }, []);

  // Fetch companies based on vertical and search
  useEffect(() => {
    if (!selectedVertical) return;
    const fetchCompanies = async () => {
      setLoadingCompanies(true);
      try {
        const res = await fetch(`/api/verticals/${selectedVertical}/companies?q=${encodeURIComponent(companySearch)}`);
        if (res.ok) {
          const data = await res.json();
          setCompanies(data.data || []);
        }
      } catch (err) {
        console.error("Failed to fetch companies", err);
      } finally {
        setLoadingCompanies(false);
      }
    };

    const delayDebounce = setTimeout(() => {
      fetchCompanies();
    }, 300);

    return () => clearTimeout(delayDebounce);
  }, [selectedVertical, companySearch]);

  const [isOtherCompany, setIsOtherCompany] = useState(false);

  const isFullFlow = formData.template === 'Q1' || formData.template?.includes('28.04.2025') || !['Q2', 'Q3', 'Q4'].includes(formData.template);

  const steps = isFullFlow ? [
    { id: 'template', title: 'Template & Company' },
    { id: 'meeting', title: 'Meeting Details' },
    { id: 'attendance', title: 'Attendance' },
    { id: 'disclosures', title: 'Disclosures' },
    { id: 'auditor', title: 'Auditor Payment' },
    { id: 'financial', title: 'Financial Statements' },
    { id: 'agm', title: 'AGM Details' },
    { id: 'signoff', title: 'Sign-off Details' },
    { id: 'resolutions', title: 'Resolutions' },
    { id: 'review', title: 'Review & Generate' },
  ] : [
    { id: 'template', title: 'Template & Company' },
    { id: 'meeting', title: 'Meeting Details' },
    { id: 'attendance', title: 'Attendance' },
    { id: 'signoff', title: 'Sign-off Details' },
    { id: 'resolutions', title: 'Resolutions' },
    { id: 'review', title: 'Review & Generate' },
  ];

  const isStepValidAt = (stepIndex: number): boolean => {
    const isQ1 = isFullFlow;

    if (isQ1) {
      switch (stepIndex) {
        case 0: { // Template & Company (includes Date & Time)
          const isTemplateValid = formData.template === 'custom' ? !!formData.customTemplateFilename : !!formData.template;
          return Boolean(isTemplateValid && formData.companyName.trim() !== "" && formData.meetingDate && formData.timeCommenced);
        }
        case 1: // Meeting Details (Meeting Place)
          return Boolean(formData.meetingPlace);
        case 2: // Attendance
          return formData.presentDirectors.length > 0;
        case 3: // Disclosures
          return true; // All fields are optional
        case 4: // Auditor Payment
          return formData.auditorPaymentNumber > 0 && formData.auditorPaymentWords.trim() !== "";
        case 5: // Financial Statements
          return Boolean(formData.fsYear > 0 &&
            formData.directorsReportYear > 0 &&
            formData.rptFinYearRangeFrom > 0 &&
            formData.rptFinYearRangeTo > 0 &&
            formData.signatory1Name.trim() !== "" &&
            formData.signatory1Role.trim() !== "" &&
            formData.signatory1Din.trim() !== "" &&
            formData.signatory2Name.trim() !== "" &&
            formData.signatory2Role.trim() !== "" &&
            formData.signatory2Din.trim() !== "");
        case 6: { // AGM Details
          const isAgmNumberValid = formData.agmNumber && formData.agmNumber.trim() !== "";
          const isAgmDateValid = Number.isFinite(formData.agmYear) &&
            Number.isFinite(formData.agmMonth) &&
            Number.isFinite(formData.agmDay) &&
            formData.agmYear! > 0 &&
            formData.agmMonth! >= 1 && formData.agmMonth! <= 12 &&
            formData.agmDay! >= 1 && formData.agmDay! <= 31;
          const isAgmTimeValid = formData.agmTime && formData.agmTime.trim() !== "";
          const isRegisteredOfficeValid = formData.registeredOfficeAddress && formData.registeredOfficeAddress.trim() !== "";
          return Boolean(isAgmNumberValid && isAgmDateValid && isAgmTimeValid && isRegisteredOfficeValid);
        }
        case 7: // Sign-off Details
          return Boolean(formData.recordingDate && formData.signingDate && formData.signingPlace);
        case 8: // Resolutions
          return true;
        default:
          return true;
      }
    } else {
      switch (stepIndex) {
        case 0: { // Template & Company
          const isTemplateValid = formData.template === 'custom' ? !!formData.customTemplateFilename : !!formData.template;
          return Boolean(isTemplateValid && formData.companyName.trim() !== "" && formData.meetingDate && formData.timeCommenced);
        }
        case 1: // Meeting Details
          return Boolean(formData.meetingPlace);
        case 2: // Attendance
          return formData.presentDirectors.length > 0;
        case 3: // Sign-off Details
          return Boolean(formData.recordingDate && formData.signingDate && formData.signingPlace);
        case 4: // Resolutions
          return true;
        default:
          return true;
      }
    }
  };

  // Backward-compatible wrapper using current step
  const isStepValid = (): boolean => isStepValidAt(currentStep);

  // Validate all steps up to (but not including) the given step index
  const areAllPreviousStepsValid = (upToStep: number): boolean => {
    for (let i = 0; i < upToStep; i++) {
      if (!isStepValidAt(i)) return false;
    }
    return true;
  };

  // Aggregate validation: check ALL steps (used before final submission)
  const areAllStepsValid = (): { valid: boolean; firstInvalidStep: number } => {
    const lastDataStep = steps.length - 2; // Exclude the review step
    for (let i = 0; i <= lastDataStep; i++) {
      if (!isStepValidAt(i)) {
        return { valid: false, firstInvalidStep: i };
      }
    }
    return { valid: true, firstInvalidStep: -1 };
  };

  // Get the highest step the user can navigate to (first invalid step or current + 1)
  const getMaxReachableStep = (): number => {
    for (let i = 0; i < steps.length; i++) {
      if (!isStepValidAt(i)) return i;
    }
    return steps.length - 1;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (currentStep < steps.length - 1) {
      // Move to next step
      setCurrentStep((s) => s + 1);
    } else {
      // Final step - validate ALL steps before submitting
      const { valid, firstInvalidStep } = areAllStepsValid();
      if (!valid) {
        toast({
          title: "Incomplete Information",
          description: `Please complete "${steps[firstInvalidStep].title}" (Step ${firstInvalidStep + 1}) before generating the document.`,
          variant: "destructive"
        });
        setCurrentStep(firstInvalidStep);
        return;
      }

      // All steps valid - submit form and generate document
      setIsSubmitting(true);
      try {
        // Prepare the data for the backend
        const minutesData = {
          template: formData.template,
          companyName: formData.companyName,
          meetingNumber: formData.meetingNumber,
          meetingType: formData.meetingType,
          meetingDay: formData.meetingDay,
          meetingDate: formData.meetingDate,
          meetingStartTime: formData.timeCommenced,
          meetingEndTime: formData.timeConcluded,
          meetingPlace: formData.meetingPlace,
          chairmanName: formData.chairmanName,
          presentDirectors: formData.presentDirectors,
          inAttendance: formData.inAttendance,
          companySecretary: formData.companySecretary,
          previousMeetingDate: formData.previousMinutesDate,
          authorisedOfficer: formData.companySecretary || (formData.inAttendance && formData.inAttendance.length > 0 ? formData.inAttendance.map(a => `${a.name} (${a.role})`).join(', ') : "Authorised Officer"),
          quorum: "Quorum details", // Default value
          concerns: "Concerns details", // Default value
          declarations: "Declarations details", // Default value
          auditorPaymentAmount: formData.auditorPaymentNumber.toString(),
          auditorPaymentWords: formData.auditorPaymentWords,
          financialYear: formData.fsYear.toString(),
          agmNumber: formData.agmNumber,
          agmDay: formData.agmDay?.toString() || "1",
          agmMonthName: formData.agmMonthName,
          agmDate: formData.meetingDate, // Using meeting date as default
          agmTime: formData.agmTime,
          agmPlace: formData.registeredOfficeAddress,
          recordingDate: formData.recordingDate,
          signingDate: formData.signingDate,
          signingPlace: formData.signingPlace,
          hasSection184Disclosure: formData.hasSection184Disclosure,
          section184Subject: formData.section184Subject,
          section184Text: formData.section184Text,
          resolutions: formData.resolutions,
          customTemplateFilename: formData.customTemplateFilename,
        };

        // Send the data to the backend to generate the document
        const response = await fetch('/api/generate-minutes', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(minutesData),
        });

        if (response.ok) {
          const result = await response.json();

          if (result.download_url) {
            // Create a download link using the URL from the response
            const link = document.createElement('a');
            // Ensure the URL is relative to the current origin if not absolute
            link.href = result.download_url;
            link.download = result.filename || `${formData.companyName}_${formData.template}_Minutes.docx`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
          }

          sessionStorage.removeItem('minutes_form_draft');
          toast({ title: "Success", description: result.message || 'Document generated successfully!' });
        } else {
          const error = await response.json();
          throw new Error(error.detail || 'Failed to generate document');
        }
      } catch (error) {
        console.error('Error generating document:', error);
        toast({ title: "Generation Error", description: error.message || 'Please try again.', variant: "destructive" });
      } finally {
        setIsSubmitting(false);
      }
    }
  };

  return (
    <ProductDashboardLayout
      productName="Generate Minutes"
      productRoute="/minutes-preparation"
      navigationItems={navigationItems}
    >
      <div className="container mx-auto py-3 px-4">
        <div className="flex justify-between items-center mb-3">
          <Button variant="ghost" onClick={() => navigate("/minutes-preparation")} className="text-xs font-semibold text-slate-600 hover:text-slate-900">
            <ArrowLeft className="h-4 w-4 mr-2" /> Back
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleResetForm}
            className="text-xs font-semibold text-red-600 border-red-200 hover:bg-red-50 hover:border-red-300 rounded-lg"
          >
            Reset Form
          </Button>
        </div>

        <div className="max-w-6xl mx-auto">
          <Stepper steps={steps} currentStep={currentStep} onStepClick={(stepIdx) => {
            // Allow going back freely, but only forward if all prior steps are valid
            if (stepIdx <= currentStep) {
              setCurrentStep(stepIdx);
            } else {
              const maxReachable = getMaxReachableStep();
              if (stepIdx <= maxReachable) {
                setCurrentStep(stepIdx);
              } else {
                // Show toast indicating which step needs to be completed first
                const firstBlockingStep = maxReachable;
                toast({
                  title: "Incomplete Step",
                  description: `Please complete "${steps[firstBlockingStep].title}" before proceeding.`,
                  variant: "destructive"
                });
                setCurrentStep(firstBlockingStep);
              }
            }
          }} />

          <form onSubmit={handleSubmit}>
            {/* TEMPLATE & COMPANY */}
            {currentStep === 0 && (
              <Step0TemplateCompany
                formData={formData}
                setFormData={setFormData}
                isUploadingTemplate={isUploadingTemplate}
                handleCustomTemplateUpload={handleCustomTemplateUpload}
                numberToOrdinal={numberToOrdinal}
                toast={toast}
              />
            )}

            {/* MEETING DETAILS */}
            {currentStep === 1 && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Meeting Details</CardTitle>
                  <CardDescription>Enter meeting date, time, and location</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="timeConcluded">Meeting Conclusion Time</Label>
                    <Input
                      id="timeConcluded"
                      type="time"
                      value={formData.timeConcluded}
                      onChange={(e) => setFormData(prev => ({ ...prev, timeConcluded: e.target.value }))}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="meetingPlace">Meeting Place *</Label>
                    <PlaceSelector
                      id="meetingPlace"
                      label="Meeting Place"
                      value={formData.meetingPlace}
                      onChange={(value) => setFormData(prev => ({ ...prev, meetingPlace: value }))}
                      placeholder="Select Adani Corporate House or add custom place"
                    />
                    <p className="text-sm text-muted-foreground">
                      Default: Adani Corporate House, Shantigram, Near Vaishno Devi Circle, S. G. Highway, Khodiyar, Ahmedabad - 382421, Gujarat, India
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* ATTENDANCE */}
            {currentStep === 2 && (
              <Step2Attendance
                formData={formData}
                setFormData={setFormData}
                isOtherCompany={isOtherCompany}
                setIsOtherCompany={setIsOtherCompany}
                companyPresets={companyPresets}
                isUploadingTemplate={isUploadingTemplate}
                handleCustomTemplateUpload={handleCustomTemplateUpload}
                resolutionTemplates={resolutionTemplates}
                setResolutionTemplates={setResolutionTemplates}
                resTemplateName={resTemplateName}
                setResTemplateName={setResTemplateName}
                numberToOrdinal={numberToOrdinal}
                isStepValid={isStepValid}
                toast={toast}
              />
            )}

            {/* DISCLOSURES */}
            {isFullFlow && currentStep === 3 && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Disclosures</CardTitle>
                  <CardDescription>Disclosures under the Companies Act</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <h3 className="text-lg font-medium mb-3">Interest Disclosures</h3>
                    <MultiDirectorSelector
                      id="interestDisclosures"
                      label="Select Directors with Interest Disclosures"
                      value={formData.interestDisclosures}
                      onChange={(directors) => setFormData(prev => ({ ...prev, interestDisclosures: directors }))}
                      placeholder="Type to search and add directors"
                    />
                  </div>

                  <div>
                    <h3 className="text-lg font-medium mb-3">Disqualification Declarations</h3>
                    <MultiDirectorSelector
                      id="disqualificationDeclarations"
                      label="Select Directors with Disqualification Declarations"
                      value={formData.disqualificationDeclarations}
                      onChange={(directors) => setFormData(prev => ({ ...prev, disqualificationDeclarations: directors }))}
                      placeholder="Type to search and add directors"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="previousMinutesDate">Previous Minutes Date</Label>
                    <Input
                      id="previousMinutesDate"
                      type="date"
                      value={formData.previousMinutesDate}
                      onChange={(e) => setFormData(prev => ({ ...prev, previousMinutesDate: e.target.value }))}
                    />
                  </div>

                  <div className="space-y-4 border-t pt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <Label className="text-base">Disclosure of Interest (Section 184)</Label>
                        <p className="text-sm text-muted-foreground">Is there a disclosure of interest for this meeting?</p>
                      </div>
                      <div className="flex bg-gray-100 p-1 rounded-md">
                        <Button
                          type="button"
                          variant={formData.hasSection184Disclosure ? "default" : "ghost"}
                          size="sm"
                          onClick={() => setFormData(prev => ({ ...prev, hasSection184Disclosure: true }))}
                        >
                          Yes
                        </Button>
                        <Button
                          type="button"
                          variant={!formData.hasSection184Disclosure ? "default" : "ghost"}
                          size="sm"
                          onClick={() => setFormData(prev => ({ ...prev, hasSection184Disclosure: false, section184Subject: '', section184Text: '' }))}
                        >
                          No
                        </Button>
                      </div>
                    </div>

                    {formData.hasSection184Disclosure && (
                      <div className="space-y-4 animate-in fade-in slide-in-from-top-2">
                        <div className="space-y-2">
                          <Label htmlFor="sec184Subject">Select Subject Line</Label>
                          <Select
                            value={formData.section184Subject}
                            onValueChange={(val) => {
                              const selected = section184SubjectLines.find(s => s.subject === val);
                              setFormData(prev => ({
                                ...prev,
                                section184Subject: val,
                                section184Text: selected ? selected.text : ''
                              }));
                            }}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Choose a subject line" />
                            </SelectTrigger>
                            <SelectContent className="bg-white">
                              {section184SubjectLines.map((line, i) => (
                                <SelectItem key={i} value={line.subject}>{line.subject}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="sec184Text">Disclosure Text</Label>
                          <textarea
                            id="sec184Text"
                            rows={4}
                            className="w-full p-3 border rounded-md text-sm"
                            value={formData.section184Text}
                            onChange={(e) => setFormData(prev => ({ ...prev, section184Text: e.target.value }))}
                            placeholder="Text will auto-populate based on subject line..."
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* AUDITOR PAYMENT */}
            {isFullFlow && currentStep === 4 && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Auditor Payment</CardTitle>
                  <CardDescription>Statutory auditor's payment details</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <Label htmlFor="auditorPaymentNumber">Payment Amount *</Label>
                      <Input
                        id="auditorPaymentNumber"
                        type="number"
                        value={formData.auditorPaymentNumber || ''}
                        onChange={(e) => {
                          const val = parseInt(e.target.value) || 0;
                          setFormData(prev => ({
                            ...prev,
                            auditorPaymentNumber: val,
                            auditorPaymentWords: numberToWords(val)
                          }));
                        }}
                        placeholder="e.g., 50000"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="auditorPaymentWords">Amount in Words *</Label>
                      <Input
                        id="auditorPaymentWords"
                        value={formData.auditorPaymentWords}
                        onChange={(e) => setFormData(prev => ({ ...prev, auditorPaymentWords: e.target.value }))}
                        placeholder="e.g., Fifty Thousand Only"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="auditorPaymentYear">Payment Year *</Label>
                      <Input
                        id="auditorPaymentYear"
                        type="number"
                        min="1900"
                        max="2100"
                        value={formData.auditorPaymentYear}
                        onChange={(e) => setFormData(prev => ({ ...prev, auditorPaymentYear: parseInt(e.target.value) || new Date().getFullYear() }))}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* FINANCIAL STATEMENTS */}
            {isFullFlow && currentStep === 5 && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Financial Statements</CardTitle>
                  <CardDescription>Financial statements approval details</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <Label htmlFor="fsYear">Financial Year *</Label>
                      <Input
                        id="fsYear"
                        type="number"
                        min="1900"
                        max="2100"
                        value={formData.fsYear}
                        onChange={(e) => setFormData(prev => ({ ...prev, fsYear: parseInt(e.target.value) || new Date().getFullYear() }))}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="directorsReportYear">Directors Report Year *</Label>
                      <Input
                        id="directorsReportYear"
                        type="number"
                        min="1900"
                        max="2100"
                        value={formData.directorsReportYear}
                        onChange={(e) => setFormData(prev => ({ ...prev, directorsReportYear: parseInt(e.target.value) || new Date().getFullYear() }))}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="rptFinYearRangeFrom">Report Financial Year From *</Label>
                      <Input
                        id="rptFinYearRangeFrom"
                        type="number"
                        min="1900"
                        max="2100"
                        value={formData.rptFinYearRangeFrom}
                        onChange={(e) => setFormData(prev => ({ ...prev, rptFinYearRangeFrom: parseInt(e.target.value) || (new Date().getFullYear() - 1) }))}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="rptFinYearRangeTo">Report Financial Year To *</Label>
                      <Input
                        id="rptFinYearRangeTo"
                        type="number"
                        min="1900"
                        max="2100"
                        value={formData.rptFinYearRangeTo}
                        onChange={(e) => setFormData(prev => ({ ...prev, rptFinYearRangeTo: parseInt(e.target.value) || new Date().getFullYear() }))}
                      />
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-lg font-medium">Signatory 1</h3>
                    <div className="space-y-2">
                      <Label htmlFor="signatory1">Select Director *</Label>
                      <select
                        id="signatory1"
                        value={formData.signatory1Name}
                        onChange={(e) => {
                          const selectedDirector = formData.presentDirectors.find(d => d.name === e.target.value);
                          if (selectedDirector) {
                            setFormData(prev => ({
                              ...prev,
                              signatory1Name: selectedDirector.name,
                              signatory1Din: selectedDirector.din,
                              signatory1Role: 'Director'
                            }));
                          }
                        }}
                        className="w-full p-2 border border-gray-300 rounded-md"
                      >
                        <option value="">Select a director</option>
                        {formData.presentDirectors.map((director, index) => (
                          <option key={index} value={director.name}>
                            {director.name} (DIN: {director.din})
                          </option>
                        ))}
                      </select>
                      {formData.signatory1Name && (
                        <p className="text-sm text-muted-foreground">
                          Selected: {formData.signatory1Name} - DIN: {formData.signatory1Din}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-lg font-medium">Signatory 2</h3>
                    <div className="space-y-2">
                      <Label htmlFor="signatory2">Select Director *</Label>
                      <select
                        id="signatory2"
                        value={formData.signatory2Name}
                        onChange={(e) => {
                          const selectedDirector = formData.presentDirectors.find(d => d.name === e.target.value);
                          if (selectedDirector) {
                            setFormData(prev => ({
                              ...prev,
                              signatory2Name: selectedDirector.name,
                              signatory2Din: selectedDirector.din,
                              signatory2Role: 'Director'
                            }));
                          }
                        }}
                        className="w-full p-2 border border-gray-300 rounded-md"
                      >
                        <option value="">Select a director</option>
                        {formData.presentDirectors.map((director, index) => (
                          <option key={index} value={director.name}>
                            {director.name} (DIN: {director.din})
                          </option>
                        ))}
                      </select>
                      {formData.signatory2Name && (
                        <p className="text-sm text-muted-foreground">
                          Selected: {formData.signatory2Name} - DIN: {formData.signatory2Din}
                        </p>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* AGM DETAILS */}
            {isFullFlow && currentStep === 6 && (
              <Card className="mb-6 border border-slate-200 shadow-xs rounded-xl bg-white">
                <CardHeader className="border-b border-slate-100 pb-4">
                  <CardTitle className="text-base font-bold text-slate-900">AGM Details</CardTitle>
                  <CardDescription className="text-xs text-slate-500">Annual General Meeting information</CardDescription>
                </CardHeader>
                <CardContent className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="agmNumber" className="text-xs font-semibold text-slate-700">AGM Number *</Label>
                    <Input
                      id="agmNumber"
                      name="agmNumber"
                      type="number"
                      min="1"
                      value={formData.agmNumber ? parseInt(formData.agmNumber.replace(/(st|nd|rd|th)$/, '')) || '' : ''}
                      onChange={(e) => {
                        const num = parseInt(e.target.value);
                        if (!isNaN(num)) {
                          // Convert to ordinal and update state
                          const ordinal = numberToOrdinal(num);
                          setFormData(prev => ({ ...prev, agmNumber: ordinal }));
                        } else {
                          setFormData(prev => ({ ...prev, agmNumber: '' }));
                        }
                      }}
                      placeholder="e.g., 10"
                      className="bg-white border-slate-200 h-9 rounded-lg text-xs"
                    />
                    <p className="text-xs text-slate-500">
                      Enter a number and it will be automatically converted to ordinal (e.g., 10 → 10th)
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="agmDate" className="text-xs font-semibold text-slate-700">AGM Date *</Label>
                    <Input
                      id="agmDate"
                      name="agmDate"
                      type="date"
                      value={formData.agmYear && formData.agmMonth && formData.agmDay ?
                        `${formData.agmYear}-${String(formData.agmMonth).padStart(2, '0')}-${String(formData.agmDay).padStart(2, '0')}` : ''}
                      onChange={(e) => {
                        const date = new Date(e.target.value);
                        if (!isNaN(date.getTime())) {
                          setFormData(prev => ({
                            ...prev,
                            agmYear: date.getFullYear(),
                            agmMonth: (date.getMonth() + 1),
                            agmDay: date.getDate(),
                            agmDayName: date.toLocaleDateString('en-US', { weekday: 'long' }),
                            agmMonthName: date.toLocaleDateString('en-US', { month: 'long' })
                          }));
                        }
                      }}
                      className="bg-white border-slate-200 h-9 rounded-lg text-xs"
                    />
                    <p className="text-xs text-slate-500">
                      Select the AGM date
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="agmTime" className="text-xs font-semibold text-slate-700">AGM Time (9 AM - 6 PM) *</Label>
                    <Input
                      id="agmTime"
                      name="agmTime"
                      type="time"
                      min="09:00"
                      max="18:00"
                      value={formData.agmTime}
                      onChange={(e) => setFormData(prev => ({ ...prev, agmTime: e.target.value }))}
                      className="bg-white border-slate-200 h-9 rounded-lg text-xs"
                    />
                    <p className="text-xs text-slate-500">
                      Select the time of the AGM (9:00 AM to 6:00 PM only)
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="agmDayName" className="text-xs font-semibold text-slate-700">AGM Day Name</Label>
                    <Input
                      id="agmDayName"
                      name="agmDayName"
                      value={formData.agmDayName}
                      onChange={(e) => setFormData(prev => ({ ...prev, agmDayName: e.target.value }))}
                      placeholder="e.g., Friday"
                      readOnly
                      className="bg-slate-50 border-slate-200 h-9 rounded-lg text-xs text-slate-600"
                    />
                    <p className="text-xs text-slate-500">
                      Automatically populated based on the selected date
                    </p>
                  </div>

                  <div className="space-y-2 md:col-span-2">
                    <PlaceSelector
                      id="registeredOfficeAddress"
                      label="Registered Office Address *"
                      value={formData.registeredOfficeAddress}
                      onChange={(value) => setFormData(prev => ({ ...prev, registeredOfficeAddress: value }))}
                      placeholder="Select address or add custom address"
                    />
                    <p className="text-xs text-slate-500">
                      Default: Adani Corporate House, Ahmedabad
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* SIGN-OFF DETAILS */}
            {((isFullFlow && currentStep === 7) || (!isFullFlow && currentStep === 3)) && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Sign-off Details</CardTitle>
                  <CardDescription>Recording and signing information</CardDescription>
                </CardHeader>
                <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="recordingDate">Recording Date *</Label>
                    <Input
                      id="recordingDate"
                      type="date"
                      value={formData.recordingDate}
                      onChange={(e) => setFormData(prev => ({ ...prev, recordingDate: e.target.value }))}
                      className={!formData.recordingDate ? 'border-red-500' : ''}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="signingDate">Signing Date *</Label>
                    <Input
                      id="signingDate"
                      type="date"
                      value={formData.signingDate}
                      onChange={(e) => setFormData(prev => ({ ...prev, signingDate: e.target.value }))}
                      className={!formData.signingDate ? 'border-red-500' : ''}
                    />
                  </div>

                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="signingPlace">Signing Place *</Label>
                    <Select
                      value={formData.signingPlace === 'Ahmedabad' ? 'Ahmedabad' : 'Other'}
                      onValueChange={(val) => {
                        if (val === 'Ahmedabad') {
                          setFormData(prev => ({ ...prev, signingPlace: 'Ahmedabad' }));
                        } else {
                          setFormData(prev => ({ ...prev, signingPlace: '' }));
                        }
                      }}
                    >
                      <SelectTrigger className="bg-white">
                        <SelectValue placeholder="Select signing place" />
                      </SelectTrigger>
                      <SelectContent className="bg-white">
                        <SelectItem value="Ahmedabad">Ahmedabad</SelectItem>
                        <SelectItem value="Other">Custom Address</SelectItem>
                      </SelectContent>
                    </Select>

                    {formData.signingPlace !== 'Ahmedabad' && (
                      <div className="mt-2 animate-in fade-in slide-in-from-top-1">
                        <Input
                          id="signingPlaceCustom"
                          value={formData.signingPlace}
                          onChange={(e) => setFormData(prev => ({ ...prev, signingPlace: e.target.value }))}
                          placeholder="Enter custom signing place address"
                          className={!formData.signingPlace.trim() ? 'border-red-500' : ''}
                        />
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* RESOLUTIONS */}
            {((isFullFlow && currentStep === 8) || (!isFullFlow && currentStep === 4)) && (
              <Step8Resolutions
                formData={formData}
                setFormData={setFormData}
                resolutionTemplates={resolutionTemplates}
                setResolutionTemplates={setResolutionTemplates}
                resTemplateName={resTemplateName}
                setResTemplateName={setResTemplateName}
                toast={toast}
              />
            )}

            {/* REVIEW & GENERATE */}
            {((isFullFlow && currentStep === 9) || (!isFullFlow && currentStep === 5)) && (
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Review Your Information</CardTitle>
                  <CardDescription>Please review all information before generating the document</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                        <Building className="h-5 w-5" />
                        Company Information
                      </h3>
                      <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                        <p><span className="font-medium">Company:</span> {formData.companyName || 'Not provided'}</p>
                        <p><span className="font-medium">Template:</span> {formData.template || 'Not provided'}</p>
                        <p><span className="font-medium">Meeting #:</span> {formData.meetingNumber || 'Not provided'}</p>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                        <Calendar className="h-5 w-5" />
                        Meeting Details
                      </h3>
                      <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                        <p><span className="font-medium">Date:</span> {formData.meetingDate || 'Not provided'}</p>
                        <p><span className="font-medium">Day:</span> {formData.meetingDay || 'Not provided'}</p>
                        <p><span className="font-medium">Time:</span> {formData.timeCommenced} - {formData.timeConcluded}</p>
                        <p><span className="font-medium">Place:</span> {formData.meetingPlace || 'Not provided'}</p>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                      <Users className="h-5 w-5" />
                      Attendance
                    </h3>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="font-medium mb-2">Directors Present:</p>
                      <ul className="list-disc pl-5 space-y-1">
                        {formData.presentDirectors.map((director, index) => (
                          <li key={index}>
                            {director.name} (DIN: {director.din || 'Not provided'})
                          </li>
                        ))}
                      </ul>
                      <p className="font-medium mt-3 mb-2">Chairman:</p>
                      <p>{formData.chairmanName || 'Not provided'}</p>
                    </div>
                  </div>

                  {formData.template === 'Q1' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                          <Hash className="h-5 w-5" />
                          AGM Details
                        </h3>
                        <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                          <p><span className="font-medium">AGM #:</span> {formData.agmNumber || 'Not provided'}</p>
                          <p><span className="font-medium">Date:</span> {formData.agmDay}/{formData.agmMonth}/{formData.agmYear}</p>
                          <p><span className="font-medium">Place:</span> {formData.registeredOfficeAddress || 'Not provided'}</p>
                          <p><span className="font-medium">Time:</span> {formData.agmTime || 'Not provided'}</p>
                          <p><span className="font-medium">Day:</span> {formData.agmDayName || 'Not provided'}</p>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                        <Clock className="h-5 w-5" />
                        Sign-off Details
                      </h3>
                      <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                        <p><span className="font-medium">Recording Date:</span> {formData.recordingDate || 'Not provided'}</p>
                        <p><span className="font-medium">Signing Date:</span> {formData.signingDate || 'Not provided'}</p>
                        <p><span className="font-medium">Signing Place:</span> {formData.signingPlace || 'Not provided'}</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="h-5 w-5 text-blue-600" />
                      <h3 className="font-semibold text-blue-800">Ready to Generate</h3>
                    </div>
                    <p className="text-sm text-blue-700">
                      All information has been reviewed. Click the "Generate Document" button below to create your meeting minutes document.
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Navigation */}
            <div className="flex justify-between mt-8">
              <Button
                type="button"
                variant="outline"
                onClick={() => setCurrentStep((s) => Math.max(0, s - 1))}
                disabled={currentStep === 0}
              >
                <ArrowLeft className="h-4 w-4 mr-2" /> Previous
              </Button>

              {currentStep === steps.length - 1 ? (
                <Button
                  type="submit"
                  disabled={isSubmitting || !isStepValid()}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {isSubmitting ? (
                    <>
                      <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent mr-2" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Download className="h-4 w-4 mr-2" /> Generate Document
                    </>
                  )}
                </Button>
              ) : (
                <Button
                  type="submit"
                  disabled={!isStepValid()}
                  className="flex items-center gap-2 px-6 py-2"
                >
                  Next <ArrowRight className="h-4 w-4" />
                </Button>
              )}
            </div>
          </form>
        </div>
      </div>
    </ProductDashboardLayout>
  );
};

export default FormBasedGenerator;