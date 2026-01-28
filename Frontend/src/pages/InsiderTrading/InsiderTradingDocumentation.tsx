import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";

const InsiderTradingDocumentation = () => {
    const [activeSection, setActiveSection] = useState("introduction");
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    const tableOfContents = [
        { id: "introduction", title: "1. Introduction" },
        { id: "purpose", title: "2. Application Purpose" },
        { id: "overview", title: "3. System Overview" },
        { id: "sources", title: "4. Data Sources" },
        { id: "frontend", title: "5. Frontend Guide" },
        { id: "backend", title: "6. Backend Architecture" },
        { id: "metrics", title: "7. Key Indicators" },
        { id: "insights", title: "8. Insights & Analysis" },
        { id: "journey", title: "9. User Journey" },
        { id: "takeaways", title: "10. Key Takeaways" },
    ];

    useEffect(() => {
        const observerOptions = {
            root: null,
            rootMargin: '-10% 0px -80% 0px',
            threshold: 0
        };

        const observerCallback = (entries: IntersectionObserverEntry[]) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    setActiveSection(entry.target.id);
                }
            });
        };

        const observer = new IntersectionObserver(observerCallback, observerOptions);

        tableOfContents.forEach(item => {
            const element = document.getElementById(item.id);
            if (element) observer.observe(element);
        });

        return () => observer.disconnect();
    }, []);

    const scrollToSection = (id: string) => {
        setIsMobileMenuOpen(false);
        const element = document.getElementById(id);
        if (element) {
            const offset = 100;
            const elementPosition = element.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.pageYOffset - offset;
            window.scrollTo({
                top: offsetPosition,
                behavior: "smooth"
            });
        }
    };

    return (
        <div className="relative flex flex-col lg:flex-row gap-8 bg-white" style={{ fontFamily: 'Adani, sans-serif' }}>
            {/* Mobile TOC Header - Sticky */}
            <div className="lg:hidden sticky top-0 z-40 bg-white border-b border-gray-200 px-4 py-3 flex justify-between items-center">
                <span className="font-bold text-sm" style={{ color: '#0B74B0' }}>User Manual Navigation</span>
                <button
                    onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                    className="px-3 py-1 bg-gray-900 text-white text-xs font-bold uppercase tracking-wider rounded"
                >
                    {isMobileMenuOpen ? "Close Menu" : "View Contents"}
                </button>
            </div>

            {/* Mobile TOC Drawer */}
            <AnimatePresence>
                {isMobileMenuOpen && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="lg:hidden fixed top-[49px] left-0 right-0 z-50 bg-white border-b-2 border-primary shadow-xl overflow-hidden max-h-[80vh] overflow-y-auto"
                    >
                        <nav className="p-4 space-y-1">
                            {tableOfContents.map((item) => (
                                <button
                                    key={item.id}
                                    onClick={() => scrollToSection(item.id)}
                                    className={`w-full text-left px-4 py-3 text-sm font-medium transition-colors border-l-4 ${activeSection === item.id
                                            ? 'bg-blue-50 text-blue-700 border-blue-600'
                                            : 'text-gray-600 border-transparent active:bg-gray-100'
                                        }`}
                                >
                                    {item.title}
                                </button>
                            ))}
                        </nav>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Desktop TOC Sidebar */}
            <aside className="hidden lg:block w-72 shrink-0">
                <div className="sticky top-28 pl-2">
                    <div className="mb-4 pb-2 border-b-2 border-[#0B74B0]/20">
                        <h3 className="text-xl font-bold uppercase tracking-tight" style={{ color: '#0B74B0' }}>Navigation</h3>
                        <p className="text-[10px] text-gray-500 font-bold uppercase tracking-[0.2em] mt-1">Manual Sections</p>
                    </div>
                    <nav className="space-y-1">
                        {tableOfContents.map((item) => (
                            <button
                                key={item.id}
                                onClick={() => scrollToSection(item.id)}
                                className={`group relative flex items-center w-full text-left px-3 py-2.5 text-xs font-bold uppercase tracking-widest transition-all ${activeSection === item.id
                                        ? 'text-blue-700 font-extrabold'
                                        : 'text-gray-400 hover:text-gray-900'
                                    }`}
                            >
                                <span className={`mr-3 w-1 h-5 transition-all ${activeSection === item.id ? 'bg-blue-600 scale-y-100' : 'bg-gray-200 scale-y-50 group-hover:scale-y-75 group-hover:bg-gray-400'
                                    }`} />
                                {item.title}
                            </button>
                        ))}
                    </nav>
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="flex-grow max-w-5xl px-4 lg:px-0 py-4 lg:py-8">
                <header className="mb-16 border-b-8 pb-10" style={{ borderColor: '#BD3861' }}>
                    <div className="flex items-center gap-3 mb-4">
                        <span className="bg-gray-900 text-white px-2 py-0.5 text-[10px] font-bold tracking-[0.3em] uppercase">Document IT-2026</span>
                        <div className="h-[1px] flex-grow bg-gray-200" />
                    </div>
                    <h1 className="text-5xl font-black mb-4 leading-tight" style={{ color: '#000000' }}>AEGIS Insider Trading System</h1>
                    <div className="flex flex-col md:flex-row md:items-center gap-4 text-justify">
                        <p className="text-2xl font-light text-gray-500 italic max-w-2xl">A comprehensive guide to surveillance, compliance, and investigative protocols.</p>
                        <div className="hidden md:block h-12 w-[1px] bg-gray-200" />
                        <div className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
                            Version 1.0.4<br />
                            Updated Jan 2026
                        </div>
                    </div>
                </header>

                {/* Introduction */}
                <section id="introduction" className="mb-24 scroll-mt-32">
                    <div className="flex items-baseline gap-4 mb-8">
                        <span className="text-4xl font-black text-gray-200 tabular-nums">01</span>
                        <h2 className="text-3xl font-bold uppercase tracking-tight" style={{ color: '#75479C' }}>Introduction</h2>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
                        <div className="md:col-span-12 lg:col-span-8 space-y-6 text-lg leading-relaxed text-gray-800">
                            <div className="p-8 bg-[#75479C]/5 border-l-4 border-[#75479C]">
                                <h4 className="text-sm font-bold uppercase tracking-[0.25em] mb-4" style={{ color: '#75479C' }}>Definition</h4>
                                <p className="font-medium">Insider trading refers to the buying or selling of a company's securities by individuals with access to material, non-public information. It maintains market integrity when conducted lawfully but becomes illegal upon violation of fiduciary duties.</p>
                            </div>

                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-12">
                                {[
                                    { title: "Market Integrity", desc: "Detects potentially illegal activities to ensure fair and transparent markets." },
                                    { title: "Investor Protection", desc: "Prevents retail investors from being disadvantaged by privileged info." },
                                    { title: "Regulatory Compliance", desc: "Ensures strict adherence to SEBI and Companies Act requirements." },
                                    { title: "Early Warning", desc: "Identifies patterns signaling upcoming material corporate events." }
                                ].map((item, i) => (
                                    <div key={i} className="group p-6 border border-gray-100 bg-white hover:border-gray-900 transition-all">
                                        <h5 className="font-black uppercase tracking-widest text-xs mb-3 flex items-center">
                                            <span className="mr-2 text-gray-300">/</span> {item.title}
                                        </h5>
                                        <p className="text-sm text-gray-600 leading-relaxed font-medium">{item.desc}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </section>

                {/* Purpose */}
                <section id="purpose" className="mb-24 scroll-mt-32">
                    <div className="flex items-baseline gap-4 mb-8">
                        <span className="text-4xl font-black text-gray-200 tabular-nums">02</span>
                        <h2 className="text-3xl font-bold uppercase tracking-tight" style={{ color: '#BD3861' }}>Application Purpose</h2>
                    </div>
                    <div className="bg-white border-2 border-gray-900 p-8 shadow-[12px_12px_0px_0px_rgba(189,56,97,0.1)]">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                            <div>
                                <h4 className="text-sm font-bold uppercase tracking-[0.2em] text-gray-400 mb-6">Core Mission</h4>
                                <p className="text-xl font-bold leading-snug">The AEGIS Insider Trading System consolidates fragmented data into actionable intelligence, reducing manual monitoring latency from hours to seconds.</p>
                            </div>
                            <div className="space-y-6">
                                {[
                                    { num: "01", text: "Automate pattern detection that is manually impossible to identify at scale." },
                                    { num: "02", text: "Create unified audit trails for regulatory compliance and physical disclosures." },
                                    { num: "03", text: "Provide cross-company liquidity insights and concentration index metrics." }
                                ].map((step, i) => (
                                    <div key={i} className="flex items-start gap-4">
                                        <span className="text-xs font-black text-[#BD3861] mt-1">{step.num}</span>
                                        <p className="text-sm border-b border-gray-100 pb-2 flex-grow font-medium">{step.text}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </section>

                {/* System Overview */}
                <section id="overview" className="mb-24 scroll-mt-32">
                    <div className="flex items-baseline gap-4 mb-8">
                        <span className="text-4xl font-black text-gray-200 tabular-nums">03</span>
                        <h2 className="text-3xl font-bold uppercase tracking-tight" style={{ color: '#0B74B0' }}>System Overview</h2>
                    </div>
                    <div className="flex flex-col gap-1">
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-1">
                            <div className="bg-gray-900 text-white p-6 flex flex-col justify-between aspect-square">
                                <span className="text-[10px] font-bold text-blue-400 uppercase tracking-widest">Logic Layer 01</span>
                                <h5 className="text-3xl font-black leading-[0.85] uppercase">Frontend Interface</h5>
                                <p className="text-[10px] font-medium leading-relaxed uppercase opacity-50">React / Tailwind / Framer Motion</p>
                            </div>
                            <div className="bg-gray-100 p-6 flex flex-col justify-between aspect-square border-x border-white">
                                <span className="text-[10px] font-bold text-purple-600 uppercase tracking-widest">Logic Layer 02</span>
                                <h5 className="text-3xl font-black leading-[0.85] uppercase text-gray-900">API Gateway</h5>
                                <p className="text-[10px] font-medium leading-relaxed uppercase opacity-50">Python FastAPI / REST Endpoints</p>
                            </div>
                            <div className="bg-blue-600 text-white p-6 flex flex-col justify-between aspect-square">
                                <span className="text-[10px] font-bold text-blue-200 uppercase tracking-widest">Logic Layer 03</span>
                                <h5 className="text-3xl font-black leading-[0.85] uppercase">Database Engine</h5>
                                <p className="text-[10px] font-medium leading-relaxed uppercase opacity-80">SQLite Persistence / Batch Processing</p>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Data Sources */}
                <section id="sources" className="mb-24 scroll-mt-32">
                    <div className="flex items-baseline gap-4 mb-8">
                        <span className="text-4xl font-black text-gray-200 tabular-nums">04</span>
                        <h2 className="text-3xl font-bold uppercase tracking-tight" style={{ color: '#75479C' }}>Data Sources</h2>
                    </div>
                    <div className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            {['CDSL', 'NSDL', 'Physical DIS'].map((source, i) => (
                                <div key={i} className="bg-gray-50 border-t-4 border-gray-900 p-6 font-bold uppercase tracking-tighter text-2xl">
                                    {source}
                                </div>
                            ))}
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-[10px] font-bold uppercase tracking-widest text-left mt-8">
                                <thead className="border-b-2 border-gray-900">
                                    <tr>
                                        <th className="py-4 px-2">Category</th>
                                        <th className="py-4 px-2">Status Code</th>
                                        <th className="py-4 px-2">Description</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                    {[
                                        { cat: "ADDED", code: "S01", desc: "New entrants in security positions", color: "text-green-600" },
                                        { cat: "REMOVED", code: "S02", desc: "Complete divestment of holdings", color: "text-red-600" },
                                        { cat: "CHANGED", code: "S03", desc: "Modification of existing position volume", color: "text-orange-600" },
                                        { cat: "UNCHANGED", code: "S00", desc: "Static holding maintenance", color: "text-gray-400" }
                                    ].map((row, i) => (
                                        <tr key={i} className="hover:bg-gray-50 transition-colors">
                                            <td className={`py-4 px-2 font-black ${row.color}`}>{row.cat}</td>
                                            <td className="py-4 px-2 text-gray-400">{row.code}</td>
                                            <td className="py-4 px-2 text-gray-600">{row.desc}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </section>

                {/* Remaining sections simplified for brevity but maintaining the premium style */}
                <section id="frontend" className="mb-24 scroll-mt-32 border-t pt-16">
                    <h3 className="text-sm font-black uppercase tracking-[0.4em] text-gray-300 mb-12">05 / Interactive Guide</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                        <div className="space-y-8">
                            <h4 className="text-4xl font-black uppercase tracking-tighter italic">Visualization Layer</h4>
                            <p className="text-sm font-medium text-gray-600 leading-relaxed border-l-4 border-blue-600 pl-6">
                                The frontend provides three primary perspectives: <strong>Analytics</strong> for macroscopic trends, <strong>Data Source</strong> for architectural fidelity, and <strong>Master Data</strong> for granular investigative search and export.
                            </p>
                        </div>
                        <div className="bg-gray-50 p-8 space-y-4">
                            <div className="text-[10px] font-black uppercase tracking-widest bg-gray-200 inline-block px-2 py-1">Feature List</div>
                            <ul className="space-y-3 font-bold text-xs uppercase italic">
                                <li>- Multi-Depository Filtering</li>
                                <li>- Position Change Timeline</li>
                                <li>- Concentration Heatmaps</li>
                                <li>- Batch Export Pipelines</li>
                            </ul>
                        </div>
                    </div>
                </section>

                <section id="metrics" className="mb-24 scroll-mt-32">
                    <div className="flex items-baseline gap-4 mb-12">
                        <span className="text-4xl font-black text-gray-200 tabular-nums">07</span>
                        <h2 className="text-3xl font-bold uppercase tracking-tight" style={{ color: '#75479C' }}>Key Indicators</h2>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {[
                            { title: "Total Records", detail: "Baseline monitoring scale" },
                            { title: "Net Share Change", detail: "Capital movement volume" },
                            { title: "Entry Volume", detail: "Confidence aggregation" },
                            { title: "Liquidity Index", detail: "Market depth assessment" }
                        ].map((metric, i) => (
                            <div key={i} className="bg-gray-50 p-6 border border-gray-200 text-center">
                                <h5 className="font-black uppercase text-sm mb-2">{metric.title}</h5>
                                <div className="h-[2px] w-8 bg-[#75479C] mx-auto mb-4" />
                                <p className="text-[10px] font-bold uppercase text-gray-400 tracking-wider">{metric.detail}</p>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Journey */}
                <section id="journey" className="mb-24 scroll-mt-32">
                    <div className="flex items-baseline gap-4 mb-8">
                        <span className="text-4xl font-black text-gray-200 tabular-nums">09</span>
                        <h2 className="text-3xl font-bold uppercase tracking-tight" style={{ color: '#0B74B0' }}>User Journey</h2>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-0 border border-gray-900 border-collapse">
                        {[
                            { step: "ACCESS", desc: "Auth & Init" },
                            { step: "ANALYZE", desc: "Macro Scrutiny" },
                            { step: "ISOLATE", desc: "Filtered Deep-dive" },
                            { step: "EXPORT", desc: "Findings Log" }
                        ].map((node, i) => (
                            <div key={i} className={`p-8 ${i < 3 ? 'md:border-r border-gray-900' : ''} ${i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                                <span className="font-black text-xs text-blue-600">0{i + 1}</span>
                                <h4 className="font-black text-xl mb-2 mt-4">{node.step}</h4>
                                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest leading-relaxed">{node.desc}</p>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Takeaways */}
                <section id="takeaways" className="mb-24 scroll-mt-32">
                    <div className="p-12 bg-gray-900 text-white rounded-n">
                        <div className="mb-8 border-b border-white/20 pb-8 flex justify-between items-end">
                            <div>
                                <span className="text-[10px] font-bold uppercase tracking-[0.5em] text-blue-400">Section 10</span>
                                <h2 className="text-5xl font-black uppercase italic">Takeaways</h2>
                            </div>
                            <div className="hidden md:block text-right">
                                <p className="text-[10px] font-bold uppercase opacity-50">Confidential Standard</p>
                                <p className="text-[10px] font-bold uppercase opacity-50">© AEGIS 2026</p>
                            </div>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 text-sm leading-relaxed font-medium">
                            <p>Information within the Insider Trading System is strictly for surveillance and compliance oversight. Users must ensure all data handled complies with the Securities and Exchange Board of India (SEBI) privacy mandates.</p>
                            <p>This surveillance engine provides decision support, not legal conclusions. Investigative protocols and human verification remain the essential final steps in all compliance escalations.</p>
                        </div>
                    </div>
                </section>

                <footer className="mt-48 pt-12 border-t-2 border-gray-100 flex flex-col md:flex-row justify-between items-center gap-6 pb-24 text-[10px] font-bold uppercase tracking-[0.2em] text-gray-400">
                    <div>AEGIS Platform Documentation Division</div>
                    <div className="flex gap-12">
                        <span>Surveillance Protocol IT-2026</span>
                        <span>Restricted Access</span>
                    </div>
                </footer>
            </main>
        </div>
    );
};

export default InsiderTradingDocumentation;
