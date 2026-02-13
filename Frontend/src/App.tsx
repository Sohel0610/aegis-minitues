import { Toaster } from "@/components/ui/toaster";
import { Toaster as SonnerToaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import LandingPage from "./pages/LandingPage";
import Dashboard from "./pages/Dashboard";
import TotalNotifications from "./pages/TotalNotifications";
import EmailData from "./pages/EmailData";
import WebsiteData from "./pages/WebsiteData";
import WorkbookData from "./pages/WorkbookData";
import TotalWorkbookNotifications from "./pages/TotalWorkbookNotifications";
import WeeklyAnalysis from "./pages/WeeklyAnalysis";
import NotFound from "./pages/NotFound";
import ExcelDataPage from "./pages/ExcelDataPage";

// Import financial analysis pages (future products)
import BSEIndiaAnalysis from "./pages/BSEIndiaAnalysis";
import RBIAnalysis from "./pages/RBIAnalysis";
import InsiderTrading from "./pages/InsiderTrading";
import DirectorsDisclosure from "./pages/DirectorsDisclosure";
import MinutesPreparation from "./pages/MinutesPreparation";
import FormBasedGenerator from "./pages/minutes-preparation/FormBasedGenerator";
import AIAssistant from "./pages/minutes-preparation/AIAssistant";

// Import SEBI specific pages
import SEBIDashboard from "./pages/SEBIDashboard";
import SEBITotalNotifications from "./pages/SEBITotalNotifications";
import SEBIEmailData from "./pages/SEBIEmailData";

// Import RBI specific pages
import RBIDashboard from "./pages/RBIDashboard";
import RBITotalNotifications from "./pages/RBITotalNotifications";
import RBIEmailData from "./pages/RBIEmailData";

// Import product-specific dashboard layouts
import BSEAlertsDashboardLayout from "@/components/layout/BSEAlertsDashboardLayout";
import RBIAnalysisDashboardLayout from "@/components/layout/RBIAnalysisDashboardLayout";
import HierarchyStructure from "./pages/HierarchyStructure";

// Import Directors Disclosure sub-pages
import DirectorsDisclosureAnalytics from "./pages/DirectorsDisclosure/DirectorsDisclosureAnalytics";
import DirectorsDisclosureCompaniesMasterData from "./pages/DirectorsDisclosure/DirectorsDisclosureCompaniesMasterData";
import DirectorsDisclosureMasterData from "./pages/DirectorsDisclosure/DirectorsDisclosureMasterData";
import DirectorsDisclosureDataSource from "./pages/DirectorsDisclosure/DirectorsDisclosureDataSource";

// Import RBAC pages
import { AccessRequest } from "./pages/AccessRequest";
import { AdminPanel } from "./pages/AdminPanel";
import { AccessDenied } from "./components/RouteGuard";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <SonnerToaster />
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* Main landing page */}
            <Route path="/" element={<LandingPage />} />

            {/* RBAC routes */}
            <Route path="/access-request" element={<AccessRequest />} />
            <Route path="/access-denied" element={<AccessDenied />} />
            <Route path="/admin-panel" element={<AdminPanel />} />

            {/* Current BSE India Analysis routes (main product) */}
            <Route path="/bse-alerts" element={
              <ProtectedRoute requiredRoute="/bse-alerts">
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/notifications" element={
              <ProtectedRoute requiredRoute="/bse-alerts">
                <TotalNotifications />
              </ProtectedRoute>
            } />
            <Route path="/emaildata" element={
              <ProtectedRoute requiredRoute="/bse-alerts">
                <EmailData />
              </ProtectedRoute>
            } />
            <Route path="/websitedata" element={
              <ProtectedRoute requiredRoute="/bse-alerts">
                <WebsiteData />
              </ProtectedRoute>
            } />
            <Route path="/workbook-data" element={
              <ProtectedRoute requiredRoute="/bse-alerts">
                <WorkbookData />
              </ProtectedRoute>
            } />
            <Route path="/total-workbook-notifications" element={
              <ProtectedRoute requiredRoute="/bse-alerts">
                <TotalWorkbookNotifications />
              </ProtectedRoute>
            } />
            <Route path="/weekly-analysis" element={
              <ProtectedRoute requiredRoute="/bse-alerts">
                <WeeklyAnalysis />
              </ProtectedRoute>
            } />

            {/* SEBI Analysis routes */}
            <Route path="/sebi-dashboard" element={
              <ProtectedRoute requiredRoute="/sebi-dashboard">
                <SEBIDashboard />
              </ProtectedRoute>
            } />
            <Route path="/sebi-notifications" element={
              <ProtectedRoute requiredRoute="/sebi-dashboard">
                <SEBITotalNotifications />
              </ProtectedRoute>
            } />
            <Route path="/sebi-emaildata" element={
              <ProtectedRoute requiredRoute="/sebi-dashboard">
                <SEBIEmailData />
              </ProtectedRoute>
            } />

            {/* RBI Analysis routes */}
            <Route path="/rbi-analysis" element={
              <ProtectedRoute requiredRoute="/rbi-dashboard">
                <RBIAnalysis />
              </ProtectedRoute>
            } />
            <Route path="/rbi-dashboard" element={
              <ProtectedRoute requiredRoute="/rbi-dashboard">
                <RBIDashboard />
              </ProtectedRoute>
            } />
            <Route path="/rbi-notifications" element={
              <ProtectedRoute requiredRoute="/rbi-dashboard">
                <RBITotalNotifications />
              </ProtectedRoute>
            } />
            <Route path="/rbi-emaildata" element={
              <ProtectedRoute requiredRoute="/rbi-dashboard">
                <RBIEmailData />
              </ProtectedRoute>
            } />

            {/* Excel Data page */}
            <Route path="/excel-data" element={
              <ProtectedRoute requiredRoute="/bse-alerts">
                <ExcelDataPage />
              </ProtectedRoute>
            } />

            {/* Future product routes */}
            <Route path="/insider-trading/*" element={
              <ProtectedRoute requiredRoute="/insider-trading">
                <InsiderTrading />
              </ProtectedRoute>
            } />
            <Route path="/directors-disclosure/*" element={
              <ProtectedRoute requiredRoute="/directors-disclosure">
                <DirectorsDisclosure />
              </ProtectedRoute>
            } />
            <Route path="/minutes-preparation/directors" element={
              <ProtectedRoute requiredRoute="/minutes-preparation">
                <MinutesPreparation />
              </ProtectedRoute>
            } />
            <Route path="/minutes-preparation" element={
              <ProtectedRoute requiredRoute="/minutes-preparation">
                <MinutesPreparation />
              </ProtectedRoute>
            } />
            <Route path="/minutes-preparation/form-generator" element={
              <ProtectedRoute requiredRoute="/minutes-preparation">
                <FormBasedGenerator />
              </ProtectedRoute>
            } />
            <Route path="/minutes-preparation/ai-assistant" element={
              <ProtectedRoute requiredRoute="/minutes-preparation">
                <AIAssistant />
              </ProtectedRoute>
            } />
            <Route path="/hierarchy-structure" element={<HierarchyStructure />} />

            {/* Legacy product routes - redirect to main product */}
            <Route path="/ageis-wind" element={
              <ProtectedRoute requiredRoute="/bse-alerts">
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/ageis-solar" element={
              <ProtectedRoute requiredRoute="/bse-alerts">
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/dashboard" element={
              <ProtectedRoute requiredRoute="/bse-alerts">
                <Dashboard />
              </ProtectedRoute>
            } />

            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
