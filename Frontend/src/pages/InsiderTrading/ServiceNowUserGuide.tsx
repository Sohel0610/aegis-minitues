import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ShieldAlert, FileCheck, AlertTriangle, TrendingUp, Users, RefreshCw, ChevronDown, ChevronRight, BookOpen, CheckCircle, XCircle, Info, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface Section {
  id: string;
  title: string;
  icon: React.ElementType;
  color: string;
  content: React.ReactNode;
}

const Accordion = ({ title, children }: { title: string; children: React.ReactNode }) => {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-gray-200 rounded-md mb-2">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 text-left text-sm font-semibold text-gray-800 hover:bg-gray-50 transition-colors"
      >
        <span>{title}</span>
        {open ? <ChevronDown className="h-4 w-4 text-gray-500" /> : <ChevronRight className="h-4 w-4 text-gray-500" />}
      </button>
      {open && <div className="px-4 pb-4 text-sm text-gray-700 border-t border-gray-100 pt-3">{children}</div>}
    </div>
  );
};

const Badge = ({ color, label }: { color: string; label: string }) => (
  <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold mr-1 ${color}`}>{label}</span>
);

const Step = ({ num, title, desc }: { num: number; title: string; desc: string }) => (
  <div className="flex gap-3 mb-4">
    <div className="flex-shrink-0 w-7 h-7 rounded-full bg-[#75479C] text-white text-xs font-bold flex items-center justify-center">{num}</div>
    <div>
      <p className="font-semibold text-gray-900 text-sm">{title}</p>
      <p className="text-gray-600 text-xs mt-0.5">{desc}</p>
    </div>
  </div>
);

const ServiceNowUserGuide = () => {
  const navigate = useNavigate();
  const [activeSection, setActiveSection] = useState("overview");

  const sections: Section[] = [
    {
      id: "overview",
      title: "Overview",
      icon: BookOpen,
      color: "#75479C",
      content: (
        <div className="space-y-5">
          <p className="text-sm text-gray-700 leading-relaxed">
            The <strong>ServiceNow PIT Compliance</strong> module is a compliance intelligence tool that
            automatically cross-checks two data sources against each other to detect potential violations of SEBI's
            Prohibition of Insider Trading (PIT) Regulations, 2015.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border border-blue-200 bg-blue-50 rounded-md p-4">
              <p className="font-semibold text-blue-900 text-sm mb-1 flex items-center gap-1.5">
                <FileCheck className="h-4 w-4" /> Source 1: ServiceNow
              </p>
              <p className="text-blue-800 text-xs leading-relaxed">
                Employee-submitted forms: yearly share holding declarations and pre-clearance requests to buy/sell company shares.
              </p>
            </div>
            <div className="border border-green-200 bg-green-50 rounded-md p-4">
              <p className="font-semibold text-green-900 text-sm mb-1 flex items-center gap-1.5">
                <Users className="h-4 w-4" /> Source 2: Depository (CDSL/NSDL)
              </p>
              <p className="text-green-800 text-xs leading-relaxed">
                Official demat account records from CDSL and NSDL showing the actual shares each person holds and their position changes over time.
              </p>
            </div>
          </div>
          <div className="border border-gray-200 rounded-md p-4 bg-gray-50">
            <p className="text-xs text-gray-600 font-semibold uppercase mb-2">The Core Idea</p>
            <p className="text-sm text-gray-700">
              By matching employees' <strong>PAN card numbers</strong> across both systems, the module flags anyone whose actual share activity in the depository does <em>not</em> match what they declared or were approved to do in ServiceNow.
            </p>
          </div>
        </div>
      ),
    },
    {
      id: "violations",
      title: "Understanding the 3 Violation Types",
      icon: AlertTriangle,
      color: "#EF4444",
      content: (
        <div className="space-y-4">
          {/* Violation 1 */}
          <div className="border border-red-200 rounded-md overflow-hidden">
            <div className="bg-red-600 text-white px-4 py-2.5 flex items-center gap-2">
              <XCircle className="h-4 w-4" />
              <span className="font-semibold text-sm">Violation 1 — Unsanctioned Trade</span>
              <Badge color="bg-red-200 text-red-900" label="HIGH SEVERITY" />
            </div>
            <div className="p-4 space-y-2">
              <p className="text-sm font-semibold text-gray-800">What it means:</p>
              <p className="text-sm text-gray-700">An employee (or their family member) bought or sold company shares, but they never submitted a pre-clearance form in ServiceNow — or their application was not approved.</p>
              <p className="text-sm font-semibold text-gray-800 mt-2">How it's detected:</p>
              <p className="text-sm text-gray-700">The system checks every person whose PAN card appears in the official shareholding records. If their share position changed but there is no matching approved permission ticket in ServiceNow, the transaction is flagged.</p>
              <p className="text-sm font-semibold text-gray-800 mt-2">Regulatory risk:</p>
              <p className="text-sm text-gray-700">Directly violates Regulation 4(1) of SEBI PIT Regulations. Can lead to investigation, trading ban, or monetary penalty.</p>
            </div>
          </div>

          {/* Violation 2 */}
          <div className="border border-orange-200 rounded-md overflow-hidden">
            <div className="bg-orange-500 text-white px-4 py-2.5 flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              <span className="font-semibold text-sm">Violation 2 — Volume Breach</span>
              <Badge color="bg-orange-200 text-orange-900" label="MEDIUM SEVERITY" />
            </div>
            <div className="p-4 space-y-2">
              <p className="text-sm font-semibold text-gray-800">What it means:</p>
              <p className="text-sm text-gray-700">An employee was approved to trade a specific number of shares (e.g. 100), but the official shareholding records show they actually traded more (e.g. 350).</p>
              <p className="text-sm font-semibold text-gray-800 mt-2">How it's detected:</p>
              <p className="text-sm text-gray-700">The quantity actually traded (as seen in the official records) is compared to the quantity approved in the ServiceNow ticket. If the actual trade exceeds the approved limit, it is flagged.</p>
              <p className="text-sm font-semibold text-gray-800 mt-2">Columns shown:</p>
              <ul className="text-sm text-gray-700 list-disc ml-4 space-y-1">
                <li><strong>Traded Volume</strong> — The actual number of shares traded.</li>
                <li><strong>Approved Volume</strong> — The number of shares the ServiceNow ticket permitted.</li>
                <li><strong>Excess Volume</strong> — How many shares were traded over the allowed limit.</li>
              </ul>
            </div>
          </div>

          {/* Violation 3 */}
          <div className="border border-amber-200 rounded-md overflow-hidden">
            <div className="bg-amber-500 text-white px-4 py-2.5 flex items-center gap-2">
              <FileCheck className="h-4 w-4" />
              <span className="font-semibold text-sm">Violation 3 — Holding Discrepancy</span>
              <Badge color="bg-amber-200 text-amber-900" label="LOW-MEDIUM SEVERITY" />
            </div>
            <div className="p-4 space-y-2">
              <p className="text-sm font-semibold text-gray-800">What it means:</p>
              <p className="text-sm text-gray-700">The number of shares an employee declared on their yearly "Self-Declaration of Shares" form in ServiceNow does not match the number shown in the official shareholding records for that PAN card and company.</p>
              <p className="text-sm font-semibold text-gray-800 mt-2">How it's detected:</p>
              <p className="text-sm text-gray-700">The declared quantity from the ServiceNow form is compared directly with the latest shareholding position from official records, for every person and company combination.</p>
              <p className="text-sm font-semibold text-gray-800 mt-2">Covers:</p>
              <p className="text-sm text-gray-700">The employee's own holdings AND their immediate relatives (spouse, parents, children) who were also declared in the form.</p>
            </div>
          </div>
        </div>
      ),
    },
    {
      id: "using",
      title: "How to Use the Dashboard",
      icon: ShieldAlert,
      color: "#75479C",
      content: (
        <div className="space-y-5">
          <Step num={1} title="Open ServiceNow Compliance" desc="In the Insider Trading module, click the 'ServiceNow Compliance' tab in the left navigation bar." />
          <Step num={2} title="Check the KPI Cards" desc="At the top, six metric cards show: total declarations, total holdings on record, pre-clearance tickets, and a count of each of the three violation types." />
          <Step num={3} title="Select a Violation Type" desc="Click one of the three buttons — 'Unsanctioned Trades', 'Volume Breaches', or 'Holding Discrepancies' — to load the matching violation records in the table below." />
          <Step num={4} title="Review the Table" desc="Each row in the table is one detected violation. You can see the employee's name, PAN, company, and the specific figures that don't match." />
          <Step num={5} title="Sync ServiceNow Data" desc="If new ServiceNow forms have been submitted, click the 'Sync ServiceNow Data' button at the top-right. This re-imports the JSON file and re-runs all compliance checks automatically." />

          <div className="mt-4 border border-blue-200 bg-blue-50 rounded-md p-4 flex items-start gap-2.5">
            <Info className="h-4 w-4 text-blue-600 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-blue-800 leading-relaxed">
              <strong>Tip:</strong> A green "Compliance Clear" state in any tab means no violations of that type were detected for the current data. This does <em>not</em> mean all employees are fully compliant — check all three tabs individually.
            </p>
          </div>
        </div>
      ),
    },
    {
      id: "data",
      title: "Where Does the Data Come From?",
      icon: RefreshCw,
      color: "#0EA5E9",
      content: (
        <div className="space-y-4">
          <p className="text-sm text-gray-700 leading-relaxed">
            This module brings together two separate sources of information that are normally kept apart:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border border-blue-200 bg-blue-50 rounded-md p-4">
              <p className="font-semibold text-blue-900 text-sm mb-2 flex items-center gap-1.5">
                <FileCheck className="h-4 w-4" /> What Employees Reported
              </p>
              <p className="text-blue-800 text-sm leading-relaxed">
                Every year, designated employees fill out two types of forms on the company's ServiceNow portal:
              </p>
              <ul className="text-blue-800 text-xs mt-2 list-disc ml-4 space-y-1">
                <li><strong>Self-Declaration of Shares</strong> — how many shares they and their family own.</li>
                <li><strong>Pre-clearance Request</strong> — asking for permission before buying or selling shares.</li>
              </ul>
            </div>
            <div className="border border-green-200 bg-green-50 rounded-md p-4">
              <p className="font-semibold text-green-900 text-sm mb-2 flex items-center gap-1.5">
                <Users className="h-4 w-4" /> What Actually Happened
              </p>
              <p className="text-green-800 text-sm leading-relaxed">
                India's official share registries (CDSL and NSDL) maintain real-time records of every share
                bought and sold in demat accounts. These records show exactly how many shares each person
                actually holds and what changed over each time period.
              </p>
            </div>
          </div>
          <div className="border border-gray-200 rounded-md p-4 bg-gray-50">
            <p className="text-xs text-gray-600 font-semibold uppercase mb-2">How They Are Connected</p>
            <p className="text-sm text-gray-700 leading-relaxed">
              Each person in India has a unique <strong>PAN card number</strong> (similar to a tax ID). The system uses this
              PAN number as the link between what an employee reported in ServiceNow and what the official
              shareholding registry shows. This matching works for both the employee themselves and any family
              members (spouse, parents, children) whose PAN numbers were declared.
            </p>
          </div>
          <div className="border border-purple-200 bg-purple-50 rounded-md p-4">
            <p className="font-semibold text-purple-900 text-sm mb-2">Companies Covered</p>
            <p className="text-purple-800 text-sm">The system currently tracks shareholding activity across six Adani Group companies:</p>
            <div className="grid grid-cols-2 gap-1 mt-2">
              {["Adani Energy Solutions", "Adani Enterprises", "Adani Green Energy", "Adani Ports (APSEZ)", "Ambuja Cements", "Sanghi Industries"].map(c => (
                <div key={c} className="flex items-center gap-1.5">
                  <CheckCircle className="h-3 w-3 text-purple-600 flex-shrink-0" />
                  <span className="text-xs text-purple-800">{c}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ),
    },
    {
      id: "faq",
      title: "FAQ",
      icon: Info,
      color: "#6B7280",
      content: (
        <div>
          <Accordion title="Why does the same employee appear multiple times?">
            Each row represents one violation per <strong>company</strong>. If an employee or family member traded shares of three different Adani companies without approval, they will appear three separate times — once for each company.
          </Accordion>
          <Accordion title="What does 'Insider Employee' mean in the Unsanctioned Trades table?">
            It means the person was identified as an insider from the shareholding records, but their name could not be directly matched to a ServiceNow account. The trade is still flagged as suspicious.
          </Accordion>
          <Accordion title="What does 'Sync ServiceNow Data' do?">
            It re-imports all the latest ServiceNow forms and re-runs all three compliance checks from scratch. Use this whenever new declaration or pre-clearance forms have been submitted by employees.
          </Accordion>
          <Accordion title="Which companies are currently tracked?">
            <ul className="list-disc ml-4 mt-1 space-y-1">
              <li>Adani Energy Solutions Limited (AESL)</li>
              <li>Adani Enterprises Limited (AEL)</li>
              <li>Adani Green Energy Limited (AGEL)</li>
              <li>Adani Ports and Special Economic Zone Limited (APSEZL)</li>
              <li>Ambuja Cements Limited</li>
              <li>Sanghi Industries Limited</li>
            </ul>
          </Accordion>
          <Accordion title="Why are some PANs flagged even though the approved quantity shows 0?">
            When an employee submitted a permission request but the approved quantity was 0 shares, it means approval was given for no trading. Any actual trade — even 1 share — then becomes a volume breach.
          </Accordion>
        </div>
      ),
    },
  ];

  const active = sections.find((s) => s.id === activeSection)!;
  const ActiveIcon = active.icon;

  return (
    <div className="min-h-screen p-4 md:p-6" style={{ background: "#ffffff" }}>
      {/* Header */}
      <div className="mb-6 border-b border-gray-100 pb-5 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <BookOpen className="h-7 w-7 text-[#75479C]" />
            ServiceNow Compliance — Guide
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            Everything you need to understand, navigate, and act on the PIT Compliance dashboard.
          </p>
        </div>
        <Button
          onClick={() => navigate('/insider-trading/servicenow')}
          className="bg-[#75479C] hover:bg-[#5a357a] text-white flex items-center gap-2 flex-shrink-0"
        >
          <ExternalLink className="h-4 w-4" />
          Open Dashboard
        </Button>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Sidebar Nav */}
        <div className="lg:w-60 flex-shrink-0">
          <div className="sticky top-4 space-y-1">
            {sections.map((s) => {
              const Icon = s.icon;
              const isActive = activeSection === s.id;
              return (
                <button
                  key={s.id}
                  onClick={() => setActiveSection(s.id)}
                  className={`w-full text-left flex items-center gap-2.5 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${isActive
                      ? "bg-[#75479C] text-white"
                      : "text-gray-700 hover:bg-gray-100"
                    }`}
                >
                  <Icon className="h-4 w-4 flex-shrink-0" />
                  <span>{s.title}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 min-w-0">
          <Card className="border rounded-md shadow-sm">
            <CardHeader className="border-b border-gray-100">
              <CardTitle className="text-base font-bold text-gray-900 flex items-center gap-2">
                <ActiveIcon className="h-5 w-5" style={{ color: active.color }} />
                {active.title}
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-5">{active.content}</CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ServiceNowUserGuide;
