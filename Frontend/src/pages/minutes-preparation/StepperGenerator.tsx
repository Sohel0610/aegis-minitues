import React from 'react';
import StepperForm from '@/components/minutes-preparation/StepperForm';
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import { FileText, BookOpen } from 'lucide-react';

const StepperGenerator = () => {
  // Define navigation items for this product
  const navigationItems = [
    { id: 'home', label: 'Home', icon: FileText, href: '/' },
    { id: 'dashboard', label: 'Generate Minutes', icon: FileText, href: '/minutes-preparation' },
    { id: 'create-agenda', label: 'Create Agenda', icon: FileText, href: '/minutes-preparation/create-agenda' },
    { id: 'compliances', label: 'Secretarial Compliances', icon: FileText, href: '/minutes-preparation/compliances' },
    { id: 'ai-mom', label: 'AI MOM', icon: FileText, href: '/minutes-preparation/ai-assistant' },
    { id: 'template-resolution', label: 'Template Resolution', icon: FileText, href: '/minutes-preparation/template-resolution' },
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