import React from 'react';
import { LayoutDashboard } from 'lucide-react';
import { PlaceholderPage } from '../../components/ui/PlaceholderPage';
import { ROUTES } from '../../constants/routes';

export const DashboardPage: React.FC = () => {
  return (
    <PlaceholderPage
      moduleName="PROJECT DASHBOARD"
      title="Student Project Registry Dashboard"
      description="Monitor active projects, view anchored version snapshots, inspect blockchain transaction receipts, and track ownership status."
      icon={LayoutDashboard}
      actionText="Browse Projects"
      actionLink={ROUTES.PROJECTS.LIST}
    />
  );
};
