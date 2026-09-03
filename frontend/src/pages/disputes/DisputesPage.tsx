import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { PlaceholderPage } from '../../components/ui/PlaceholderPage';
import { ROUTES } from '../../constants/routes';

export const DisputesPage: React.FC = () => {
  return (
    <PlaceholderPage
      moduleName="MODULE 8 & 9: DISPUTES"
      title="Ownership Claims & Dispute Registry"
      description="File academic plagiarism claims with IPFS-pinned evidence, track dispute review timelines, and view administrative adjudications recorded on-chain."
      icon={AlertTriangle}
      actionText="Back to Dashboard"
      actionLink={ROUTES.DASHBOARD}
    />
  );
};
