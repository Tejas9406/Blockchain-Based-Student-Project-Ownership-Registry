import React from 'react';
import { useParams } from 'react-router-dom';
import { FileUp } from 'lucide-react';
import { PlaceholderPage } from '../../components/ui/PlaceholderPage';
import { ROUTES } from '../../constants/routes';

export const ProjectArtifactsPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();

  return (
    <PlaceholderPage
      moduleName="MODULE 5: ARTIFACT INTAKE"
      title="Project Artifacts & File Ingestion"
      description={`Upload source code, documentation, models, and specifications for project ${projectId || ''}. Files are streamed, validated up to 50 MB, and hashed incrementally.`}
      icon={FileUp}
      actionText="Back to Project"
      actionLink={ROUTES.PROJECTS.DETAIL(projectId)}
    />
  );
};
