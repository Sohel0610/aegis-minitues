import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  BookOpen, Info, Shield, Users, Network, Database, 
  FileText, Settings, BarChart3, ChevronDown, ChevronUp, 
  CheckCircle2, HelpCircle, Layers, Phone, Mail, User
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

// Sleek corporate color tokens
const COLORS = {
  purple: "#75479C",
  purpleLight: "#8B5CF6",
  purplePale: "#F5F3FF",
  blue: "#0B74B0",
  bluePale: "#E0F2FE",
  green: "#10B981",
  greenPale: "#ECFDF5",
  grayDark: "#1F2937",
  grayMedium: "#4B5563",
  grayLight: "#F3F4F6",
  white: "#FFFFFF"
};

interface FAQItem {
  question: string;
  answer: string;
}

const faqs: FAQItem[] = [
  {
    question: "How do I perform a live data sync with the MCA Registry?",
    answer: "To run a live update, navigate to the 'Registry control center' via the sidebar menu. You can perform a group-wide refresh or target an individual director by specifying their DIN. The system connects to the MCA Registry to fetch the latest filings. The update process typically completes within 2 to 5 minutes, after which all dashboards will display the newly synchronized corporate data."
  },
  {
    question: "What is overboarding and how does the platform calculate it?",
    answer: "According to Section 165 of the Indian Companies Act, 2013, a director is legally restricted to holding a maximum of 20 directorships, of which no more than 10 can be public companies. The platform's 'Institutional risk' monitor dynamically counts the active corporate board seats for each director. Private companies that are holding or subsidiary entities of a public company are automatically treated as public companies in accordance with statutory guidelines, and any breach of these thresholds immediately triggers a high-priority overboarding alert."
  },
  {
    question: "How can I download MBP-1 and DIR-8 compliance forms?",
    answer: "Navigate to the 'Disclosure Repository'. You will see a list of directors and their statutory filings. You can click 'Download' next to any director's record, or click 'Download templates' at the top to access standard template forms. If a director is active on multiple boards, a 'Consolidated MBP-1' document will be available, compiling all their interest disclosures into a single unified report."
  },
  {
    question: "How do I reconcile board seat counts if they differ from physical records?",
    answer: "Reconciled counts are determined by active DIN records registered with the MCA Registry. If a recently updated directorship is not yet visible, ensure that the director's Form DIR-12 (appointment filing) has been approved by the Registrar of Companies (RoC), then execute a live refresh from the Registry Control Center to fetch the updated registry state."
  },
  {
    question: "How does the system handle directorships in foreign companies and Section 8 companies?",
    answer: "In accordance with Section 165 of the Indian Companies Act, 2013, directorships held in foreign entities and non-profit entities registered under Section 8 of the Act are completely excluded from the statutory limit calculations. The platform automatically filters these entities out of the directorship counts."
  }
];

interface FAQAccordionProps {
  item: FAQItem;
  index: number;
  isOpen: boolean;
  onToggle: () => void;
}

const FAQAccordion = ({ item, index, isOpen, onToggle }: FAQAccordionProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, duration: 0.25 }}
      className="mb-3 rounded-xl border transition-all duration-200 overflow-hidden w-full max-w-full"
      style={{
        borderColor: isOpen ? COLORS.purple : "#E5E7EB",
        backgroundColor: isOpen ? COLORS.purplePale : COLORS.white
      }}
    >
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 text-left font-sans cursor-pointer focus:outline-none gap-4"
      >
        <span className="font-bold text-gray-900 text-xs sm:text-sm break-words flex-1">
          {item.question}
        </span>
        {isOpen ? (
          <ChevronUp className="h-4 w-4 shrink-0" style={{ color: COLORS.purple }} />
        ) : (
          <ChevronDown className="h-4 w-4 shrink-0" style={{ color: COLORS.grayMedium }} />
        )}
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <div className="px-4 pb-4 pt-1 text-xs text-gray-600 leading-relaxed font-sans whitespace-pre-line break-words w-full max-w-full">
              {item.answer}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export const DirectorsDisclosureUserGuide = () => {
  const [openFaqIndex, setOpenFaqIndex] = useState<number | null>(null);

  return (
    <div className="w-full max-w-full overflow-hidden space-y-6 px-1">
      
      {/* Sleek, Compact Hero Banner */}
      <div 
        className="relative rounded-2xl p-5 sm:p-6 md:p-8 overflow-hidden text-white shadow-md w-full"
        style={{ background: `linear-gradient(135deg, ${COLORS.purple} 0%, #5b21b6 100%)` }}
      >
        <div className="absolute top-0 right-0 w-48 h-48 bg-white/5 rounded-full blur-2xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-purple-500/10 rounded-full blur-xl pointer-events-none" />

        <div className="relative z-10 max-w-4xl">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-white/15 backdrop-filter backdrop-blur-md mb-3 border border-white/10">
            <BookOpen className="h-3.5 w-3.5 text-white" />
            <span className="text-[9px] font-black uppercase tracking-widest text-white">Platform Documentation</span>
          </div>
          
          <h1 className="text-xl sm:text-2xl font-black tracking-tight mb-2 text-white break-words">
            Directors' Disclosure & Governance Guide
          </h1>
          <p className="text-purple-100 text-xs sm:text-sm max-w-3xl leading-relaxed font-medium break-words">
            Welcome to the definitive user guide for the Aegis Directors' Disclosure Agent platform. 
            This manual is prepared for the Secretarial, Legal, and Corporate Governance teams to 
            enable compliance tracking, registry synchronization, and statutory filings.
          </p>
        </div>
      </div>

      {/* Main Grid: Stacked by default, split into columns only on xl screens (1280px+) */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 w-full items-start">
        
        {/* Left Column: Core Guide Content (takes 2/3 width on xl) */}
        <div className="xl:col-span-2 space-y-8 w-full max-w-full overflow-hidden">
          
          {/* Section: Platform Purpose & Governance Impact */}
          <section className="space-y-4">
            <div className="flex items-center gap-2 border-b border-gray-100 pb-3">
              <Info className="h-5 w-5 shrink-0" style={{ color: COLORS.purple }} />
              <h2 className="text-base sm:text-lg font-bold text-gray-900 tracking-tight break-words">
                Platform Purpose & Governance Impact
              </h2>
            </div>
            <div className="text-gray-600 text-xs sm:text-sm leading-relaxed space-y-4 break-words">
              <p>
                The <strong>Directors' Disclosure Agent</strong> is a professional compliance platform built to automate the annual statutory reporting cycle under the Indian Companies Act, 2013. By establishing a direct connection with the <strong>Ministry of Corporate Affairs (MCA) Registry</strong>, the platform queries and processes statutory directorship limits, active DIN profiles, and corporate interest records. This ensures that the Secretarial and Corporate Governance teams can manage compliance metrics dynamically without relying on error-prone spreadsheets.
              </p>
              <p>
                In terms of corporate governance, maintaining an accurate and timely disclosure of directors' interests is a primary statutory obligation. Directors are required under Section 184 of the Companies Act to disclose their concerns or interests in other companies or bodies corporate annually using Form MBP-1. Additionally, under Section 164, they must submit Form DIR-8 confirming they are not disqualified from board representation. The platform acts as a safeguard, validating these disclosures against live registry data to prevent compliance omissions that could lead to severe regulatory actions or disqualifications.
              </p>
            </div>

            {/* Strategic Benefits Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div className="p-4 rounded-xl border border-gray-100 bg-gray-50/50 hover:bg-white hover:shadow-sm transition-all w-full">
                <CheckCircle2 className="h-5 w-5 text-emerald-500 mb-2 shrink-0" />
                <h4 className="font-bold text-gray-900 text-xs sm:text-sm mb-1 break-words">Automated Overboarding Alerts</h4>
                <p className="text-[11px] text-gray-500 leading-relaxed break-words">
                  The platform counts corporate board seats to ensure compliance with the maximum limit of twenty directorships, including the ten public company restriction.
                </p>
              </div>
              <div className="p-4 rounded-xl border border-gray-100 bg-gray-50/50 hover:bg-white hover:shadow-sm transition-all w-full">
                <CheckCircle2 className="h-5 w-5 text-emerald-500 mb-2 shrink-0" />
                <h4 className="font-bold text-gray-900 text-xs sm:text-sm mb-1 break-words">Unified MBP-1 & DIR-8 Generation</h4>
                <p className="text-[11px] text-gray-500 leading-relaxed break-words">
                  The system auto-fills disclosures by gathering directorship data from subsidiaries and external entities, packaging them into audit-ready documents.
                </p>
              </div>
              <div className="p-4 rounded-xl border border-gray-100 bg-gray-50/50 hover:bg-white hover:shadow-sm transition-all w-full">
                <CheckCircle2 className="h-5 w-5 text-emerald-500 mb-2 shrink-0" />
                <h4 className="font-bold text-gray-900 text-xs sm:text-sm mb-1 break-words">Real-Time MCA Synchronization</h4>
                <p className="text-[11px] text-gray-500 leading-relaxed break-words">
                  By executing live checks on the MCA Registry database, the compliance desk accesses the most current corporate registration and filing history.
                </p>
              </div>
              <div className="p-4 rounded-xl border border-gray-100 bg-gray-50/50 hover:bg-white hover:shadow-sm transition-all w-full">
                <CheckCircle2 className="h-5 w-5 text-emerald-500 mb-2 shrink-0" />
                <h4 className="font-bold text-gray-900 text-xs sm:text-sm mb-1 break-words">DIR-3 KYC Audit Verification</h4>
                <p className="text-[11px] text-gray-500 leading-relaxed break-words">
                  The platform flags directors with pending or expired annual KYC status, mitigating the risk of inactive DIN designations and associated penalties.
                </p>
              </div>
            </div>
          </section>

          {/* Section: Platform Flow Diagram */}
          <section className="space-y-4">
            <div className="flex items-center gap-2 border-b border-gray-100 pb-3">
              <Layers className="h-5 w-5 shrink-0" style={{ color: COLORS.purple }} />
              <h2 className="text-base sm:text-lg font-bold text-gray-900 tracking-tight break-words">
                Information Flow & Sync Cycle
              </h2>
            </div>
            <div className="p-4 sm:p-6 rounded-2xl border border-gray-100 bg-gray-50/30 w-full max-w-full">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full">
                
                {/* Node 1 */}
                <div className="text-center p-4 bg-white rounded-xl border border-gray-100 shadow-sm w-full flex flex-col justify-between">
                  <div>
                    <div className="h-6 w-6 rounded-full bg-purple-100 flex items-center justify-center mx-auto mb-2 text-[#75479C] font-black text-[10px] shrink-0">1</div>
                    <h4 className="font-bold text-gray-900 text-xs mb-1 break-words">MCA Registry Query</h4>
                  </div>
                  <p className="text-[10px] text-gray-500 mt-2 break-words">Live statutory filings, active directorship networks, and corporate details are pulled dynamically.</p>
                </div>

                {/* Node 2 */}
                <div className="text-center p-4 bg-white rounded-xl border border-gray-100 shadow-sm w-full flex flex-col justify-between">
                  <div>
                    <div className="h-6 w-6 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-2 text-[#0B74B0] font-black text-[10px] shrink-0">2</div>
                    <h4 className="font-bold text-gray-900 text-xs mb-1 break-words">Aegis Intelligence Engine</h4>
                  </div>
                  <p className="text-[10px] text-gray-500 mt-2 break-words">Board seat counts are evaluated against Section 165 limits while interlocking company groups are mapped for conflicts.</p>
                </div>

                {/* Node 3 */}
                <div className="text-center p-4 bg-white rounded-xl border border-gray-100 shadow-sm w-full flex flex-col justify-between">
                  <div>
                    <div className="h-6 w-6 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-2 text-emerald-600 font-black text-[10px] shrink-0">3</div>
                    <h4 className="font-bold text-gray-900 text-xs mb-1 break-words">Disclosure Repository</h4>
                  </div>
                  <p className="text-[10px] text-gray-500 mt-2 break-words">Automated Form MBP-1 and Form DIR-8 document packages are compiled and stored in an audit-ready archive.</p>
                </div>

              </div>
            </div>
          </section>

          {/* Section: Module Deep-Dive */}
          <section className="space-y-4">
            <div className="flex items-center gap-2 border-b border-gray-100 pb-3">
              <Settings className="h-5 w-5 shrink-0" style={{ color: COLORS.purple }} />
              <h2 className="text-base sm:text-lg font-bold text-gray-900 tracking-tight break-words">
                Module Functions & Governance Explanations
              </h2>
            </div>
            
            <div className="space-y-4 w-full max-w-full">
              
              {/* Row 1 */}
              <div className="flex gap-3 p-4 rounded-xl border border-gray-100 bg-white w-full">
                <div className="h-8 w-8 rounded-lg bg-purple-50 flex items-center justify-center shrink-0 mt-0.5">
                  <BarChart3 className="h-4.5 w-4.5 text-[#75479C]" />
                </div>
                <div className="space-y-1.5 flex-1 min-w-0">
                  <h4 className="font-bold text-gray-900 text-xs sm:text-sm break-words">Analytics Dashboard</h4>
                  <p className="text-xs text-gray-500 leading-relaxed break-words">
                    Provides an immediate executive summary of group-wide compliance, displaying total active directors, unique companies, and compliance tracking status at a glance.
                  </p>
                  <p className="text-[10px] text-gray-600 leading-relaxed break-words pl-2 border-l-2 border-purple-200">
                    <strong>Governance value:</strong> This screen gives the Corporate Secretariat real-time insights to present to the board. It displays key statistics on board composition, independent directorship balances, and potential gender diversity representation.
                  </p>
                </div>
              </div>

              {/* Row 2 */}
              <div className="flex gap-3 p-4 rounded-xl border border-gray-100 bg-white w-full">
                <div className="h-8 w-8 rounded-lg bg-blue-50 flex items-center justify-center shrink-0 mt-0.5">
                  <Shield className="h-4.5 w-4.5 text-[#0B74B0]" />
                </div>
                <div className="space-y-1.5 flex-1 min-w-0">
                  <h4 className="font-bold text-gray-900 text-xs sm:text-sm break-words">Institutional Risk Monitor</h4>
                  <p className="text-xs text-gray-500 leading-relaxed break-words">
                    Active monitoring of board seats across public and private entities, validating that none of the group directors exceed statutory limits.
                  </p>
                  <p className="text-[10px] text-gray-600 leading-relaxed break-words pl-2 border-l-2 border-blue-200">
                    <strong>Governance value:</strong> Under Section 165, the platform automatically determines if private companies are subsidiaries of public companies, calculating public limits correctly. This allows the secretariat to mitigate compliance violations.
                  </p>
                </div>
              </div>

              {/* Row 3 */}
              <div className="flex gap-3 p-4 rounded-xl border border-gray-100 bg-white w-full">
                <div className="h-8 w-8 rounded-lg bg-purple-50 flex items-center justify-center shrink-0 mt-0.5">
                  <Network className="h-4.5 w-4.5 text-[#75479C]" />
                </div>
                <div className="space-y-1.5 flex-1 min-w-0">
                  <h4 className="font-bold text-gray-900 text-xs sm:text-sm break-words">Registry Intelligence</h4>
                  <p className="text-xs text-gray-500 leading-relaxed break-words">
                    Maps directorship networks, tracing connections across internal group subsidiaries and external target business entities.
                  </p>
                  <p className="text-[10px] text-gray-600 leading-relaxed break-words pl-2 border-l-2 border-purple-200">
                    <strong>Governance value:</strong> Vital for drafting Related Party Transaction (RPT) reports. Displays overlapping board positions and ownership relationships to prevent conflicts of interest.
                  </p>
                </div>
              </div>

              {/* Row 4 */}
              <div className="flex gap-3 p-4 rounded-xl border border-gray-100 bg-white w-full">
                <div className="h-8 w-8 rounded-lg bg-blue-50 flex items-center justify-center shrink-0 mt-0.5">
                  <Database className="h-4.5 w-4.5 text-[#0B74B0]" />
                </div>
                <div className="space-y-1.5 flex-1 min-w-0">
                  <h4 className="font-bold text-gray-900 text-xs sm:text-sm break-words">Directors Master Data</h4>
                  <p className="text-xs text-gray-500 leading-relaxed break-words">
                    Primary system of record for all verified director credentials, including full names, PAN credentials, active status indicators, and emergency records.
                  </p>
                  <p className="text-[10px] text-gray-600 leading-relaxed break-words pl-2 border-l-2 border-blue-200">
                    <strong>Governance value:</strong> Reconciles records against the MCA database, ensuring annual DIR-3 KYC filings are completed before the statutory September deadline.
                  </p>
                </div>
              </div>

              {/* Row 5 */}
              <div className="flex gap-3 p-4 rounded-xl border border-gray-100 bg-white w-full">
                <div className="h-8 w-8 rounded-lg bg-purple-50 flex items-center justify-center shrink-0 mt-0.5">
                  <FileText className="h-4.5 w-4.5 text-[#75479C]" />
                </div>
                <div className="space-y-1.5 flex-1 min-w-0">
                  <h4 className="font-bold text-gray-900 text-xs sm:text-sm break-words">Disclosure Repository</h4>
                  <p className="text-xs text-gray-500 leading-relaxed break-words">
                    Coordinates disclosure updates. Users can download active Form MBP-1 and Form DIR-8 files, manage document revisions, and view change logs.
                  </p>
                  <p className="text-[10px] text-gray-600 leading-relaxed break-words pl-2 border-l-2 border-purple-200">
                    <strong>Governance value:</strong> Keeps an organized, historical database of both current and historical filings, making the group audit-ready.
                  </p>
                </div>
              </div>

              {/* Row 6 */}
              <div className="flex gap-3 p-4 rounded-xl border border-gray-100 bg-white w-full">
                <div className="h-8 w-8 rounded-lg bg-blue-50 flex items-center justify-center shrink-0 mt-0.5">
                  <Layers className="h-4.5 w-4.5 text-[#0B74B0]" />
                </div>
                <div className="space-y-1.5 flex-1 min-w-0">
                  <h4 className="font-bold text-gray-900 text-xs sm:text-sm break-words">Registry Control Center</h4>
                  <p className="text-xs text-gray-500 leading-relaxed break-words">
                    Manages synchronization requests, connecting with the MCA Registry database to pull corporate filing histories.
                  </p>
                  <p className="text-[10px] text-gray-600 leading-relaxed break-words pl-2 border-l-2 border-blue-200">
                    <strong>Governance value:</strong> Automatically alerts the compliance team if a director joins or resigns from an external board, enabling proactive disclosure adjustments.
                  </p>
                </div>
              </div>

            </div>
          </section>

          {/* Section: Frequently Asked Questions */}
          <section className="space-y-4">
            <div className="flex items-center gap-2 border-b border-gray-100 pb-3">
              <HelpCircle className="h-5 w-5 shrink-0" style={{ color: COLORS.purple }} />
              <h2 className="text-base sm:text-lg font-bold text-gray-900 tracking-tight break-words">
                Frequently Asked Questions
              </h2>
            </div>
            <div className="mt-2 w-full max-w-full">
              {faqs.map((item, idx) => (
                <FAQAccordion 
                  key={idx} 
                  item={item} 
                  index={idx} 
                  isOpen={openFaqIndex === idx}
                  onToggle={() => setOpenFaqIndex(openFaqIndex === idx ? null : idx)}
                />
              ))}
            </div>
          </section>

        </div>

        {/* Right Column: Quick Compliance Sheet & Contact Card (stacked underneath on mobile/tablet, side column on xl) */}
        <div className="space-y-6 w-full max-w-full overflow-hidden">
          
          {/* Quick Compliance Sheet Card */}
          <Card className="rounded-2xl border border-gray-100 shadow-sm overflow-hidden bg-gray-50/50 w-full max-w-full">
            <CardHeader className="bg-white border-b border-gray-100 p-5">
              <CardTitle className="text-sm sm:text-base font-black text-gray-900 tracking-tight break-words">
                Quick Compliance Sheet
              </CardTitle>
              <CardDescription className="text-xs break-words">
                Statutory limits as per Companies Act, 2013
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5 space-y-4 text-xs">
              
              <div className="break-words space-y-0.5">
                <span className="text-[9px] font-black text-gray-400 uppercase tracking-widest block">Total Directorships</span>
                <span className="font-bold text-gray-900">Max 20 Companies</span>
                <p className="text-[10px] text-gray-500 leading-normal">Includes public and private entities, excluding foreign companies and Section 8 non-profit organizations.</p>
              </div>

              <div className="break-words space-y-0.5">
                <span className="text-[9px] font-black text-gray-400 uppercase tracking-widest block">Public Company Limit</span>
                <span className="font-bold text-gray-900">Max 10 Public Companies</span>
                <p className="text-[10px] text-gray-500 leading-normal">Directorships in private companies that are holding or subsidiary entities of a public company count toward this limit.</p>
              </div>

              <div className="break-words space-y-0.5">
                <span className="text-[9px] font-black text-gray-400 uppercase tracking-widest block">DIR-3 KYC Filing</span>
                <span className="font-bold text-gray-900">Annual Requirement</span>
                <p className="text-[10px] text-gray-500 leading-normal">Must be filed by September 30th of every financial year for each active DIN holder.</p>
              </div>

              <div className="break-words space-y-0.5">
                <span className="text-[9px] font-black text-gray-400 uppercase tracking-widest block">MBP-1 Interest Filing</span>
                <span className="font-bold text-gray-900">First Board Meeting</span>
                <p className="text-[10px] text-gray-500 leading-normal">Every director must submit disclosure of interest in Form MBP-1 at the first board meeting of each financial year or whenever changes occur.</p>
              </div>

            </CardContent>
          </Card>

          {/* Help & Support Desk Card */}
          <div 
            className="p-5 rounded-2xl border border-gray-100 shadow-md text-white relative overflow-hidden w-full max-w-full"
            style={{ background: `linear-gradient(135deg, ${COLORS.blue} 0%, #0369a1 100%)` }}
          >
            <div className="absolute top-0 right-0 w-24 h-24 bg-white/5 rounded-full blur-xl pointer-events-none" />
            
            <h4 className="font-bold text-sm mb-2 flex items-center gap-1.5">
              <User className="h-4.5 w-4.5 shrink-0 text-blue-200" />
              Need Support?
            </h4>
            
            <p className="text-xs text-blue-100 leading-relaxed mb-4 break-words">
              If you discover a discrepancy between the system's board count and physical records, or if an MCA Registry sync fail occurs, please contact our Secretarial Support Desk.
            </p>

            <div className="space-y-3 bg-white/10 rounded-xl p-3.5 border border-white/10 w-full text-xs">
              <div className="flex items-start gap-2 min-w-0">
                <User className="h-3.5 w-3.5 text-blue-200 shrink-0 mt-0.5" />
                <div>
                  <span className="text-[9px] font-bold text-blue-200 uppercase tracking-wider block leading-none">Support Contact</span>
                  <span className="font-bold text-white break-all">Pragnesh Darji - AGM Secretarial</span>
                </div>
              </div>

              <div className="flex items-start gap-2 min-w-0">
                <Mail className="h-3.5 w-3.5 text-blue-200 shrink-0 mt-0.5" />
                <div>
                  <span className="text-[9px] font-bold text-blue-200 uppercase tracking-wider block leading-none">Email Address</span>
                  <a href="mailto:pragnesh.darji@adani.com" className="font-bold text-white hover:underline break-all">
                    pragnesh.darji@adani.com
                  </a>
                </div>
              </div>

              <div className="flex items-start gap-2 min-w-0">
                <Phone className="h-3.5 w-3.5 text-blue-200 shrink-0 mt-0.5" />
                <div>
                  <span className="text-[9px] font-bold text-blue-200 uppercase tracking-wider block leading-none">Work Phone</span>
                  <span className="font-bold text-white break-all">59439</span>
                </div>
              </div>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};

export default DirectorsDisclosureUserGuide;
