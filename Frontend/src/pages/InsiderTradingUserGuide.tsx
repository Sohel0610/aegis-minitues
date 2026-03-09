import { useEffect } from 'react';
import { motion } from 'framer-motion';
import {
    BookOpen,
    Search,
    TrendingDown,
    Database,
    Info,
    CheckCircle2,
    Zap,
    LayoutDashboard,
    LucideIcon,
    Globe,
    FileSpreadsheet,
    Layers,
    RefreshCw,
    Server,
    Monitor,
    Filter,
    BarChart3,
    FileText,
    SlidersHorizontal,
    ArrowLeftRight,
    Users,
    ListFilter,
    ChevronRight
} from 'lucide-react';

// ─── Adani Brand Tokens ──────────────────────────────────────
const BRAND = {
    blue: '#005DA4',
    blueLight: '#0B74B0',
    bluePale: '#E8F4FD',
    lavender: '#75479C',
    maroon: '#BD3861',
    black: '#1A1A2E',
    gray: '#64748B',
    grayLight: '#F1F5F9',
    white: '#FFFFFF',
    green: '#16A34A',
    red: '#DC2626',
    yellow: '#CA8A04',
    font: "'Adani', ui-sans-serif, system-ui, sans-serif",
    gradient: 'linear-gradient(135deg, #75479C 0%, #005DA4 100%)',
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

// ─── Types ───────────────────────────────────────────────────
interface InfoCard {
    icon: LucideIcon;
    title: string;
    description: string;
    points?: string[];
    color: string;
}

// ─── Data ────────────────────────────────────────────────────

const workflowCards: InfoCard[] = [
    {
        icon: Globe,
        title: 'InstaMUFG Portal',
        description: 'The primary gateway for sourcing depository information. Data is extracted directly from the InstaMUFG portal for each company.',
        points: [
            'Authorized access portal',
            'Company-wise data categorization',
            'Centralized report repository'
        ],
        color: BRAND.blue
    },
    {
        icon: FileSpreadsheet,
        title: 'Multi-Format Processing',
        description: 'The system handles multiple file types for comprehensive coverage of all shareholding types.',
        points: [
            'NSDL (Electronic Records)',
            'CDSL (Electronic Records)',
            'PHY (Physical Certificates)'
        ],
        color: BRAND.lavender
    },
    {
        icon: RefreshCw,
        title: 'Batch-Based Comparison',
        description: 'Each batch compares two filing dates to identify changes. Select a batch to see who entered, exited, bought more, or sold.',
        points: [
            'Date-range based comparison',
            'Identification of new entrants',
            'Tracking of exited positions'
        ],
        color: BRAND.maroon
    }
];

const dataPipeline = [
    {
        step: '01',
        title: 'Data Extraction',
        icon: Server,
        desc: 'Source files (NSDL, CDSL, PHY) are downloaded from the InstaMUFG Portal for each company.'
    },
    {
        step: '02',
        title: 'Backend Processing',
        icon: Layers,
        desc: 'The Python backend parses raw files, cleans data, compares two filing dates, and stores results as a batch.'
    },
    {
        step: '03',
        title: 'Database Storage',
        icon: Database,
        desc: 'Results are stored in PostgreSQL: summary counts and individual shareholder records per batch, company, and depository.'
    },
    {
        step: '04',
        title: 'UI Visualization',
        icon: Monitor,
        desc: 'The dashboard pulls data via filtered APIs, showing 15 records at a time with batch, company, and depository filters.'
    }
];

const filterGuide = [
    {
        icon: Layers,
        title: 'Batch',
        description: 'Select which date-range comparison to view (e.g., "25jan_01feb" = comparing 25 Jan vs 1 Feb filings). The latest batch is auto-selected.',
        color: BRAND.blue
    },
    {
        icon: Users,
        title: 'Company',
        description: 'Filter data for a specific company (e.g., Adani Enterprises, Ambuja Cements). Select "All Companies" to see aggregated data.',
        color: BRAND.lavender
    },
    {
        icon: FileSpreadsheet,
        title: 'Depository',
        description: 'Choose the depository type — CDSL (electronic), NSDL (electronic), or PHY (physical certificates).',
        color: BRAND.maroon
    }
];

const tabGuide: InfoCard[] = [
    {
        icon: BarChart3,
        title: 'Analytics Tab',
        description: 'The main dashboard showing key metrics, movement analysis cards, and a detailed table of the top 15 movers in each category.',
        points: [
            'Key Metrics: Total Investors, Net Change, Modified Positions',
            'Movement Analysis: Color-coded counts of Added, Removed, Changed, Unchanged',
            'Detailed Table: Switch between New Investors, Exits, Top Buyers, Top Sellers',
            'Each table shows the top 15 records based on position difference'
        ],
        color: BRAND.blueLight
    },
    {
        icon: FileText,
        title: 'Data Source Tab',
        description: 'Shows a per-company summary of shareholder activity. Each row shows a company × batch × depository combination with counts.',
        points: [
            'Aggregate summary cards at top (Total, Added, Removed, Changed, Unchanged)',
            'Detailed table with Company, Batch, Depository, and all counts',
            'Totals row at the bottom',
            'Search bar to filter companies by name'
        ],
        color: BRAND.lavender
    },
    {
        icon: Database,
        title: 'Master Data Tab',
        description: 'Individual shareholder records with pagination. Browse all records or filter by status.',
        points: [
            'Status filter buttons: All, Added, Removed, Changed, Unchanged (with counts)',
            'Shows 15 records per page with Previous/Next pagination',
            'Columns: PAN/GIR, Name, Older Position, Latest Position, Difference, Status, Company, Depository',
            'Search by PAN, name, email, or company'
        ],
        color: BRAND.green
    }
];

const statusGuide = [
    { status: 'ADDED', color: BRAND.green, bg: '#F0FDF4', border: '#BBF7D0', desc: 'Investor appeared in the latest filing but was NOT in the older filing. This is a new position entry.' },
    { status: 'REMOVED', color: BRAND.red, bg: '#FEF2F2', border: '#FECACA', desc: 'Investor was in the older filing but is NOT in the latest filing. They have fully exited their position.' },
    { status: 'CHANGED', color: BRAND.yellow, bg: '#FEFCE8', border: '#FEF08A', desc: 'Investor exists in both filings but their share position changed. Positive difference = bought more; negative = sold some.' },
    { status: 'UNCHANGED', color: BRAND.gray, bg: BRAND.grayLight, border: '#E2E8F0', desc: 'Investor exists in both filings and their share position is exactly the same. No trading activity detected.' }
];

// ─── Components ──────────────────────────────────────────────
const SectionHeader = ({ icon: Icon, title, subtitle, color = BRAND.blue }: { icon: LucideIcon; title: string; subtitle?: string; color?: string }) => (
    <div style={{ marginBottom: 40 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 12 }}>
            <div style={{
                width: 48, height: 48, borderRadius: 12,
                background: `${color}15`,
                display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
                <Icon size={24} style={{ color: color }} />
            </div>
            <h2 style={{ fontSize: 28, fontWeight: 800, color: BRAND.black, fontFamily: BRAND.font, margin: 0, letterSpacing: '-0.02em' }}>
                {title}
            </h2>
        </div>
        {subtitle && (
            <p style={{ fontSize: 16, color: BRAND.gray, fontFamily: BRAND.font, margin: 0, paddingLeft: 64, lineHeight: 1.6 }}>
                {subtitle}
            </p>
        )}
    </div>
);

const RegulationCard = ({ item, index }: { item: InfoCard; index: number }) => (
    <motion.div
        custom={index}
        variants={fadeUp}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.2 }}
        style={{
            background: BRAND.white,
            borderRadius: 20,
            padding: 32,
            border: '1px solid #E2E8F0',
            display: 'flex',
            flexDirection: 'column',
            gap: 20,
            boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)'
        }}
    >
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{
                width: 44, height: 44, borderRadius: 10,
                background: `${item.color}10`,
                display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
                <item.icon size={22} style={{ color: item.color }} />
            </div>
            <h3 style={{ fontSize: 18, fontWeight: 700, color: BRAND.black, margin: 0 }}>{item.title}</h3>
        </div>
        <p style={{ fontSize: 14, color: BRAND.gray, lineHeight: 1.6, margin: 0 }}>{item.description}</p>
        {item.points && (
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
                {item.points.map((p, i) => (
                    <li key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: BRAND.black, fontWeight: 500 }}>
                        <CheckCircle2 size={14} style={{ color: BRAND.green }} />
                        {p}
                    </li>
                ))}
            </ul>
        )}
    </motion.div>
);

const InsiderTradingUserGuide = () => {
    useEffect(() => {
        window.scrollTo(0, 0);
    }, []);

    return (
        <div style={{ fontFamily: BRAND.font, background: '#FAFBFC', minHeight: '100vh' }}>

            {/* ─── Hero Header ───────────────────────────────────── */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.8 }}
                style={{
                    background: BRAND.gradient,
                    padding: '80px 40px 60px',
                    position: 'relative',
                    overflow: 'hidden',
                    color: BRAND.white
                }}
            >
                <div style={{ position: 'absolute', top: -100, right: -100, width: 400, height: 400, borderRadius: '50%', background: 'rgba(255,255,255,0.05)' }} />
                <div style={{ position: 'absolute', bottom: -50, left: -50, width: 300, height: 300, borderRadius: '50%', background: 'rgba(255,255,255,0.03)' }} />

                <div style={{ maxWidth: 1100, margin: '0 auto', position: 'relative', zIndex: 1 }}>
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2, duration: 0.5 }}
                        style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24 }}
                    >
                        <div style={{
                            width: 56, height: 56, borderRadius: 16,
                            background: 'rgba(255,255,255,0.15)',
                            backdropFilter: 'blur(10px)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center'
                        }}>
                            <BookOpen size={28} />
                        </div>
                        <div>
                            <h1 style={{ fontSize: 42, fontWeight: 900, margin: 0, letterSpacing: '-0.03em' }}>Insider Trading User Guide</h1>
                            <span style={{ fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.2em', opacity: 0.7, fontWeight: 700 }}>
                                Filters • Analytics • Data Source • Master Data
                            </span>
                        </div>
                    </motion.div>

                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.35, duration: 0.5 }}
                        style={{ fontSize: 18, lineHeight: 1.7, maxWidth: 700, opacity: 0.9, margin: 0 }}
                    >
                        This guide explains how to use the Insider Trading module — from selecting filters to understanding the data shown in each tab.
                        All tabs share the same filters, and each table shows 15 records at a time.
                    </motion.p>
                </div>
            </motion.div>

            {/* ─── Main Content ─────────────────────────────────── */}
            <div style={{ maxWidth: 1100, margin: '0 auto', padding: '64px 32px 100px' }}>

                {/* ─── SECTION: Quick Start ────────────────────── */}
                <section id="quickstart" style={{ marginBottom: 80 }}>
                    <SectionHeader
                        icon={Zap}
                        title="Quick Start"
                        subtitle="Get started in 3 simple steps."
                        color={BRAND.green}
                    />

                    <div style={{
                        background: BRAND.white,
                        borderRadius: 24,
                        border: '1px solid #E2E8F0',
                        padding: 40,
                        boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)'
                    }}>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 32 }}>
                            {[
                                { step: '1', title: 'Select a Batch', desc: 'Pick a date-range comparison from the Batch dropdown. The latest batch is auto-selected when you first open the page.', icon: Layers },
                                { step: '2', title: 'Apply Filters', desc: 'Optionally narrow down by Company and/or Depository. These filters apply to ALL tabs automatically.', icon: Filter },
                                { step: '3', title: 'Explore Tabs', desc: 'Browse Analytics for top movers, Data Source for company summaries, and Master Data for individual records (15 per page).', icon: LayoutDashboard },
                            ].map((s, i) => (
                                <div key={i} style={{ display: 'flex', gap: 16 }}>
                                    <div style={{
                                        width: 48, height: 48, borderRadius: 12, flexShrink: 0,
                                        background: BRAND.gradient, color: BRAND.white,
                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        fontSize: 20, fontWeight: 900
                                    }}>
                                        {s.step}
                                    </div>
                                    <div>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                                            <s.icon size={16} style={{ color: BRAND.lavender }} />
                                            <h4 style={{ fontSize: 16, fontWeight: 700, color: BRAND.black, margin: 0 }}>{s.title}</h4>
                                        </div>
                                        <p style={{ fontSize: 14, color: BRAND.gray, lineHeight: 1.6, margin: 0 }}>{s.desc}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

                {/* ─── SECTION: Filters ────────────────────────── */}
                <section id="filters" style={{ marginBottom: 80 }}>
                    <SectionHeader
                        icon={SlidersHorizontal}
                        title="Global Filters"
                        subtitle="All three filters apply across every tab. Change a filter once, and it updates Analytics, Data Source, and Master Data simultaneously."
                        color={BRAND.blue}
                    />

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 24 }}>
                        {filterGuide.map((f, i) => (
                            <motion.div
                                key={i}
                                custom={i}
                                variants={fadeUp}
                                initial="hidden"
                                whileInView="visible"
                                viewport={{ once: true, amount: 0.2 }}
                                style={{
                                    background: BRAND.white,
                                    borderRadius: 20,
                                    padding: 32,
                                    border: '1px solid #E2E8F0',
                                    borderTop: `4px solid ${f.color}`,
                                    boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)'
                                }}
                            >
                                <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 16 }}>
                                    <div style={{
                                        width: 44, height: 44, borderRadius: 10,
                                        background: `${f.color}10`,
                                        display: 'flex', alignItems: 'center', justifyContent: 'center'
                                    }}>
                                        <f.icon size={22} style={{ color: f.color }} />
                                    </div>
                                    <h3 style={{ fontSize: 18, fontWeight: 700, color: BRAND.black, margin: 0 }}>{f.title}</h3>
                                </div>
                                <p style={{ fontSize: 14, color: BRAND.gray, lineHeight: 1.6, margin: 0 }}>{f.description}</p>
                            </motion.div>
                        ))}
                    </div>

                    <div style={{
                        marginTop: 24,
                        padding: '16px 24px',
                        background: '#EFF6FF',
                        borderRadius: 12,
                        border: '1px solid #BFDBFE',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 12
                    }}>
                        <Info size={18} style={{ color: BRAND.blue, flexShrink: 0 }} />
                        <p style={{ fontSize: 14, color: BRAND.black, margin: 0, lineHeight: 1.6 }}>
                            <strong>Tip:</strong> Use the <strong>"Clear"</strong> button to reset all filters at once.
                            Filters persist when you switch between tabs, so your selection is always maintained.
                        </p>
                    </div>
                </section>

                {/* ─── SECTION: Tabs Guide ─────────────────────── */}
                <section id="tabs" style={{ marginBottom: 80 }}>
                    <SectionHeader
                        icon={LayoutDashboard}
                        title="Tab-by-Tab Guide"
                        subtitle="Each tab serves a different purpose — from high-level metrics to individual records."
                        color={BRAND.lavender}
                    />

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
                        {tabGuide.map((tab, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, x: -20 }}
                                whileInView={{ opacity: 1, x: 0 }}
                                viewport={{ once: true }}
                                style={{
                                    background: BRAND.white,
                                    borderRadius: 20,
                                    padding: 32,
                                    border: '1px solid #E2E8F0',
                                    borderLeft: `6px solid ${tab.color}`,
                                    display: 'flex',
                                    alignItems: 'flex-start',
                                    gap: 32,
                                    flexWrap: 'wrap'
                                }}
                            >
                                <div style={{ flex: '1 1 400px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 16 }}>
                                        <tab.icon size={22} style={{ color: tab.color }} />
                                        <h3 style={{ fontSize: 20, fontWeight: 700, color: BRAND.black, margin: 0 }}>{tab.title}</h3>
                                    </div>
                                    <p style={{ fontSize: 15, color: BRAND.gray, lineHeight: 1.7, margin: 0 }}>{tab.description}</p>
                                </div>
                                <div style={{ flex: '1 1 250px', background: BRAND.grayLight, padding: 24, borderRadius: 16 }}>
                                    <h5 style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', color: BRAND.gray, marginBottom: 16, letterSpacing: '0.1em' }}>What You'll See</h5>
                                    <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 12 }}>
                                        {tab.points?.map((p, pi) => (
                                            <li key={pi} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13, color: BRAND.black, fontWeight: 500 }}>
                                                <ChevronRight size={14} style={{ color: tab.color, marginTop: 2, flexShrink: 0 }} />
                                                <span>{p}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </section>

                {/* ─── SECTION: Status Meanings ────────────────── */}
                <section id="statuses" style={{ marginBottom: 80 }}>
                    <SectionHeader
                        icon={ListFilter}
                        title="Understanding Statuses"
                        subtitle="Each shareholder record has one of four statuses, based on the comparison between two filing dates."
                        color={BRAND.maroon}
                    />

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 20 }}>
                        {statusGuide.map((s, i) => (
                            <motion.div
                                key={i}
                                custom={i}
                                variants={fadeUp}
                                initial="hidden"
                                whileInView="visible"
                                viewport={{ once: true, amount: 0.2 }}
                                style={{
                                    background: s.bg,
                                    borderRadius: 16,
                                    padding: 28,
                                    border: `1px solid ${s.border}`,
                                }}
                            >
                                <div style={{
                                    display: 'inline-flex', alignItems: 'center',
                                    padding: '4px 12px', borderRadius: 6,
                                    background: s.color, color: BRAND.white,
                                    fontSize: 12, fontWeight: 800, marginBottom: 14,
                                    letterSpacing: '0.05em'
                                }}>
                                    {s.status}
                                </div>
                                <p style={{ fontSize: 14, color: BRAND.black, lineHeight: 1.6, margin: 0 }}>{s.desc}</p>
                            </motion.div>
                        ))}
                    </div>
                </section>

                {/* ─── SECTION: Data Pipeline ────────────────── */}
                <section id="pipeline" style={{ marginBottom: 80 }}>
                    <SectionHeader
                        icon={ArrowLeftRight}
                        title="How Data Flows"
                        subtitle="From source portal to your screen — the end-to-end journey."
                        color={BRAND.blue}
                    />

                    <div style={{
                        background: BRAND.white,
                        borderRadius: 24,
                        border: '1px solid #E2E8F0',
                        padding: 40,
                        boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)'
                    }}>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 40 }}>
                            {dataPipeline.map((p, i) => (
                                <div key={i} style={{ position: 'relative' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                                        <div style={{
                                            width: 32, height: 32, borderRadius: 8,
                                            background: `${BRAND.blue}10`, color: BRAND.blue,
                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                            fontSize: 12, fontWeight: 900
                                        }}>
                                            {p.step}
                                        </div>
                                        <div style={{ height: 2, flexGrow: 1, background: BRAND.grayLight }} />
                                    </div>
                                    <div style={{ position: 'relative', zIndex: 1 }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                                            <p.icon size={18} style={{ color: BRAND.blue }} />
                                            <h4 style={{ fontSize: 16, fontWeight: 700, color: BRAND.black, margin: 0 }}>{p.title}</h4>
                                        </div>
                                        <p style={{ fontSize: 14, color: BRAND.gray, lineHeight: 1.6, margin: 0 }}>{p.desc}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

                {/* ─── SECTION: Data Ecosystem ────────────────── */}
                <section id="ecosystem" style={{ marginBottom: 80 }}>
                    <SectionHeader
                        icon={Server}
                        title="Data Sources"
                        subtitle="Where the data comes from and how multiple file formats are processed."
                        color={BRAND.lavender}
                    />

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 24 }}>
                        {workflowCards.map((card, i) => (
                            <RegulationCard key={i} item={card} index={i} />
                        ))}
                    </div>
                </section>

                {/* ─── Support Footer ──────────────────────────────── */}
                <div style={{
                    textAlign: 'center',
                    padding: '60px 40px',
                    background: BRAND.grayLight,
                    borderRadius: 32,
                    border: '1px solid #E2E8F0',
                    marginTop: 40
                }}>
                    <RefreshCw size={48} style={{ color: BRAND.blue, marginBottom: 24, marginInline: 'auto' }} />
                    <h3 style={{ fontSize: 24, fontWeight: 800, color: BRAND.black, marginBottom: 12 }}>Continuous Data Sync</h3>
                    <p style={{ fontSize: 16, color: BRAND.gray, maxWidth: 500, marginInline: 'auto', marginBottom: 0 }}>
                        The AEGIS engine processes new batches as filing data becomes available.
                        Each batch shows a snapshot comparison, and the latest batch is always selected by default.
                    </p>
                </div>

            </div>
        </div>
    );
};

export default InsiderTradingUserGuide;
