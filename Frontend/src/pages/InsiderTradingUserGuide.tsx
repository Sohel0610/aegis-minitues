import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
    BookOpen,
    Search,
    FileCheck,
    TrendingDown,
    Database,
    Info,
    ArrowRight,
    CheckCircle2,
    Zap,
    LayoutDashboard,
    LucideIcon,
    Globe,
    FileSpreadsheet,
    Layers,
    RefreshCw,
    Server,
    Monitor
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
        title: 'Weekly Comparison',
        description: 'Automated weekly comparison of current files against historical data to identify deltas in shareholdings.',
        points: [
            'Delta analysis for volume changes',
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
        desc: 'Source files (NSDL, CDSL, PHY) are downloaded from the InstaMUFG Portal for each Adani portfolio company.'
    },
    {
        step: '02',
        title: 'Backend Processing',
        icon: Layers,
        desc: 'The Python backend parses the raw files, cleans data, and performs the weekly comparison logic.'
    },
    {
        step: '03',
        title: 'Database Storage',
        icon: Database,
        desc: 'Aggregated findings and individual transaction deltas are persisted in the AEGIS secure database.'
    },
    {
        step: '04',
        title: 'UI Visualization',
        icon: Monitor,
        desc: 'React-based interface pulls the processed data to visualize trends, movements, and alerts.'
    }
];

const analyticFeatures: InfoCard[] = [
    {
        icon: TrendingDown,
        title: 'Delta Analytics',
        description: 'Visual tracking of net share changes between weekly data snapshots.',
        points: ['Volume variance charts', 'Stakeholder move tracking', 'Historical comparison'],
        color: BRAND.blueLight
    },
    {
        icon: Search,
        title: 'Master Search',
        description: 'Investigative interface to search across NSDL, CDSL, and PHY records.',
        points: ['PAN-based searching', 'Company-level filtering', 'Batch export to Excel'],
        color: BRAND.lavender
    },
    {
        icon: Info,
        title: 'Status Indicators',
        description: 'Automated categorization of moves detected during the weekly comparison.',
        points: ['ADDED: New position entry', 'REMOVED: Full exit', 'CHANGED: Volume modification'],
        color: BRAND.green
    }
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
                            <h1 style={{ fontSize: 42, fontWeight: 900, margin: 0, letterSpacing: '-0.03em' }}>Insider Trading Analysis Guide</h1>
                            <span style={{ fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.2em', opacity: 0.7, fontWeight: 700 }}>
                                Data Flow • Weekly Comparison • Portfolio Monitoring
                            </span>
                        </div>
                    </motion.div>

                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.35, duration: 0.5 }}
                        style={{ fontSize: 18, lineHeight: 1.7, maxWidth: 700, opacity: 0.9, margin: 0 }}
                    >
                        A technical guide to the AEGIS Insider Trading monitoring system, focusing on
                        InstaMUFG Portal integration and weekly delta analysis of multi-depository records.
                    </motion.p>
                </div>
            </motion.div>

            {/* ─── Main Content Container ─────────────────────────── */}
            <div style={{ maxWidth: 1100, margin: '0 auto', padding: '64px 32px 100px' }}>

                {/* ─── SECTION: Data Ecosystem ────────────────── */}
                <section id="ecosystem" style={{ marginBottom: 80 }}>
                    <SectionHeader
                        icon={Server}
                        title="Data Ecosystem"
                        subtitle="The architecture of our data sourcing and multi-format file processing workflow."
                        color={BRAND.blue}
                    />

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 24 }}>
                        {workflowCards.map((card, i) => (
                            <RegulationCard key={i} item={card} index={i} />
                        ))}
                    </div>
                </section>

                {/* ─── SECTION: Data Pipeline ────────────────── */}
                <section id="pipeline" style={{ marginBottom: 80 }}>
                    <SectionHeader
                        icon={Layers}
                        title="Analysis Pipeline"
                        subtitle="The end-to-end journey from source portal extraction to UI visualization."
                        color={BRAND.lavender}
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

                {/* ─── SECTION: Software Features ──────────────────────── */}
                <section id="features" style={{ marginBottom: 80 }}>
                    <SectionHeader
                        icon={LayoutDashboard}
                        title="Software Features"
                        subtitle="Interactive tools for searching, auditing, and analyzing depository movements."
                        color={BRAND.maroon}
                    />

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
                        {analyticFeatures.map((feat, i) => (
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
                                    borderLeft: `6px solid ${feat.color}`,
                                    display: 'flex',
                                    alignItems: 'flex-start',
                                    gap: 32,
                                    flexWrap: 'wrap'
                                }}
                            >
                                <div style={{ flex: '1 1 400px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 16 }}>
                                        <feat.icon size={22} style={{ color: feat.color }} />
                                        <h3 style={{ fontSize: 20, fontWeight: 700, color: BRAND.black, margin: 0 }}>{feat.title}</h3>
                                    </div>
                                    <p style={{ fontSize: 15, color: BRAND.gray, lineHeight: 1.7, margin: 0 }}>{feat.description}</p>
                                </div>
                                <div style={{ flex: '1 1 250px', background: BRAND.grayLight, padding: 24, borderRadius: 16 }}>
                                    <h5 style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', color: BRAND.gray, marginBottom: 16, letterSpacing: '0.1em' }}>Capabilities</h5>
                                    <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 12 }}>
                                        {feat.points?.map((p, pi) => (
                                            <li key={pi} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 13, color: BRAND.black, fontWeight: 500 }}>
                                                <Zap size={14} style={{ color: feat.color }} />
                                                {p}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            </motion.div>
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
                        The AEGIS engine performs weekly synchronizations to ensure the most current
                        depository data is reflected in our analytics suite.
                    </p>
                </div>

            </div>
        </div>
    );
};

export default InsiderTradingUserGuide;
