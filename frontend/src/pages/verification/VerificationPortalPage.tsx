import React from 'react';
import { CheckCircle2 } from 'lucide-react';
import { PlaceholderPage } from '../../components/ui/PlaceholderPage';
import { ROUTES } from '../../constants/routes';

export const VerificationPortalPage: React.FC = () => {
  return (
    <PlaceholderPage
      moduleName="MODULE 6: PUBLIC VERIFICATION"
      title="Trustless Verification Portal"
      description="Verify the provenance and authenticity of academic projects using Registration ID (REG-YYYY-XXXXX), raw SHA-256 hash, or direct file drag-and-drop."
      icon={CheckCircle2}
      actionText="Back to Dashboard"
      actionLink={ROUTES.DASHBOARD}
    />
  );
};
