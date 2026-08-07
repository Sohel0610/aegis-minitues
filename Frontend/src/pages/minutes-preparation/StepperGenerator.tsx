import React from 'react';
import StepperForm from '@/components/minutes-preparation/StepperForm';
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import { getMinutesNavItems } from '@/constants/minutesNavigation';

const StepperGenerator = () => {
  const navigationItems = getMinutesNavItems('dashboard');

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