import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    BookOpen,
    LayoutDashboard,
    Bell,
    Mail,
    Globe,
    BarChart3,
    Calendar,
    Search,
    Download,
    Filter,
    ChevronDown,
    ChevronUp,
    ArrowRight,
    CheckCircle2,
    Info,
    Zap,
    Shield,
    TrendingUp,
    FileText,
    Eye,
    MousePointer,
    RefreshCw,
    HelpCircle,
    ExternalLink,
    Activity,
    Users,
    Clock,
    LucideIcon
} from 'lucide-react';
import RBIAnalysisDashboardLayout from '@/components/layout/RBIAnalysisDashboardLayout';

// ─── Adani Brand Tokens ──────────────────────────────────────
const BRAND = {
    blue: '#005DA4',
    blueLight: '#0B74B0',
    bluePale: '#E8F4FD',
    maroon: '#BD3861',
    lavender: '#75479C',
    gradient: 'linear-gradient(135deg, #75479C 0%, #BD3861 100%)',
    gradientSoft: 'linear-gradient(135deg, #F5F3F7 0%, #FDE8EF 100%)',
    black: '#1A1A2E',
    gray: '#64748B',
    grayLight: '#F1F5F9',
    white: '#FFFFFF',
    green: '#16A34A',
    font: "'Adani', ui-sans-serif, system-ui, sans-serif",
};

// ─── Animation Variants ──────────────────────────────────────
const fadeUp = {
    hidden: { opacity: 0, y: 24 },
    visible: (i: number) => ({
        opacity: 1,
        y: 0,
        transition: { delay: i * 0.08, duration: 0.5, ease: [0.22, 1, 0.36, 1] as any }
    })
};

const staggerContainer = {
    hidden: {},
    visible: { transition: { staggerChildren: 0.08 } }
};

// ─── Types ───────────────────────────────────────────────────
interface FAQItem {
    question: string;
    answer: string;
}

interface ModuleInfo {
    icon: LucideIcon;
    title: string;
    route: string;
    description: string;
    features: string[];
    color: string;
}

interface StepInfo {
    step: number;
    icon: LucideIcon;
    title: string;
    description: string;
}

// ─── Data ────────────────────────────────────────────────────
const modules: ModuleInfo[] = [
    {
        icon: BarChart3,
        title: 'RBI Dashboard',
        route: '/rbi-dashboard',
        description: 'Central hub for monitoring RBI-related regulatory updates, monetary policy changes, and banking sector notifications.',
        features: [
            'Real-time RBI circular tracking',
            'Monetary policy update highlights',
            'Banking compliance trend charts',
            'Categorized regulatory alerts',
            'Advanced search & filtering'
        ],
        color: BRAND.lavender,
    },
    {
        icon: Bell,
        title: 'Total Notifications',
        route: '/rbi-notifications',
        description: 'Comprehensive historical repository of all RBI notifications, circulars, and master directions.',
        features: [
            'Full historical circular archive',
            'Search by circular number or subject',
            'Filter by notification category',
            'Sortable data by date and relevance',
            'Export capabilities for compliance records'
        ],
        color: BRAND.blueLight,
    },
    {
        icon: Mail,
        title: 'Email Data',
        route: '/rbi-emaildata',
        description: 'Track and manage automated email alerts sent to stakeholders regarding critical RBI updates.',
        features: [
            'Email transmission logs',
            'Recipient delivery verification',
            'Content preview of sent alerts',
            'Search by date or subject',
            'Stakeholder management'
        ],
        color: BRAND.maroon,
    }
];

const gettingStartedSteps: StepInfo[] = [
    {
        step: 1,
        icon: Shield,
        title: 'Secure Access',
        description: 'Log in using your corporate credentials. Access to RBI Analysis is governed by role-based permissions.'
    },
    {
        step: 2,
        icon: MousePointer,
        title: 'RBI Module Selection',
        description: 'Select "RBI Analysis" from the main landing page to view specialized banking regulatory data.'
    },
    {
        step: 3,
        icon: LayoutDashboard,
        title: 'Review Dashboard',
        description: 'Check the dashboard for the latest circulars and visual summaries of recent regulatory activity.'
    },
    {
        step: 4,
        icon: Activity,
        title: 'Analyse Circulars',
        description: 'Use the notifications section to deep-dive into specific RBI directions and their compliance impact.'
    }
];

const featureHighlights = [
    {
        icon: TrendingUp,
        title: 'Compliance Trends',
        description: 'Visualise the frequency and nature of RBI regulatory changes over time to identify focus areas.'
    },
    {
        icon: Search,
        title: 'Global Search',
        description: 'Find any RBI circular by subject, keyword, or reference number across the entire database.'
    },
    {
        icon: FileText,
        title: 'Policy Tracking',
        description: 'Keep track of changes in monetary policy, interest rate directions, and banking regulations.'
    },
    {
        icon: RefreshCw,
        title: 'Automated Sync',
        description: 'System automatically fetches the latest data from official RBI sources to ensure zero delay.'
    },
    {
        icon: Eye,
        title: 'Circular Preview',
        description: 'View summaries of notifications directly within the platform with links to original documents.'
    },
    {
        icon: Download,
        title: 'Compliance Reports',
        description: 'Download filtered sets of notifications for internal reporting and audit trails.'
    }
];

const faqData: FAQItem[] = [
    {
        question: 'How does AEGIS track RBI notifications?',
        answer: 'The system uses automated background processes to monitor official RBI channels and circular feeds. New notifications are ingested, categorized, and displayed in real-time.'
    },
    {
        question: 'Can I filter for specific types of RBI circulars?',
        answer: 'Yes, you can filter by category, date range, or use the search functionality to find circulars related to specific banking sectors or compliance themes.'
    },
    {
        question: 'Are historical RBI directions available?',
        answer: 'The "Total Notifications" section maintains a comprehensive historical archive of data processed by the AEGIS system, allowing for long-term compliance tracking.'
    },
    {
        question: 'How do I know if I have the latest data?',
        answer: 'The platform displays "Sync Status" and allows for manual refresh on the dashboard to pull the absolute latest updates from the system wide feed.'
    }
];

// ─── FAQ Accordion Component ─────────────────────────────────
const FAQAccordion = ({ item, index }: { item: FAQItem; index: number }) => {
    const [isOpen, setIsOpen] = useState(false);
    return (
        <motion.div
            custom={index}
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
            style={{
                borderRadius: 12,
                border: `1px solid ${isOpen ? BRAND.lavender : '#E2E8F0'}`,
                background: isOpen ? '#F5F3F7' : BRAND.white,
                transition: 'all 0.3s ease',
                overflow: 'hidden'
            }}
        >
            <button
                onClick={() => setIsOpen(!isOpen)}
                style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '20px 24px',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    fontFamily: BRAND.font,
                    textAlign: 'left',
                    gap: 16
                }}
            >
                <span style={{
                    fontSize: 15,
                    fontWeight: 600,
                    color: BRAND.black,
                    lineHeight: 1.5
                }}>
                    {item.question}
                </span>
                {isOpen
                    ? <ChevronUp size={18} style={{ color: BRAND.lavender, flexShrink: 0 }} />
                    : <ChevronDown size={18} style={{ color: BRAND.gray, flexShrink: 0 }} />
                }
            </button>
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3, ease: [.22, 1, .36, 1] }}
                    >
                        <div style={{
                            padding: '0 24px 20px 24px',
                            fontSize: 14,
                            lineHeight: 1.7,
                            color: BRAND.gray,
                            fontFamily: BRAND.font
                        }}>
                            {item.answer}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

// ─── Section Header Component ────────────────────────────────
const SectionHeader = ({ icon: Icon, title, subtitle }: { icon: LucideIcon; title: string; subtitle?: string }) => (
    <div style={{ marginBottom: 32 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
            <div style={{
                width: 40,
                height: 40,
                borderRadius: 10,
                background: '#F5F3F7',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
            }}>
                <Icon size={20} style={{ color: BRAND.lavender }} />
            </div>
            <h2 style={{
                fontSize: 24,
                fontWeight: 700,
                color: BRAND.black,
                fontFamily: BRAND.font,
                margin: 0
            }}>
                {title}
            </h2>
        </div>
        {subtitle && (
            <p style={{
                fontSize: 15,
                color: BRAND.gray,
                fontFamily: BRAND.font,
                margin: 0,
                paddingLeft: 52,
                lineHeight: 1.6
            }}>
                {subtitle}
            </p>
        )}
    </div>
);

const RBIUserGuide = () => {
    useEffect(() => {
        window.scrollTo(0, 0);
    }, []);

    return (
        <RBIAnalysisDashboardLayout>
            <div style={{ fontFamily: BRAND.font, background: '#FAFBFC', minHeight: '100vh' }}>

                {/* ─── Hero Banner ──────────────────────────────────── */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.6 }}
                    style={{
                        background: BRAND.gradient,
                        padding: '56px 32px 48px',
                        position: 'relative',
                        overflow: 'hidden'
                    }}
                >
                    {/* Decorative elements */}
                    <div style={{
                        position: 'absolute', top: -40, right: -40,
                        width: 200, height: 200, borderRadius: '50%',
                        background: 'rgba(255,255,255,0.08)'
                    }} />
                    <div style={{
                        position: 'absolute', bottom: -60, left: -30,
                        width: 260, height: 260, borderRadius: '50%',
                        background: 'rgba(255,255,255,0.05)'
                    }} />

                    <div style={{ maxWidth: 900, margin: '0 auto', position: 'relative', zIndex: 1 }}>
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2, duration: 0.5 }}
                            style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 16 }}
                        >
                            <div style={{
                                width: 48, height: 48, borderRadius: 12,
                                background: 'rgba(255,255,255,0.2)',
                                backdropFilter: 'blur(10px)',
                                display: 'flex', alignItems: 'center', justifyContent: 'center'
                            }}>
                                <BookOpen size={24} style={{ color: BRAND.white }} />
                            </div>
                            <h1 style={{
                                fontSize: 32,
                                fontWeight: 700,
                                color: BRAND.white,
                                fontFamily: BRAND.font,
                                margin: 0,
                                letterSpacing: '-0.02em'
                            }}>
                                RBI User Guide
                            </h1>
                        </motion.div>

                        <motion.p
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.35, duration: 0.5 }}
                            style={{
                                fontSize: 16,
                                color: 'rgba(255,255,255,0.9)',
                                fontFamily: BRAND.font,
                                margin: 0,
                                lineHeight: 1.7,
                                maxWidth: 640
                            }}
                        >
                            Master the <strong>RBI Analysis</strong> module. Learn how to track banking circulars,
                            monetary policy updates, and compliance directions efficiently.
                        </motion.p>
                    </div>
                </motion.div>

                {/* ─── Content Container ────────────────────────────── */}
                <div style={{ maxWidth: 900, margin: '0 auto', padding: '48px 24px 80px' }}>

                    {/* ─── SECTION: Overview ─────────────────── */}
                    <section id="section-overview" style={{ marginBottom: 64 }}>
                        <SectionHeader
                            icon={Info}
                            title="Module Overview"
                            subtitle="Specialized regulatory intelligence for banking and monetary policy."
                        />

                        <motion.div
                            style={{
                                background: BRAND.white,
                                borderRadius: 16,
                                border: '1px solid #E2E8F0',
                                padding: 32,
                                boxShadow: '0 1px 3px rgba(0,0,0,0.04)'
                            }}
                        >
                            <p style={{ fontSize: 15, lineHeight: 1.8, color: BRAND.black, fontFamily: BRAND.font, margin: 0 }}>
                                The <strong>RBI Analysis</strong> module within Project AEGIS is designed to streamline the monitoring of
                                Reserve Bank of India regulatory activity. It serves as a central repository for circulars, directions,
                                and press releases that impact the banking and financial services landscape.
                            </p>
                        </motion.div>
                    </section>

                    {/* ─── SECTION: Getting Started ──────────────────── */}
                    <section id="section-getting-started" style={{ marginBottom: 64 }}>
                        <SectionHeader
                            icon={ArrowRight}
                            title="Getting Started"
                            subtitle="Quick steps to begin monitoring RBI updates."
                        />

                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 }}>
                            {gettingStartedSteps.map((step, i) => (
                                <div
                                    key={step.step}
                                    style={{
                                        padding: 24,
                                        borderRadius: 16,
                                        background: BRAND.white,
                                        border: '1px solid #E2E8F0',
                                        boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                                        position: 'relative'
                                    }}
                                >
                                    <div style={{
                                        width: 40, height: 40, borderRadius: 10,
                                        background: '#F5F3F7',
                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        marginBottom: 16
                                    }}>
                                        <step.icon size={20} style={{ color: BRAND.lavender }} />
                                    </div>
                                    <h3 style={{ fontSize: 15, fontWeight: 600, color: BRAND.black, fontFamily: BRAND.font, marginBottom: 8, marginTop: 0 }}>
                                        {step.title}
                                    </h3>
                                    <p style={{ fontSize: 13, color: BRAND.gray, lineHeight: 1.6, fontFamily: BRAND.font, margin: 0 }}>
                                        {step.description}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </section>

                    {/* ─── SECTION: Module Walkthrough ────────────────── */}
                    <section id="section-modules" style={{ marginBottom: 64 }}>
                        <SectionHeader
                            icon={LayoutDashboard}
                            title="Walkthrough"
                            subtitle="Understanding the RBI module components."
                        />

                        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                            {modules.map((mod, i) => (
                                <div
                                    key={mod.title}
                                    style={{
                                        padding: 28,
                                        borderRadius: 16,
                                        background: BRAND.white,
                                        border: '1px solid #E2E8F0',
                                        boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                                        borderLeft: `4px solid ${mod.color}`
                                    }}
                                >
                                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16, flexWrap: 'wrap' }}>
                                        <div style={{ flex: '1 1 300px' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                                                <mod.icon size={20} style={{ color: mod.color }} />
                                                <h3 style={{ fontSize: 16, fontWeight: 600, color: BRAND.black, fontFamily: BRAND.font, margin: 0 }}>{mod.title}</h3>
                                            </div>
                                            <p style={{ fontSize: 14, color: BRAND.gray, lineHeight: 1.7, fontFamily: BRAND.font, margin: 0 }}>{mod.description}</p>
                                        </div>
                                        <div style={{ flex: '1 1 240px' }}>
                                            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                                                {mod.features.map((feat, fi) => (
                                                    <li key={fi} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, fontSize: 13, color: BRAND.gray, fontFamily: BRAND.font }}>
                                                        <CheckCircle2 size={14} style={{ color: BRAND.green }} />
                                                        {feat}
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </section>

                    {/* ─── SECTION: FAQ ──────────────────────────────── */}
                    <section id="section-faq" style={{ marginBottom: 64 }}>
                        <SectionHeader
                            icon={HelpCircle}
                            title="FAQ"
                            subtitle="Commonly asked questions about RBI Analysis."
                        />
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                            {faqData.map((item, i) => (
                                <FAQAccordion key={i} item={item} index={i} />
                            ))}
                        </div>
                    </section>

                    {/* ─── Support Footer ────────────────────────── */}
                    <div style={{
                        padding: 32,
                        background: BRAND.black,
                        borderRadius: 20,
                        color: BRAND.white,
                        textAlign: 'center'
                    }}>
                        <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 12, marginTop: 0 }}>Need further assistance?</h3>
                        <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.7)', marginBottom: 24 }}>Reach out to the AEGIS support team for module-specific queries.</p>
                        <button style={{
                            background: BRAND.white,
                            color: BRAND.black,
                            border: 'none',
                            padding: '10px 24px',
                            borderRadius: 30,
                            fontWeight: 600,
                            cursor: 'pointer'
                        }}>Contact Support</button>
                    </div>

                </div>
            </div>
        </RBIAnalysisDashboardLayout>
    );
};

export default RBIUserGuide;
