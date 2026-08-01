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
import SEBIAnalysisDashboardLayout from '@/components/layout/SEBIAnalysisDashboardLayout';

// ─── Adani Brand Tokens ──────────────────────────────────────
const BRAND = {
    blue: '#005DA4',
    blueLight: '#0B74B0',
    bluePale: '#E8F4FD',
    maroon: '#BD3861',
    maroonDeep: '#8B2647',
    maroonPale: '#FDE8EF',
    gradient: 'linear-gradient(135deg, #BD3861 0%, #8B2647 100%)',
    gradientSoft: 'linear-gradient(135deg, #FDE8EF 0%, #E8F4FD 100%)',
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
        icon: Shield,
        title: 'SEBI Dashboard',
        route: '/sebi-dashboard',
        description: 'Comprehensive monitoring tool for SEBI regulations, market surveillance updates, and listing agreement compliance.',
        features: [
            'Real-time SEBI circular tracking',
            'Market surveillance insights',
            'Listing agreement compliance checks',
            'Interactive regulatory trend charts',
            'Centralized regulatory update feed'
        ],
        color: BRAND.maroon,
    },
    {
        icon: Bell,
        title: 'Total Notifications',
        route: '/sebi-notifications',
        description: 'Archive of all SEBI notifications, press releases, and legal orders processed by the AEGIS platform.',
        features: [
            'Historical SEBI order archive',
            'Advanced keyword search',
            'Filter by notification type (LODR, ICDR, etc.)',
            'Detailed timeline of regulatory changes',
            'Export feature for audit trails'
        ],
        color: BRAND.maroonDeep,
    },
    {
        icon: Mail,
        title: 'Email Data',
        route: '/sebi-emaildata',
        description: 'Audit and review system-generated email alerts related to critical SEBI regulatory transitions.',
        features: [
            'Automated email notification logs',
            'Delivery status monitoring',
            'Alert content verification',
            'Recipient tracking by role',
            'Search across historical alerts'
        ],
        color: BRAND.blue,
    }
];

const gettingStartedSteps: StepInfo[] = [
    {
        step: 1,
        icon: Zap,
        title: 'Initial Access',
        description: 'Enter the AEGIS platform via Single Sign-On. Ensure you have the "SEBI Analysis" role assigned.'
    },
    {
        step: 2,
        icon: Eye,
        title: 'Select SEBI Module',
        description: 'Locate the SEBI Analysis card on the landing page and click "Launch" to enter the module.'
    },
    {
        step: 3,
        icon: LayoutDashboard,
        title: 'Analyse Dashboard',
        description: 'Review high-level metrics on market regulations and recent SEBI filings on the main dashboard.'
    },
    {
        step: 4,
        icon: Filter,
        title: 'Custom Search',
        description: 'Use specialized filters to find regulations that impact specific business units or listing categories.'
    }
];

const featureHighlights = [
    {
        icon: Activity,
        title: 'Market Surveillance',
        description: 'Track SEBI surveillance updates and regulatory actions in real-time to mitigate market risks.'
    },
    {
        icon: Users,
        title: 'Investor Protection',
        description: 'Stay updated on SEBI directives related to investor education and protection measures.'
    },
    {
        icon: FileText,
        title: 'LODR Compliance',
        description: 'Monitor Listing Obligations and Disclosure Requirements (LODR) updates and their specific mandates.'
    },
    {
        icon: Globe,
        title: 'Corporate Governance',
        description: 'Track changes in corporate governance norms and reporting requirements issued by SEBI.'
    },
    {
        icon: CheckCircle2,
        title: 'Filing Tracking',
        description: 'Monitor the status and timelines of mandatory regulatory filings and disclosures.'
    },
    {
        icon: TrendingUp,
        title: 'Impact Analysis',
        description: 'Visualise regulatory trends to understand the evolving landscape of Indian capital markets.'
    }
];

const faqData: FAQItem[] = [
    {
        question: 'What SEBI data sources are integrated?',
        answer: 'AEGIS monitors SEBI\'s official website, circular feeds, and legal order repositories to ensure data completeness and accuracy.'
    },
    {
        question: 'How do I track LODR amendments?',
        answer: 'You can use the search bar in the "Total Notifications" section to search for "LODR" or filter notifications by the "Listing Agreement" category.'
    },
    {
        question: 'Can I see SEBI orders against companies?',
        answer: 'Yes, the system captures SEBI orders, adjudication proceedings, and settlement orders, providing a detailed summary and original links.'
    },
    {
        question: 'Is there an alert system for new SEBI circulars?',
        answer: 'Yes, AEGIS sends automated email alerts to designated compliance officers as soon as a new high-priority SEBI notification is detected.'
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
                border: `1px solid ${isOpen ? BRAND.maroon : '#E2E8F0'}`,
                background: isOpen ? BRAND.maroonPale : BRAND.white,
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
                    ? <ChevronUp size={18} style={{ color: BRAND.maroon, flexShrink: 0 }} />
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
                background: BRAND.maroonPale,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
            }}>
                <Icon size={20} style={{ color: BRAND.maroon }} />
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

const SEBIUserGuide = () => {
    useEffect(() => {
        window.scrollTo(0, 0);
    }, []);

    return (
        <SEBIAnalysisDashboardLayout>
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
                    {/* Decorative circles */}
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
                                SEBI User Guide
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
                            Learn how to leverage the <strong>SEBI Analysis</strong> module to monitor market
                            regulations, LODR compliance, and investor protection directives.
                        </motion.p>
                    </div>
                </motion.div>

                {/* ─── Content Container ────────────────────────────── */}
                <div style={{ maxWidth: 900, margin: '0 auto', padding: '48px 24px 80px' }}>

                    {/* ─── SECTION: Platform Overview ─────────────────── */}
                    <section id="section-overview" style={{ marginBottom: 64 }}>
                        <SectionHeader
                            icon={Info}
                            title="Module Overview"
                            subtitle="Specialized analysis for capital market regulations."
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
                                The <strong>SEBI Analysis</strong> module provides a specialized lens into the regulatory landscape of the
                                Securities and Exchange Board of India. It helps compliance teams track market surveillance actions,
                                new disclosure requirements, and corporate governance updates that affect listed entities.
                            </p>
                        </motion.div>
                    </section>

                    {/* ─── SECTION: Getting Started ──────────────────── */}
                    <section id="section-getting-started" style={{ marginBottom: 64 }}>
                        <SectionHeader
                            icon={ArrowRight}
                            title="Getting Started"
                            subtitle="Four steps to master the SEBI module."
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
                                        background: BRAND.maroonPale,
                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        marginBottom: 16
                                    }}>
                                        <step.icon size={20} style={{ color: BRAND.maroon }} />
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
                            subtitle="A guide to the SEBI module sections."
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
                            subtitle="Quick answers about the SEBI module."
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
                        <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 12, marginTop: 0 }}>Need more information?</h3>
                        <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.7)', marginBottom: 24 }}>The SEBI regulatory landscape changes frequently. Contact support for assistance.</p>
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
        </SEBIAnalysisDashboardLayout>
    );
};

export default SEBIUserGuide;
