import React from 'react';
import { useParams } from 'react-router-dom';
import { Layers } from 'lucide-react';
import { PlaceholderPage } from '../../components/ui/PlaceholderPage';
import { ROUTES } from '../../constants/routes';

export const ProjectVersionsPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();

  return (
    <PlaceholderPage
      moduleName="MODULE 4: VERSION ANCHORING"
      title="Project Milestones & Version Snapshots"
      description={`Create immutable milestone snapshots for project ${projectId || ''}. Combines artifacts into a deterministic SHA-256 root and anchors proof onto the EVM smart contract.`}
      icon={Layers}
      actionText="Back to Project"
      actionLink={ROUTES.PROJECTS.DETAIL(projectId)}
    />
  );
};
