import React from 'react';
import StepperForm from '@/components/minutes-preparation/StepperForm';
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import { FileText, BookOpen, Home, Plus, FileSpreadsheet, History, Users } from 'lucide-react';

const StepperGenerator = () => {
  // Define navigation items for this product
  const navigationItems = [
    { id: 'home', label: 'Home', icon: Home, href: '/' },
    { id: 'dashboard', label: 'Generate Minutes', icon: FileText, href: '/minutes-preparation' },
    { id: 'create-agenda', label: 'Create Agenda', icon: Plus, href: '/minutes-preparation/create-agenda' },
    { id: 'compliances', label: 'Secretarial Compliances', icon: FileSpreadsheet, href: '/minutes-preparation/compliances' },
    { id: 'ai-mom', label: 'AI MOM', icon: FileText, href: '/minutes-preparation/ai-assistant' },
    { id: 'template-resolution', label: 'Template Resolution', icon: History, href: '/minutes-preparation/template-resolution' },
    { id: 'minutes', label: 'Meeting Minutes', icon: FileText, href: '/minutes-preparation/minutes' },
    { id: 'templates', label: 'Templates', icon: FileSpreadsheet, href: '/minutes-preparation/templates' },
    { id: 'directors', label: 'Directors', icon: Users, href: '/minutes-preparation/directors' },
    { id: 'manual', label: 'User Manual', icon: BookOpen, href: '#' }
  ];

  return (
    <ProductDashboardLayout
      productName="Generate Minutes"
      productRoute="/minutes-preparation"
      navigationItems={navigationItems}
    >
      <StepperForm />
    </ProductDashboardLayout>
  );
};

export default StepperGenerator;