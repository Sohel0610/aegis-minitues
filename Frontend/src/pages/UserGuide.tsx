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
import BSEAlertsDashboardLayout from '@/components/layout/BSEAlertsDashboardLayout';

// ─── Adani Brand Tokens ──────────────────────────────────────
const BRAND = {
  blue:        '#005DA4',
  blueLight:   '#0B74B0',
  bluePale:    '#E8F4FD',
  maroon:      '#BD3861',
  gradient:    'linear-gradient(135deg, #0B74B0 0%, #BD3861 100%)',
  gradientSoft:'linear-gradient(135deg, #E8F4FD 0%, #FDE8EF 100%)',
  black:       '#1A1A2E',
  gray:        '#64748B',
  grayLight:   '#F1F5F9',
  white:       '#FFFFFF',
  green:       '#16A34A',
  font:        "'Adani', ui-sans-serif, system-ui, sans-serif",
};

// ─── Animation Variants ──────────────────────────────────────
const fadeUp = {
  hidden:  { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.5, ease: [.22,1,.36,1] }
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
    icon: Activity,
    title: 'BSE Alerts Dashboard',
    route: '/bse-alerts',
    description: 'The main dashboard showing real-time BSE corporate announcement data with interactive charts and detailed notification tables.',
    features: [
      'Monthly, weekly, and daily trend charts',
      'Entity-wise distribution analysis',
      'Detailed notification table with search & filter',
      'Date range filtering',
      'One-click refresh for latest data'
    ],
    color: BRAND.blue,
  },
  {
    icon: Bell,
    title: 'Total Notifications',
    route: '/notifications',
    description: 'Complete historical archive of all BSE corporate announcements across all entities and time periods.',
    features: [
      'Full historical data access',
      'Advanced search across all fields',
      'Pagination for large datasets',
      'Sort by date, entity, or nature',
      'Export data capabilities'
    ],
    color: BRAND.blueLight,
  },
  {
    icon: Mail,
    title: 'Email Data',
    route: '/emaildata',
    description: 'Manage and review email notifications sent by the AEGIS system, including delivery status and recipient tracking.',
    features: [
      'Email delivery history',
      'Recipient tracking',
      'Email content preview',
      'Search by date or subject',
      'Admin management controls'
    ],
    color: BRAND.maroon,
  },
  {
    icon: Globe,
    title: 'Website Data',
    route: '/websitedata',
    description: 'Monitor data collected from BSE India website, covering corporate filings, disclosures, and regulatory updates.',
    features: [
      'Live website data feed',
      'Filing type categorization',
      'Source URL verification',
      'Data quality monitoring',
      'Admin management controls'
    ],
    color: '#16A34A',
  }
];

const gettingStartedSteps: StepInfo[] = [
  {
    step: 1,
    icon: Shield,
    title: 'Login with SSO',
    description: 'Access the platform using your Adani corporate Single Sign-On (SSO) credentials from the landing page. No separate registration is required.'
  },
  {
    step: 2,
    icon: MousePointer,
    title: 'Select BSE Analysis',
    description: 'From the landing page, click "Launch Application" on the BSE Analysis card to enter the BSE Alerts module.'
  },
  {
    step: 3,
    icon: LayoutDashboard,
    title: 'Explore the Dashboard',
    description: 'The main dashboard shows real-time charts and the latest month\'s notifications. Use the sidebar to navigate between modules.'
  },
  {
    step: 4,
    icon: Filter,
    title: 'Filter & Analyse',
    description: 'Use date range pickers, search bars, and column filters to drill down into specific announcements or time periods.'
  }
];

const featureHighlights = [
  {
    icon: BarChart3,
    title: 'Interactive Charts',
    description: 'Monthly trend, weekly distribution, and daily activity charts powered by real-time data. Hover over data points for details.'
  },
  {
    icon: Calendar,
    title: 'Date Range Filtering',
    description: 'Select custom date ranges to focus your analysis on specific time periods. Works across all data views and charts.'
  },
  {
    icon: Search,
    title: 'Smart Search',
    description: 'Search across entity names, announcement nature, and summary content to find specific corporate filings instantly.'
  },
  {
    icon: RefreshCw,
    title: 'Real-Time Refresh',
    description: 'Click the refresh button on the dashboard to pull the latest data from the BSE feed without leaving the page.'
  },
  {
    icon: Eye,
    title: 'Detailed Preview',
    description: 'Click on any notification row to open a detailed modal showing full announcement summary and a direct link to the BSE filing.'
  },
  {
    icon: Download,
    title: 'Data Export',
    description: 'Export notification data to Excel or CSV for offline reporting, compliance documentation, or further analysis.'
  }
];

const faqData: FAQItem[] = [
  {
    question: 'What is Project AEGIS?',
    answer: 'AEGIS (Adani Green Energy Intelligence System) is an enterprise-grade regulatory intelligence platform built for Adani Green Energy Limited. It aggregates, analyses, and delivers real-time regulatory notifications from BSE, SEBI, and RBI to help compliance and legal teams stay ahead of their obligations.'
  },
  {
    question: 'How often is the data updated?',
    answer: 'BSE alert data is updated automatically via scheduled background scripts that fetch the latest corporate announcements from the BSE India website. The dashboard displays the most recent data and can be manually refreshed at any time using the refresh button.'
  },
  {
    question: 'Who can access the BSE Alerts module?',
    answer: 'Access is managed through a role-based access control (RBAC) system. Your administrator can grant you access to specific modules (BSE Alerts, SEBI, RBI, etc.) from the Admin Panel. You can request access from the "Request Access" page on the landing page.'
  },
  {
    question: 'Can I export the notification data?',
    answer: 'Yes. The notification tables support exporting data to Excel format. Use the date range filter first to narrow your selection, then use the export functionality to download the filtered data.'
  },
  {
    question: 'What do the charts on the dashboard show?',
    answer: 'The Monthly Trend chart shows notification volume across months. The Weekly chart breaks down entity-level distribution. The Daily chart shows daily notification counts for the current month. All charts are interactive — hover for details.'
  },
  {
    question: 'How do I search for a specific company\'s filing?',
    answer: 'Use the search bar above the notification table on the BSE Alerts dashboard. Type the company name (entity name) or any keyword from the announcement nature or summary. The table filters in real-time as you type.'
  },
  {
    question: 'I cannot see the BSE Alerts module. What should I do?',
    answer: 'You likely don\'t have permissions yet. Visit the "Request Access" page from the landing page and submit a request for the BSE Alerts module. Your administrator will review and approve your access.'
  },
  {
    question: 'What other modules are available besides BSE Alerts?',
    answer: 'AEGIS also includes SEBI Analysis, RBI Analysis, Insider Trading monitoring, Directors\' Disclosure tracking, and a Minutes Generator for meeting documentation. Each module can be accessed from the main landing page if you have the required permissions.'
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
        border: `1px solid ${isOpen ? BRAND.blue : '#E2E8F0'}`,
        background: isOpen ? BRAND.bluePale : BRAND.white,
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
          ? <ChevronUp size={18} style={{ color: BRAND.blue, flexShrink: 0 }} />
          : <ChevronDown size={18} style={{ color: BRAND.gray, flexShrink: 0 }} />
        }
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: [.22,1,.36,1] }}
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
        background: BRAND.bluePale,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <Icon size={20} style={{ color: BRAND.blue }} />
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

// ═══════════════════════════════════════════════════════════════
// USER GUIDE PAGE
// ═══════════════════════════════════════════════════════════════
const UserGuide = () => {
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  return (
    <BSEAlertsDashboardLayout>
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
                User Guide
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
              Welcome to <strong>Project AEGIS</strong> — the Adani Green Energy Intelligence System.
              This guide will walk you through the BSE Alerts module, its features,
              and how to make the most of the platform.
            </motion.p>

            {/* Quick jump pills */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.5 }}
              style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 24 }}
            >
              {['Overview', 'Getting Started', 'Modules', 'Features', 'FAQ'].map((label) => (
                <button
                  key={label}
                  onClick={() => {
                    const el = document.getElementById(`section-${label.toLowerCase().replace(/\s/g, '-')}`);
                    el?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                  }}
                  style={{
                    padding: '8px 18px',
                    borderRadius: 20,
                    background: 'rgba(255,255,255,0.15)',
                    backdropFilter: 'blur(8px)',
                    border: '1px solid rgba(255,255,255,0.25)',
                    color: BRAND.white,
                    fontSize: 13,
                    fontWeight: 500,
                    cursor: 'pointer',
                    fontFamily: BRAND.font,
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    (e.target as HTMLElement).style.background = 'rgba(255,255,255,0.3)';
                  }}
                  onMouseLeave={(e) => {
                    (e.target as HTMLElement).style.background = 'rgba(255,255,255,0.15)';
                  }}
                >
                  {label}
                </button>
              ))}
            </motion.div>
          </div>
        </motion.div>


        {/* ─── Content Container ────────────────────────────── */}
        <div style={{ maxWidth: 900, margin: '0 auto', padding: '48px 24px 80px' }}>

          {/* ─── SECTION: Platform Overview ─────────────────── */}
          <section id="section-overview" style={{ marginBottom: 64 }}>
            <SectionHeader
              icon={Info}
              title="Platform Overview"
              subtitle="Understand what AEGIS does and why it matters for your role."
            />

            <motion.div
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              style={{
                background: BRAND.white,
                borderRadius: 16,
                border: '1px solid #E2E8F0',
                padding: 32,
                boxShadow: '0 1px 3px rgba(0,0,0,0.04)'
              }}
            >
              <motion.p variants={fadeUp} custom={0} style={{
                fontSize: 15, lineHeight: 1.8, color: BRAND.black,
                fontFamily: BRAND.font, marginBottom: 24, marginTop: 0
              }}>
                <strong>Project AEGIS</strong> is an enterprise regulatory intelligence platform built exclusively for
                <strong> Adani Green Energy Limited</strong>. It aggregates real-time corporate announcements,
                regulatory notifications, and compliance data from India's key financial regulators — <strong>BSE</strong>,
                <strong> SEBI</strong>, and <strong>RBI</strong> — into a single, unified dashboard.
              </motion.p>

              <motion.div variants={fadeUp} custom={1} style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: 16
              }}>
                {[
                  { icon: Zap,        label: 'Real-time Alerts',     desc: 'Instant push of new BSE corporate announcements' },
                  { icon: TrendingUp, label: 'Trend Analytics',      desc: 'Visual trends across daily, weekly & monthly periods' },
                  { icon: Shield,     label: 'Compliance Ready',     desc: 'Built for legal & compliance team workflows' },
                  { icon: Users,      label: 'Role-Based Access',    desc: 'Secure SSO login with fine-grained permissions' },
                ].map((item, i) => (
                  <motion.div
                    key={item.label}
                    variants={fadeUp}
                    custom={i + 2}
                    style={{
                      padding: 20,
                      borderRadius: 12,
                      background: BRAND.gradientSoft,
                      border: '1px solid #E2E8F0'
                    }}
                  >
                    <item.icon size={20} style={{ color: BRAND.blue, marginBottom: 10 }} />
                    <div style={{ fontSize: 14, fontWeight: 600, color: BRAND.black, marginBottom: 4, fontFamily: BRAND.font }}>
                      {item.label}
                    </div>
                    <div style={{ fontSize: 13, color: BRAND.gray, lineHeight: 1.5, fontFamily: BRAND.font }}>
                      {item.desc}
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            </motion.div>
          </section>


          {/* ─── SECTION: Getting Started ──────────────────── */}
          <section id="section-getting-started" style={{ marginBottom: 64 }}>
            <SectionHeader
              icon={ArrowRight}
              title="Getting Started"
              subtitle="Follow these four steps to begin using the BSE Alerts module."
            />

            <motion.div
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.2 }}
              style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 }}
            >
              {gettingStartedSteps.map((step, i) => (
                <motion.div
                  key={step.step}
                  variants={fadeUp}
                  custom={i}
                  style={{
                    padding: 24,
                    borderRadius: 16,
                    background: BRAND.white,
                    border: '1px solid #E2E8F0',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                    position: 'relative',
                    overflow: 'hidden'
                  }}
                >
                  {/* Step number badge */}
                  <div style={{
                    position: 'absolute', top: 16, right: 16,
                    width: 28, height: 28, borderRadius: '50%',
                    background: BRAND.bluePale,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 13, fontWeight: 700, color: BRAND.blue,
                    fontFamily: BRAND.font
                  }}>
                    {step.step}
                  </div>

                  <div style={{
                    width: 40, height: 40, borderRadius: 10,
                    background: BRAND.bluePale,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    marginBottom: 16
                  }}>
                    <step.icon size={20} style={{ color: BRAND.blue }} />
                  </div>

                  <h3 style={{
                    fontSize: 15, fontWeight: 600, color: BRAND.black,
                    fontFamily: BRAND.font, marginBottom: 8, marginTop: 0
                  }}>
                    {step.title}
                  </h3>
                  <p style={{
                    fontSize: 13, color: BRAND.gray, lineHeight: 1.6,
                    fontFamily: BRAND.font, margin: 0
                  }}>
                    {step.description}
                  </p>
                </motion.div>
              ))}
            </motion.div>
          </section>


          {/* ─── SECTION: Module Walkthrough ────────────────── */}
          <section id="section-modules" style={{ marginBottom: 64 }}>
            <SectionHeader
              icon={LayoutDashboard}
              title="Module Walkthrough"
              subtitle="Detailed overview of each section available in the BSE Alerts sidebar."
            />

            <motion.div
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.15 }}
              style={{ display: 'flex', flexDirection: 'column', gap: 20 }}
            >
              {modules.map((mod, i) => (
                <motion.div
                  key={mod.title}
                  variants={fadeUp}
                  custom={i}
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
                    {/* Icon + Title */}
                    <div style={{ flex: '1 1 300px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                        <div style={{
                          width: 36, height: 36, borderRadius: 8,
                          background: `${mod.color}15`,
                          display: 'flex', alignItems: 'center', justifyContent: 'center'
                        }}>
                          <mod.icon size={18} style={{ color: mod.color }} />
                        </div>
                        <div>
                          <h3 style={{
                            fontSize: 16, fontWeight: 600, color: BRAND.black,
                            fontFamily: BRAND.font, margin: 0
                          }}>
                            {mod.title}
                          </h3>
                          <span style={{
                            fontSize: 12, color: BRAND.gray, fontFamily: BRAND.font
                          }}>
                            {mod.route}
                          </span>
                        </div>
                      </div>
                      <p style={{
                        fontSize: 14, color: BRAND.gray, lineHeight: 1.7,
                        fontFamily: BRAND.font, margin: 0
                      }}>
                        {mod.description}
                      </p>
                    </div>

                    {/* Features checklist */}
                    <div style={{ flex: '1 1 240px' }}>
                      <div style={{
                        fontSize: 12, fontWeight: 600, color: BRAND.black,
                        fontFamily: BRAND.font, textTransform: 'uppercase',
                        letterSpacing: '0.05em', marginBottom: 10
                      }}>
                        Key Capabilities
                      </div>
                      <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                        {mod.features.map((feat, fi) => (
                          <li key={fi} style={{
                            display: 'flex', alignItems: 'flex-start', gap: 8,
                            marginBottom: 8, fontSize: 13, color: BRAND.gray,
                            fontFamily: BRAND.font, lineHeight: 1.5
                          }}>
                            <CheckCircle2 size={14} style={{
                              color: BRAND.green, flexShrink: 0, marginTop: 3
                            }} />
                            {feat}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          </section>


          {/* ─── SECTION: Key Features ─────────────────────── */}
          <section id="section-features" style={{ marginBottom: 64 }}>
            <SectionHeader
              icon={Zap}
              title="Key Features"
              subtitle="Powerful tools at your fingertips to analyse and act on regulatory data."
            />

            <motion.div
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.2 }}
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                gap: 16
              }}
            >
              {featureHighlights.map((feat, i) => (
                <motion.div
                  key={feat.title}
                  variants={fadeUp}
                  custom={i}
                  style={{
                    padding: 24,
                    borderRadius: 16,
                    background: BRAND.white,
                    border: '1px solid #E2E8F0',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                    transition: 'box-shadow 0.25s ease, transform 0.25s ease',
                    cursor: 'default'
                  }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLElement).style.boxShadow = '0 8px 24px rgba(0,93,164,0.1)';
                    (e.currentTarget as HTMLElement).style.transform = 'translateY(-2px)';
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLElement).style.boxShadow = '0 1px 3px rgba(0,0,0,0.04)';
                    (e.currentTarget as HTMLElement).style.transform = 'translateY(0)';
                  }}
                >
                  <div style={{
                    width: 40, height: 40, borderRadius: 10,
                    background: BRAND.bluePale,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    marginBottom: 16
                  }}>
                    <feat.icon size={20} style={{ color: BRAND.blue }} />
                  </div>
                  <h3 style={{
                    fontSize: 15, fontWeight: 600, color: BRAND.black,
                    fontFamily: BRAND.font, marginBottom: 8, marginTop: 0
                  }}>
                    {feat.title}
                  </h3>
                  <p style={{
                    fontSize: 13, color: BRAND.gray, lineHeight: 1.6,
                    fontFamily: BRAND.font, margin: 0
                  }}>
                    {feat.description}
                  </p>
                </motion.div>
              ))}
            </motion.div>
          </section>


          {/* ─── SECTION: FAQ ──────────────────────────────── */}
          <section id="section-faq" style={{ marginBottom: 64 }}>
            <SectionHeader
              icon={HelpCircle}
              title="Frequently Asked Questions"
              subtitle="Quick answers to common questions from new users."
            />

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {faqData.map((item, i) => (
                <FAQAccordion key={i} item={item} index={i} />
              ))}
            </div>
          </section>


          {/* ─── SECTION: Need Help ────────────────────────── */}
          <motion.section
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            style={{
              padding: 32,
              borderRadius: 16,
              background: BRAND.gradient,
              textAlign: 'center',
              position: 'relative',
              overflow: 'hidden'
            }}
          >
            <div style={{
              position: 'absolute', top: -30, right: -30,
              width: 150, height: 150, borderRadius: '50%',
              background: 'rgba(255,255,255,0.08)'
            }} />
            <div style={{
              position: 'absolute', bottom: -40, left: -20,
              width: 180, height: 180, borderRadius: '50%',
              background: 'rgba(255,255,255,0.05)'
            }} />

            <div style={{ position: 'relative', zIndex: 1 }}>
              <HelpCircle size={32} style={{ color: 'rgba(255,255,255,0.9)', marginBottom: 16 }} />
              <h2 style={{
                fontSize: 22, fontWeight: 700, color: BRAND.white,
                fontFamily: BRAND.font, marginBottom: 8, marginTop: 0
              }}>
                Still Have Questions?
              </h2>
              <p style={{
                fontSize: 14, color: 'rgba(255,255,255,0.85)',
                fontFamily: BRAND.font, marginBottom: 20, lineHeight: 1.6,
                maxWidth: 480, margin: '0 auto 20px'
              }}>
                Reach out to the AEGIS development team or your IT administrator for further assistance.
              </p>
              <div style={{
                display: 'inline-flex', alignItems: 'center', gap: 8,
                padding: '10px 24px', borderRadius: 10,
                background: 'rgba(255,255,255,0.2)',
                backdropFilter: 'blur(8px)',
                border: '1px solid rgba(255,255,255,0.25)',
                color: BRAND.white,
                fontSize: 14, fontWeight: 500,
                fontFamily: BRAND.font
              }}>
                <Mail size={16} />
                Contact: aegis-support@adani.com
              </div>
            </div>
          </motion.section>


          {/* ─── Footer ────────────────────────────────────── */}
          <div style={{
            marginTop: 48, paddingTop: 24,
            borderTop: '1px solid #E2E8F0',
            textAlign: 'center'
          }}>
            <p style={{
              fontSize: 12, color: BRAND.gray,
              fontFamily: BRAND.font, margin: 0
            }}>
              Powered by Adani Green Energy Limited &nbsp;•&nbsp; Project AEGIS v1.0.0
            </p>
          </div>
        </div>
      </div>
    </BSEAlertsDashboardLayout>
  );
};

export default UserGuide;
