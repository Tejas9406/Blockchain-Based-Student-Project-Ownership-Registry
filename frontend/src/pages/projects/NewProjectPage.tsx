import React from 'react';
import { PlusCircle } from 'lucide-react';
import { PlaceholderPage } from '../../components/ui/PlaceholderPage';
import { ROUTES } from '../../constants/routes';

export const NewProjectPage: React.FC = () => {
  return (
    <PlaceholderPage
      moduleName="MODULE 2: PROJECTS"
      title="Register New Project"
      description="Initialize a new academic project container, configure departmental metadata, and assign project leadership."
      icon={PlusCircle}
      actionText="Back to Projects"
      actionLink={ROUTES.PROJECTS.LIST}
    />
  );
};
