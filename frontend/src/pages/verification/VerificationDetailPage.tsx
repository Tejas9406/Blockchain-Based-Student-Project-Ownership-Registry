import React from 'react';
import { useParams } from 'react-router-dom';
import { FileCheck } from 'lucide-react';
import { PlaceholderPage } from '../../components/ui/PlaceholderPage';
import { ROUTES } from '../../constants/routes';

export const VerificationDetailPage: React.FC = () => {
  const { registrationId } = useParams<{ registrationId: string }>();

  return (
    <PlaceholderPage
      moduleName="MODULE 6: VERIFICATION DOSSIER"
      title="Ownership Authenticity Dossier"
      description={`Inspect on-chain proof, timestamp verification, author wallet, IPFS content root, and dispute standing for registration ${registrationId || ''}.`}
      icon={FileCheck}
      actionText="Search Another Registration"
      actionLink={ROUTES.VERIFICATION.PORTAL}
    />
  );
};
