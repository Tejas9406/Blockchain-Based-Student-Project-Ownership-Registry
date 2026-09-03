import React from 'react';
import { HelpCircle } from 'lucide-react';
import { PlaceholderPage } from '../../components/ui/PlaceholderPage';
import { ROUTES } from '../../constants/routes';

export const NotFoundPage: React.FC = () => {
  return (
    <PlaceholderPage
      moduleName="404 ERROR"
      title="Page Not Found"
      description="The requested route does not exist in the Student Project Ownership Registry."
      icon={HelpCircle}
      actionText="Return to Dashboard"
      actionLink={ROUTES.DASHBOARD}
    />
  );
};
