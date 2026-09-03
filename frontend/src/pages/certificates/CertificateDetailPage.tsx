import React from 'react';
import { useParams } from 'react-router-dom';
import { Award } from 'lucide-react';
import { PlaceholderPage } from '../../components/ui/PlaceholderPage';
import { ROUTES } from '../../constants/routes';

export const CertificateDetailPage: React.FC = () => {
  const { registrationId } = useParams<{ registrationId: string }>();

  return (
    <PlaceholderPage
      moduleName="MODULE 7: CERTIFICATES & QR"
      title="Ownership Certificate Preview"
      description={`View certificate metadata, scan the URL-encoded verification QR code, or download the official PDF ownership certificate for registration ${registrationId || ''}.`}
      icon={Award}
      actionText="Verify on Portal"
      actionLink={ROUTES.VERIFICATION.DETAIL(registrationId)}
    />
  );
};
