import React from 'react';
import { FolderGit2 } from 'lucide-react';
import { PlaceholderPage } from '../../components/ui/PlaceholderPage';
import { ROUTES } from '../../constants/routes';

export const ProjectsListPage: React.FC = () => {
  return (
    <PlaceholderPage
      moduleName="MODULE 2: PROJECTS"
      title="Academic Project Catalog"
      description="Explore registered student innovations across departments, filter by category and lifecycle stage, and inspect ownership history."
      icon={FolderGit2}
      actionText="Create New Project"
      actionLink={ROUTES.PROJECTS.NEW}
    />
  );
};
