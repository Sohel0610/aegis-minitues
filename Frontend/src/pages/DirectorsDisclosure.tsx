import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import { FileText, Database, BarChart3, Home, FileSpreadsheet, History, Network, Shield, BookOpen, Settings } from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import DirectorsDisclosureDataSource from "./DirectorsDisclosure/DirectorsDisclosureDataSource";
import DirectorsDisclosureAnalytics from "./DirectorsDisclosure/DirectorsDisclosureAnalytics";
import DirectorsDisclosureMasterData from "./DirectorsDisclosure/DirectorsDisclosureMasterData";
import DirectorsDisclosureCompaniesMasterData from "./DirectorsDisclosure/DirectorsDisclosureCompaniesMasterData";
import DirectorDisclosureChanges from "./DirectorsDisclosure/DirectorDisclosureChanges";
import DirectorRegistryIntelligence from "./DirectorsDisclosure/DirectorRegistryIntelligence";
import InstitutionalRiskMonitor from "./DirectorsDisclosure/InstitutionalRiskMonitor";
import RegistryManagement from "./DirectorsDisclosure/RegistryManagement";
import DirectorsDisclosureUserGuide from "./DirectorsDisclosure/DirectorsDisclosureUserGuide";

type TabType = 'analytics' | 'datasource' | 'masterdata' | 'companies';

const DirectorsDisclosure = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // Define navigation items for this product using useMemo to prevent unnecessary re-renders
  const navigationItems = useMemo(() => {
    // Get the current path without query params or hash
    const currentPath = location.pathname;

    return [
      {
        id: 'home',
        label: 'Home',
        icon: Home,
        href: '/',
        isActive: false
      },
      {
        id: 'registry-management',
        label: 'Registry control center',
        icon: Settings,
        href: '/directors-disclosure/registry-management',
        isActive: currentPath.endsWith('/registry-management')
      },
      {
        id: 'analytics',
        label: 'Analytics',
        icon: BarChart3,
        href: '/directors-disclosure/analytics',
        isActive: currentPath === '/directors-disclosure' || currentPath === '/directors-disclosure/' || currentPath.endsWith('/analytics')
      },
      {
        id: 'institutional-risk',
        label: 'Institutional risk',
        icon: Shield,
        href: '/directors-disclosure/institutional-risk',
        isActive: currentPath.endsWith('/institutional-risk')
      },
      {
        id: 'intelligence',
        label: 'Registry intelligence',
        icon: Network,
        href: '/directors-disclosure/registry-intelligence',
        isActive: currentPath.endsWith('/registry-intelligence')
      },
      {
        id: 'masterdata',
        label: 'Directors master data',
        icon: Database,
        href: '/directors-disclosure/master-data',
        isActive: currentPath.endsWith('/master-data')
      },
      {
        id: 'companies',
        label: 'Companies master list',
        icon: FileSpreadsheet,
        href: '/directors-disclosure/companies-master-data',
        isActive: currentPath.endsWith('/companies-master-data')
      },
      {
        id: 'changes',
        label: 'Director disclosure history',
        icon: History,
        href: '/directors-disclosure/changes',
        isActive: currentPath.endsWith('/changes')
      },
      {
        id: 'repository',
        label: 'Disclosure Repository',
        icon: FileText,
        href: '/directors-disclosure/repository',
        isActive: currentPath.endsWith('/repository')
      },
      {
        id: 'user-guide',
        label: 'User Guide & Docs',
        icon: BookOpen,
        href: '/directors-disclosure/user-guide',
        isActive: currentPath.endsWith('/user-guide')
      }
    ];
  }, [location.pathname]);

  const renderContent = () => {
    // Determine active tab based on current route
    if (location.pathname.endsWith('/repository')) {
      return <DirectorsDisclosureDataSource />;
    } else if (location.pathname.endsWith('/master-data')) {
      return <DirectorsDisclosureMasterData />;
    } else if (location.pathname.endsWith('/analytics')) {
      return <DirectorsDisclosureAnalytics />;
    } else if (location.pathname.endsWith('/companies-master-data')) {
      return <DirectorsDisclosureCompaniesMasterData />;
    } else if (location.pathname.endsWith('/changes')) {
      return <DirectorDisclosureChanges />;
    } else if (location.pathname.endsWith('/registry-intelligence')) {
      return <DirectorRegistryIntelligence />;
    } else if (location.pathname.endsWith('/institutional-risk')) {
      return <InstitutionalRiskMonitor />;
    } else if (location.pathname.endsWith('/registry-management')) {
      return <RegistryManagement />;
    } else if (location.pathname.endsWith('/user-guide')) {
      return <DirectorsDisclosureUserGuide />;
    } else {
      // Default to Analytics
      return <DirectorsDisclosureAnalytics />;
    }
  };

  useEffect(() => {
    // Redirect root to analytics to maintain consistency with sidebar highlighting
    if (location.pathname === '/directors-disclosure' || location.pathname === '/directors-disclosure/') {
      navigate('/directors-disclosure/analytics', { replace: true });
    }
  }, [location.pathname, navigate]);

  return (
    <ProductDashboardLayout
      productName="Directors' Disclosure Agent"
      productRoute="/directors-disclosure"
      navigationItems={navigationItems}
    >
      <div className="container mx-auto py-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          {renderContent()}
        </motion.div>
      </div>
    </ProductDashboardLayout>
  );
};

export default DirectorsDisclosure;