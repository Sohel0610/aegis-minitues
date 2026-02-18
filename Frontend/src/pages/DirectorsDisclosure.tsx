import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import { FileText, Database, BarChart3, Home, FileSpreadsheet, History } from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import DirectorsDisclosureDataSource from "./DirectorsDisclosure/DirectorsDisclosureDataSource";
import DirectorsDisclosureAnalytics from "./DirectorsDisclosure/DirectorsDisclosureAnalytics";
import DirectorsDisclosureMasterData from "./DirectorsDisclosure/DirectorsDisclosureMasterData";
import DirectorsDisclosureCompaniesMasterData from "./DirectorsDisclosure/DirectorsDisclosureCompaniesMasterData";
import DirectorDisclosureChanges from "./DirectorsDisclosure/DirectorDisclosureChanges";

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
      },
      {
        id: 'masterdata',
        label: 'Directors Master Data',
        icon: Database,
        href: '/directors-disclosure',
        isActive: currentPath === '/directors-disclosure' || currentPath === '/directors-disclosure/' || currentPath.endsWith('/master-data')
      },
      {
        id: 'datasource',
        label: 'Data Source',
        icon: FileText,
        href: '/directors-disclosure/data-source',
        isActive: currentPath.endsWith('/data-source')
      },
      {
        id: 'changes',
        label: 'Director Disclosure Changes',
        icon: History,
        href: '/directors-disclosure/changes',
        isActive: currentPath.endsWith('/changes')
      },
      {
        id: 'analytics',
        label: 'Analytics',
        icon: BarChart3,
        href: '/directors-disclosure/analytics',
        isActive: currentPath.endsWith('/analytics')
      },
      {
        id: 'companies',
        label: 'Companies Master List',
        icon: FileSpreadsheet,
        href: '/directors-disclosure/companies-master-data',
        isActive: currentPath.endsWith('/companies-master-data')
      }
    ];
  }, [location.pathname]);

  const renderContent = () => {
    // Determine active tab based on current route
    if (location.pathname.endsWith('/data-source')) {
      return <DirectorsDisclosureDataSource />;
    } else if (location.pathname.endsWith('/master-data')) {
      return <DirectorsDisclosureMasterData />;
    } else if (location.pathname.endsWith('/analytics')) {
      return <DirectorsDisclosureAnalytics />;
    } else if (location.pathname.endsWith('/companies-master-data')) {
      return <DirectorsDisclosureCompaniesMasterData />;
    } else if (location.pathname.endsWith('/changes')) {
      return <DirectorDisclosureChanges />;
    } else {
      // Default to Directors Master Data
      return <DirectorsDisclosureMasterData />;
    }
  };

  return (
    <ProductDashboardLayout
      productName="Directors' Disclosure"
      productRoute="/directors-disclosure"
      navigationItems={navigationItems}
    >
      <div className="container mx-auto py-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
          <div>
            <h1 className="text-3xl font-bold">Directors' Disclosure</h1>
            <p className="text-muted-foreground">Track and analyze directors' disclosure reports</p>
          </div>
        </div>
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