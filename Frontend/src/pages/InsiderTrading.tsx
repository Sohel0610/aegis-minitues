import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import { Database, BarChart3, FileText, BookOpen, Home, ShieldAlert } from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import { InsiderTradingFilterProvider } from "@/contexts/InsiderTradingFilterContext";
import EnhancedInsiderTradingAnalytics from "./InsiderTrading/EnhancedInsiderTradingAnalytics";
import InsiderTradingDataSource from "./InsiderTrading/InsiderTradingDataSource";
import InsiderTradingMasterData from "./InsiderTrading/InsiderTradingMasterData";
import ServiceNowMasterData from "./InsiderTrading/ServiceNowMasterData";
import InsiderTradingDocumentation from "./InsiderTrading/InsiderTradingDocumentation";
import InsiderTradingUserGuide from "./InsiderTradingUserGuide";
import ServiceNowReconciliation from "./InsiderTrading/ServiceNowReconciliation";
import ServiceNowUserGuide from "./InsiderTrading/ServiceNowUserGuide";


type TabType = 'analytics' | 'datasource' | 'masterdata' | 'documentation' | 'home' | 'servicenow' | 'servicenow-guide' | 'servicenow-masterdata';

const InsiderTrading = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // Add effect to listen for documentation tab switch event
  useEffect(() => {
    const handleSwitchToDocumentation = () => {
      navigate('/insider-trading/documentation');
    };

    window.addEventListener('switchToDocumentationTab', handleSwitchToDocumentation);
    return () => {
      window.removeEventListener('switchToDocumentationTab', handleSwitchToDocumentation);
    };
  }, [navigate]);

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
        id: 'analytics',
        label: 'Analytics',
        icon: BarChart3,
        href: '/insider-trading',
        isActive: currentPath === '/insider-trading' || currentPath === '/insider-trading/'
      },
      {
        id: 'datasource',
        label: 'Data Source',
        icon: FileText,
        href: '/insider-trading/data-source',
        isActive: currentPath.endsWith('/data-source')
      },
      {
        id: 'masterdata',
        label: 'Master Data',
        icon: Database,
        href: '/insider-trading/master-data',
        isActive: currentPath.endsWith('/master-data')
      },
      {
        id: 'servicenow',
        label: 'ServiceNow Alerts',
        icon: ShieldAlert,
        href: '/insider-trading/servicenow',
        isActive: currentPath.endsWith('/servicenow')
      },
      {
        id: 'servicenow-masterdata',
        label: 'ServiceNow Master Data',
        icon: Database,
        href: '/insider-trading/servicenow-masterdata',
        isActive: currentPath.endsWith('/servicenow-masterdata')
      },
      {
        id: 'documentation',
        label: 'Documentation',
        icon: BookOpen,
        href: '/insider-trading/documentation',
        isActive: currentPath.endsWith('/documentation')
      },

      {
        id: 'servicenow-guide',
        label: 'ServiceNow Guide',
        icon: BookOpen,
        href: '/insider-trading/servicenow-guide',
        isActive: currentPath.endsWith('/servicenow-guide')
      },
      {
        id: 'user-guide',
        label: 'User Guide',
        icon: BookOpen,
        href: '/insider-trading/user-guide',
        isActive: currentPath.endsWith('/user-guide')
      }
    ];
  }, [location.pathname]);

  const renderContent = () => {
    // Determine active tab based on current route
    if (location.pathname.endsWith('/data-source')) {
      return <InsiderTradingDataSource />;
    } else if (location.pathname.endsWith('/master-data')) {
      return <InsiderTradingMasterData />;
    } else if (location.pathname.endsWith('/documentation')) {
      return <InsiderTradingDocumentation />;
    } else if (location.pathname.endsWith('/user-guide')) {
      return <InsiderTradingUserGuide />;
    }
    if (location.pathname.endsWith('/servicenow-masterdata')) {
      return <ServiceNowMasterData />;
    }
    if (location.pathname.endsWith('/servicenow')) {
      return <ServiceNowReconciliation />;
    } else if (location.pathname.endsWith('/servicenow-guide')) {
      return <ServiceNowUserGuide />;
    } else {
      // Default to analytics
      return <EnhancedInsiderTradingAnalytics />;
    }
  };

  return (
    <InsiderTradingFilterProvider>
      <ProductDashboardLayout
        productName="Insider Trading"
        productRoute="/insider-trading"
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
    </InsiderTradingFilterProvider>
  );
};

export default InsiderTrading;