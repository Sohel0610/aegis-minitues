import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  BookOpen, Info, Shield, Users, Network, Database, 
  FileSpreadsheet, History, FileText, Settings, BarChart3, 
  ChevronDown, ChevronUp, CheckCircle2, AlertCircle, HelpCircle, 
  ArrowRight, Download, RefreshCw, Layers
} from "lucide-react";

// Brand Colors
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
    question: "How do I perform a live data sync with the MCA database?",
    answer: "Go to the 'Registry control center' from the sidebar. You can perform a group-wide update or target a specific director using their DIN. The system connects to the MCA Registry Proxy to fetch the latest details. Once requested, the update takes about 2 to 5 minutes to synchronize."
  },
  {
    question: "What is overboarding and how does the platform calculate it?",
    answer: "Under Section 165 of the Indian Companies Act, 2013, a director can hold a maximum of 20 directorships, of which no more than 10 can be public companies. The 'Institutional risk' monitor counts the active corporate board seats held by each director. If a director exceeds either of these thresholds, a high-priority 'Overboarding Alert' is flagged on the dashboard to warn the secretarial team."
  },
  {
    question: "How can I download MBP-1 and DIR-8 compliance forms?",
    answer: "Navigate to the 'Disclosure Repository'. You will see a list of directors and their statutory filings. You can click 'Download' next to any director's record, or click 'Download templates' at the top to access standard template forms. If a director is active on multiple boards, a 'Consolidated MBP-1' document will be available, compiling all their interest disclosures into a single unified report."
  },
  {
    question: "What is the difference between 'Live', 'Cached', and 'Stale' registry status?",
    answer: "• Live: Data has been synchronized with the MCA registry within the last 24 hours.\n• Cached: Data is fresh, fetched within the last 90 days.\n• Stale: Data has not been updated for over 90 days. We recommend running a single DIN refresh for these directors from the Registry control center."
  },
  {
    question: "How do I update a director's profile photo?",
    answer: "Go to 'Directors master data', locate the director in the table, and click 'View Profile'. In the profile dialog, you can upload a new photo. The platform immediately updates the avatar across all analytics and compliance screens, automatically handling fallback silhouettes if no photo is provided."
  }
];

const FAQAccordion = ({ item, index }: { item: FAQItem; index: number }) => {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      className="mb-4 rounded-2xl border transition-all duration-200 overflow-hidden"
      style={{
        borderColor: isOpen ? COLORS.purple : "#E5E7EB",
        backgroundColor: isOpen ? COLORS.purplePale : COLORS.white
      }}
    >
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-5 text-left font-sans cursor-pointer focus:outline-none"
      >
        <span className="font-bold text-gray-900 text-sm md:text-base">
          {item.question}
        </span>
        {isOpen ? (
          <ChevronUp className="h-5 w-5 shrink-0" style={{ color: COLORS.purple }} />
        ) : (
          <ChevronDown className="h-5 w-5 shrink-0" style={{ color: COLORS.grayMedium }} />
        )}
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
          >
            <div className="px-5 pb-5 pt-1 text-xs md:text-sm text-gray-600 leading-relaxed font-sans whitespace-pre-line">
              {item.answer}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export const DirectorsDisclosureUserGuide = () => {
  return (
    <div className="bg-white min-h-screen font-sans">
      {/* Hero Banner */}
      <div 
        className="relative rounded-[2rem] p-8 md:p-12 overflow-hidden mb-10 text-white shadow-xl"
        style={{ background: `linear-gradient(135deg, ${COLORS.purple} 0%, #4c1d95 100%)` }}
      >
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-purple-500/10 rounded-full blur-2xl" />

        <div className="relative z-10 max-w-4xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/15 backdrop-filter backdrop-blur-md mb-6 border border-white/10">
            <BookOpen className="h-4 w-4 text-white" />
            <span className="text-[10px] font-black uppercase tracking-widest text-white">Platform Documentation</span>
          </div>
          
          <h1 className="text-3xl md:text-4xl lg:text-5xl font-black tracking-tight mb-4 leading-tight text-white">
            Directors' Disclosure & Governance Guide
          </h1>
          <p className="text-purple-100 text-sm md:text-base max-w-2xl leading-relaxed font-medium">
            Welcome to the definitive user guide for the Aegis Directors' Disclosure platform. 
            This manual is prepared for the Secretarial, Legal, and Corporate Governance teams to 
            enable compliance tracking, registry synchronization, and statutory filings.
          </p>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left column - Content */}
        <div className="lg:col-span-2 space-y-10">
          
          {/* Section: What is this Platform */}
          <section className="space-y-4">
            <h2 className="text-xl md:text-2xl font-black text-gray-900 tracking-tight flex items-center gap-3">
              <Info className="h-6 w-6" style={{ color: COLORS.purple }} />
              Platform Purpose & Core Benefits
            </h2>
            <div className="prose max-w-none text-gray-600 text-sm md:text-base leading-relaxed space-y-3">
              <p>
                The <strong>Directors' Disclosure Platform</strong> is designed to automate and simplify the annual 
                statutory compliance cycle under the Indian Companies Act, 2013. By connecting directly with the 
                <strong> Ministry of Corporate Affairs (MCA) database</strong>, it monitors directorship limits, 
                KYC statuses, and regulatory changes in real-time.
              </p>
              <p>
                As a member of the Secretarial team, this system eliminates manual tracking of board seats, 
                detects compliance risks early, and compiles multi-entity disclosures into audit-ready documents with one click.
              </p>
            </div>

            {/* Strategic Benefits Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-6">
              <div className="p-5 rounded-2xl border border-gray-100 bg-gray-50/50 hover:bg-white transition-all shadow-sm">
                <CheckCircle2 className="h-6 w-6 text-emerald-500 mb-3" />
                <h4 className="font-bold text-gray-900 text-sm mb-1">Automated Overboarding Alerts</h4>
                <p className="text-xs text-gray-500 leading-relaxed">
                  Automatically flags if a director exceeds the statutory threshold of 20 companies or 10 public company board seats.
                </p>
              </div>
              <div className="p-5 rounded-2xl border border-gray-100 bg-gray-50/50 hover:bg-white transition-all shadow-sm">
                <CheckCircle2 className="h-6 w-6 text-emerald-500 mb-3" />
                <h4 className="font-bold text-gray-900 text-sm mb-1">Unified MBP-1 / DIR-8 Downloads</h4>
                <p className="text-xs text-gray-500 leading-relaxed">
                  Consolidates statutory disclosures from multiple subsidiaries into one clean, unified disclosure form.
                </p>
              </div>
              <div className="p-5 rounded-2xl border border-gray-100 bg-gray-50/50 hover:bg-white transition-all shadow-sm">
                <CheckCircle2 className="h-6 w-6 text-emerald-500 mb-3" />
                <h4 className="font-bold text-gray-900 text-sm mb-1">Real-Time MCA Sync</h4>
                <p className="text-xs text-gray-500 leading-relaxed">
                  Queries active DIN records to ensure the legal department works with the absolute latest corporate registry details.
                </p>
              </div>
              <div className="p-5 rounded-2xl border border-gray-100 bg-gray-50/50 hover:bg-white transition-all shadow-sm">
                <CheckCircle2 className="h-6 w-6 text-emerald-500 mb-3" />
                <h4 className="font-bold text-gray-900 text-sm mb-1">KYC Status Audits</h4>
                <p className="text-xs text-gray-500 leading-relaxed">
                  Identifies directors with pending or expired annual DIR-3 KYC compliance to prevent statutory penalties.
                </p>
              </div>
            </div>
          </section>

          {/* Section: Platform Flow Diagram */}
          <section className="space-y-4 pt-4">
            <h2 className="text-xl md:text-2xl font-black text-gray-900 tracking-tight flex items-center gap-3">
              <Layers className="h-6 w-6" style={{ color: COLORS.purple }} />
              Information Flow & Sync Cycle
            </h2>
            <div className="p-6 md:p-8 rounded-[1.5rem] border border-gray-100 bg-gray-50/30">
              <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                
                {/* Node 1 */}
                <div className="text-center p-4 bg-white rounded-2xl border border-gray-100 shadow-sm w-full md:w-1/3">
                  <div className="h-8 w-8 rounded-full bg-purple-100 flex items-center justify-center mx-auto mb-2 text-[#75479C] font-black text-xs">1</div>
                  <h4 className="font-bold text-gray-900 text-xs mb-1">MCA Registry Proxy</h4>
                  <p className="text-[10px] text-gray-500">Live statutory data & board positions queried.</p>
                </div>

                <ArrowRight className="hidden md:block h-6 w-6 text-gray-400" />

                {/* Node 2 */}
                <div className="text-center p-4 bg-white rounded-2xl border border-gray-100 shadow-sm w-full md:w-1/3">
                  <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-2 text-[#0B74B0] font-black text-xs">2</div>
                  <h4 className="font-bold text-gray-900 text-xs mb-1">Aegis Intelligence Engine</h4>
                  <p className="text-[10px] text-gray-500">Limits parsed, cross-holding risks calculated.</p>
                </div>

                <ArrowRight className="hidden md:block h-6 w-6 text-gray-400" />

                {/* Node 3 */}
                <div className="text-center p-4 bg-white rounded-2xl border border-gray-100 shadow-sm w-full md:w-1/3">
                  <div className="h-8 w-8 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-2 text-emerald-600 font-black text-xs">3</div>
                  <h4 className="font-bold text-gray-900 text-xs mb-1">Compliance Repo</h4>
                  <p className="text-[10px] text-gray-500">Forms generated & digital archives stored.</p>
                </div>

              </div>
            </div>
          </section>

          {/* Section: Module Deep-Dive */}
          <section className="space-y-4 pt-4">
            <h2 className="text-xl md:text-2xl font-black text-gray-900 tracking-tight flex items-center gap-3">
              <Settings className="h-6 w-6" style={{ color: COLORS.purple }} />
              Module Functions & Explanations
            </h2>
            
            <div className="space-y-4">
              
              {/* Row 1 */}
              <div className="flex gap-4 p-5 rounded-2xl border border-gray-100 hover:shadow-md transition-shadow">
                <div className="h-10 w-10 rounded-xl bg-purple-50 flex items-center justify-center shrink-0">
                  <BarChart3 className="h-5 w-5 text-[#75479C]" />
                </div>
                <div>
                  <h4 className="font-bold text-gray-900 text-sm mb-1">Analytics Dashboard</h4>
                  <p className="text-xs md:text-sm text-gray-500 leading-relaxed">
                    Provides an immediate executive summary of group-wide compliance. Displays total active directors, unique companies, and compliance tracking metrics at a glance.
                  </p>
                </div>
              </div>

              {/* Row 2 */}
              <div className="flex gap-4 p-5 rounded-2xl border border-gray-100 hover:shadow-md transition-shadow">
                <div className="h-10 w-10 rounded-xl bg-blue-50 flex items-center justify-center shrink-0">
                  <Shield className="h-5 w-5 text-[#0B74B0]" />
                </div>
                <div>
                  <h4 className="font-bold text-gray-900 text-sm mb-1">Institutional Risk Monitor</h4>
                  <p className="text-xs md:text-sm text-gray-500 leading-relaxed">
                    Flags overboarding exposure by counting board positions. It separates public and private companies, ensuring the legal limits under Indian law are strictly respected.
                  </p>
                </div>
              </div>

              {/* Row 3 */}
              <div className="flex gap-4 p-5 rounded-2xl border border-gray-100 hover:shadow-md transition-shadow">
                <div className="h-10 w-10 rounded-xl bg-purple-50 flex items-center justify-center shrink-0">
                  <Network className="h-5 w-5 text-[#75479C]" />
                </div>
                <div>
                  <h4 className="font-bold text-gray-900 text-sm mb-1">Registry Intelligence</h4>
                  <p className="text-xs md:text-sm text-gray-500 leading-relaxed">
                    Maps complex networks of business relationships. It tracks the interlock of directors across both internal subsidiaries and external target entities.
                  </p>
                </div>
              </div>

              {/* Row 4 */}
              <div className="flex gap-4 p-5 rounded-2xl border border-gray-100 hover:shadow-md transition-shadow">
                <div className="h-10 w-10 rounded-xl bg-blue-50 flex items-center justify-center shrink-0">
                  <Database className="h-5 w-5 text-[#0B74B0]" />
                </div>
                <div>
                  <h4 className="font-bold text-gray-900 text-sm mb-1">Directors Master Data</h4>
                  <p className="text-xs md:text-sm text-gray-500 leading-relaxed">
                    Your central repository of personal credentials, containing full names, PAN numbers, active/inactive statuses, profile photos, and emergency contact registries.
                  </p>
                </div>
              </div>

              {/* Row 5 */}
              <div className="flex gap-4 p-5 rounded-2xl border border-gray-100 hover:shadow-md transition-shadow">
                <div className="h-10 w-10 rounded-xl bg-purple-50 flex items-center justify-center shrink-0">
                  <FileText className="h-5 w-5 text-[#75479C]" />
                </div>
                <div>
                  <h4 className="font-bold text-gray-900 text-sm mb-1">Disclosure Repository</h4>
                  <p className="text-xs md:text-sm text-gray-500 leading-relaxed">
                    The operational workspace for statutory disclosures. Access current MBP-1 and DIR-8 files, manage file uploads, and view the change log history of compliance updates.
                  </p>
                </div>
              </div>

            </div>
          </section>

          {/* FAQ Section */}
          <section className="space-y-4 pt-4">
            <h2 className="text-xl md:text-2xl font-black text-gray-900 tracking-tight flex items-center gap-3">
              <HelpCircle className="h-6 w-6" style={{ color: COLORS.purple }} />
              Frequently Asked Questions
            </h2>
            <div className="mt-4">
              {faqs.map((item, idx) => (
                <FAQAccordion key={idx} item={item} index={idx} />
              ))}
            </div>
          </section>

        </div>

        {/* Right column - Side Summary / Quick Reference */}
        <div className="space-y-6">
          <Card className="rounded-[1.8rem] border border-gray-100 shadow-sm overflow-hidden bg-gray-50/50">
            <CardHeader className="bg-white border-b border-gray-100 p-6">
              <CardTitle className="text-lg font-black text-gray-900 tracking-tight">
                Quick Compliance Sheet
              </CardTitle>
              <CardDescription>
                Statutory limits as per Companies Act, 2013
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6 space-y-5">
              
              <div>
                <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest block mb-1">Total Directorships</span>
                <span className="text-xl font-bold text-gray-900">Max 20 Companies</span>
                <p className="text-[10px] text-gray-500 mt-0.5">Includes both public and private entities, excluding foreign and section 8 entities.</p>
              </div>

              <div>
                <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest block mb-1">Public Company Limit</span>
                <span className="text-xl font-bold text-gray-900">Max 10 Public Companies</span>
                <p className="text-[10px] text-gray-500 mt-0.5">Directorships in private companies that are holding/subsidiaries of a public company count toward this limit.</p>
              </div>

              <div>
                <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest block mb-1">DIR-3 KYC Filing</span>
                <span className="text-xl font-bold text-gray-900">Annual Requirement</span>
                <p className="text-[10px] text-gray-500 mt-0.5">Must be filed by September 30th of every financial year for each active DIN holder.</p>
              </div>

              <div>
                <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest block mb-1">MBP-1 Interest Filing</span>
                <span className="text-xl font-bold text-gray-900">First Board Meeting</span>
                <p className="text-[10px] text-gray-500 mt-0.5">Every director must submit disclosure of interest in Form MBP-1 at the first board meeting of each financial year or whenever changes occur.</p>
              </div>

            </CardContent>
          </Card>

          {/* Quick Help Card */}
          <div 
            className="p-6 rounded-[1.8rem] border shadow-sm text-white relative overflow-hidden"
            style={{ background: `linear-gradient(135deg, ${COLORS.blue} 0%, #0369a1 100%)` }}
          >
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full blur-xl" />
            <h4 className="font-bold text-base mb-2">Need Support?</h4>
            <p className="text-xs text-blue-100 leading-relaxed mb-4">
              If you discover a discrepancy between the system's board count and physical records, or if an MCA sync fails, please contact the Secretarial Support Desk.
            </p>
            <div className="text-[10px] font-black tracking-widest uppercase text-blue-200">
              INTERNAL DISCLOSURE HELPLINE
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default DirectorsDisclosureUserGuide;
