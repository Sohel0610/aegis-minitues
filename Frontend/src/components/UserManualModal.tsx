import React from "react";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
    BookOpen,
    Settings,
    Shield,
    Database,
    FileText,
    Bell,
    Activity,
    ChevronRight,
    Info,
    HelpCircle,
    MessageSquareIcon
} from "lucide-react";

interface UserManualModalProps {
    isOpen: boolean;
    onClose: () => void;
    initialAgent?: string;
}


const UserManualModal = ({ isOpen, onClose, initialAgent }: UserManualModalProps) => {
    const allAgents = [
        {
            title: "BSE Analysis Agent",
            icon: <Activity className="h-5 w-5 text-honolulu-blue" />,
            description: "Standard Operating Procedure for monitoring BSE historical data and notifications.",
            steps: [
                "Login to AEGIS platform and navigate to 'BSE Analysis' from the main dashboard.",
                "View real-time notifications fetched daily from public BSE records via automated pipelines.",
                "Use the 'Total Notifications' tab to browse the complete chronological history of disclosures.",
                "Apply the custom date range filters to isolate specific corporate actions within a given quarter.",
                "Search for specific keywords (e.g., 'Board Meeting', 'Dividend') using the global search bar.",
                "Export filtered datasets to Excel/CSV for offline analysis and reporting to stakeholders.",
                "Monitor upcoming events and alerts automatically tracked by the system's heuristic engine."
            ]
        },
        {
            title: "RBI Analysis Agent",
            icon: <Shield className="h-5 w-5 text-dark-lavender" />,
            description: "SOP for monitoring and analyzing RBI notifications and guidelines.",
            steps: [
                "Select 'RBI Analysis' from the dashboard to view live regulatory monitoring.",
                "The dashboard displays daily, weekly, and monthly notification trends using interactive charts.",
                "Access the summary of each notification by clicking 'View' on the specific record.",
                "Download original PDF circulars directly through the provided hyperlinked source files.",
                "Use the date range filter to track historical regulatory changes over time.",
                "Review the AI-generated sentiment and compliance impact score for major circulars.",
                "The system highlights urgent notifications according to internal Adani priority rules."
            ]
        },
        {
            title: "AI Meeting Assistant",
            icon: <MessageSquareIcon className="h-5 w-5 text-indigo-500" />,
            description: "SOP for querying meeting context and transcripts using the RAG-powered AI Chatbot.",
            steps: [
                "Navigate to 'Generate Minutes' and click on 'Meeting Assistant' in the left sidebar.",
                "Upload a meeting transcript (.txt or .docx) or PDF agenda using the 'Train AI' button.",
                "Wait for the system to index the document and generate vector embeddings.",
                "Ask natural language questions like 'What were the decisions made about the Q2 budget?'.",
                "Review the AI's response, which includes precise source citations and similarity scores.",
                "Access previous chat sessions from the 'Recent Sessions' history in the sidebar.",
                "Start a 'New Chat' to clear the context window for a completely new topic."
            ]
        },
        {
            title: "Generate Minutes Workflow",
            icon: <FileText className="h-5 w-5 text-x11-maroon" />,
            description: "SOP for automated meeting documentation, agenda creation, and compliance management.",
            steps: [
                "Navigate to 'Generate Minutes' >> 'Minutes Generator' to start the workflow.",
                "Step 1: Fill in basic meeting details (Company Name, Date, Time, Quorum status).",
                "Step 2: Select the Meeting Place. If a place isn't listed, use the 'Add Place' button.",
                "Step 3: Select participating Directors from the centralized multi-select dropdown.",
                "Step 4: Draft resolutions. You can load pre-saved templates from the 'Template Resolution' tab.",
                "Step 5: Choose a master DOCX template (e.g., Q1, Q2, AGM) or upload a custom formatting template.",
                "Step 6: Click 'Generate'. The system maps all data to placeholders and creates the finalized Word document.",
                "Access the 'Meeting Minutes' tab to download, review, or delete generated files."
            ]
        },
        {
            title: "Secretarial Compliances",
            icon: <Settings className="h-5 w-5 text-honolulu-blue" />,
            description: "SOP for managing and tracking statutory compliance timelines.",
            steps: [
                "Open 'Secretarial Compliances' to view the master compliance calendar.",
                "Track upcoming statutory filings (e.g., MGT-7, AOC-4) with real-time countdowns.",
                "Click 'Add Task' to manually input new regulatory obligations or internal deadlines.",
                "Fill in the Form Name, Description, Due Date, Status, and Priority level.",
                "Update the status of ongoing tasks from 'Pending' to 'Completed' once filed.",
                "Use the interactive dashboard to visualize Completed, Upcoming, and Overdue metrics."
            ]
        },
        {
            title: "Directors' Disclosure Agent",
            icon: <Database className="h-5 w-5 text-dark-lavender" />,
            description: "SOP for tracking director interests and mandatory disclosures (MBP-1/DIR-8).",
            steps: [
                "Navigate to 'Directors\\' Disclosure' to view the centralized master database.",
                "Search by Director Name or DIN to isolate specific individual disclosures.",
                "Track changes in directorships and shareholding across various group companies.",
                "Select a specific director and click 'Generate MBP-1' or 'Generate DIR-8'.",
                "The system automatically pre-fills the statutory forms with the latest database records.",
                "Download the generated Word documents for final physical signature.",
                "Verify disclosure history through the 'Analytics' tab for trend tracking."
            ]
        },
        {
            title: "SEBI Analysis Agent",
            icon: <Activity className="h-5 w-5 text-x11-maroon" />,
            description: "SOP for monitoring SEBI regulations and compliance updates.",
            steps: [
                "Access 'SEBI Dashboard' for a high-level overview of recent regulatory updates.",
                "Navigate to 'SEBI Notifications' to view detailed circulars, orders, and master directions.",
                "Use the 'Email Data' integration to track regulatory communications and system alerts.",
                "Filter notifications by date, regulatory type, or keyword for targeted analysis.",
                "Download relevant PDF documents directly for offline compliance checks.",
                "Monitor real-time alerts for critical SEBI announcements that require immediate action."
            ]
        }
    ];

    // Filter agents if initialAgent is provided, otherwise show all
    const agents = initialAgent
        ? allAgents.filter(agent => agent.title === initialAgent)
        : allAgents;


    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-4xl h-[85vh] p-0 bg-white border border-gray-100 shadow-2xl flex flex-col overflow-hidden rounded-xl">
                {/* Header */}
                <div className="bg-white border-b border-gray-100 p-6 shrink-0 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="bg-blue-50 p-2 rounded-lg">
                            <BookOpen className="h-6 w-6 text-blue-600" />
                        </div>
                        <div>
                            <DialogTitle className="text-xl font-bold text-gray-900">User Manual & SOP</DialogTitle>
                            <DialogDescription className="text-gray-500 text-sm mt-0.5">
                                Comprehensive operating procedures for {initialAgent || "AEGIS Platform"}
                            </DialogDescription>
                        </div>
                    </div>
                </div>

                {/* Content - Scrollable Area */}
                <div className="flex-1 overflow-y-auto p-6 bg-gray-50/50 space-y-8">
                    {/* Introduction Section */}
                    <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
                        <div className="flex items-center gap-2 mb-3">
                            <Info className="h-5 w-5 text-blue-600" />
                            <h3 className="font-semibold text-gray-900">Platform Overview</h3>
                        </div>
                        <p className="text-sm text-gray-600 leading-relaxed">
                            Project AEGIS (Advanced Governance & Intimation System) is a state-of-the-art AI-powered platform designed for Adani Green Energy Limited. It automates regulatory monitoring, document generation, and compliance tracking to ensure seamless governance across group entities.
                        </p>
                    </div>

                    {/* SOP Section */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 px-1">
                            <Settings className="h-4 w-4 text-gray-400" />
                            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Standard Operating Procedures</h3>
                        </div>

                        {agents.map((agent, index) => (
                            <div key={index} className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden transition-all hover:shadow-md">
                                <div className="p-5 border-b border-gray-50 bg-white flex items-center gap-4">
                                    <div className="p-2.5 rounded-lg bg-gray-50 border border-gray-100">
                                        {agent.icon}
                                    </div>
                                    <div>
                                        <h4 className="font-bold text-gray-900">{agent.title}</h4>
                                        <p className="text-xs text-gray-500 mt-1">{agent.description}</p>
                                    </div>
                                </div>
                                <div className="p-5 bg-white">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4">
                                        {agent.steps.map((step, sIdx) => (
                                            <div key={sIdx} className="flex gap-3 items-start">
                                                <div className="h-5 w-5 rounded-full bg-blue-50 text-blue-600 text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5 border border-blue-100">
                                                    {sIdx + 1}
                                                </div>
                                                <span className="text-sm text-gray-600 leading-relaxed font-medium">{step}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Support Section */}
                    <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                        <div className="flex items-center gap-2 mb-4">
                            <HelpCircle className="h-5 w-5 text-gray-700" />
                            <h3 className="font-bold text-gray-900">Need Assistance?</h3>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                            <div>
                                <h5 className="text-xs font-bold text-blue-600 uppercase tracking-wider mb-2">Technical Support</h5>
                                <p className="text-xs text-gray-600 leading-relaxed">
                                    Contact the development team for portal malfunctions or access issues via internal support channels.
                                </p>
                            </div>
                            <div>
                                <h5 className="text-xs font-bold text-purple-600 uppercase tracking-wider mb-2">Data Accuracy</h5>
                                <p className="text-xs text-gray-600 leading-relaxed">
                                    For discrepancies in circulars or compliance data, please verify with the respective secretarial heads.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-gray-100 bg-white flex justify-end shrink-0">
                    <button
                        onClick={onClose}
                        className="px-6 py-2.5 bg-gray-900 hover:bg-gray-800 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2 shadow-sm"
                    >
                        Close Manual
                    </button>
                </div>
            </DialogContent>
        </Dialog>
    );
};

export default UserManualModal;
