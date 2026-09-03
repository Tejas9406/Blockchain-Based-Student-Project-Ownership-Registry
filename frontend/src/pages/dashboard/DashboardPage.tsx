import React from 'react';
import {
  FolderGit2,
  CheckCircle2,
  AlertTriangle,
  Award,
} from 'lucide-react';
import { useAuth } from '../../hooks';
import { ROUTES } from '../../constants/routes';
import {
  DashboardWelcome,
  DashboardActionCard,
  DashboardOverview,
  GettingStarted,
} from '../../components/dashboard';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();

  const actionCards = [
    {
      title: 'My Projects',
      description:
        'Explore your registered academic repositories, browse milestone versions, and inspect uploaded artifacts.',
      icon: FolderGit2,
      link: ROUTES.PROJECTS.LIST,
      badge: 'WORKSPACE',
      actionText: 'Browse Catalog',
      variant: 'emerald' as const,
    },
    {
      title: 'Verify Ownership',
      description:
        'Execute zero-trust authenticity checks against EVM smart contract state using raw files or registration IDs.',
      icon: CheckCircle2,
      link: ROUTES.VERIFICATION.PORTAL,
      badge: 'PUBLIC / TRUSTLESS',
      actionText: 'Open Verifier',
      variant: 'indigo' as const,
    },
    {
      title: 'Disputes',
      description:
        'Review logged ownership disputes, attach IPFS evidence dossiers, and track formal academic adjudication records.',
      icon: AlertTriangle,
      link: ROUTES.DISPUTES.LIST,
      badge: 'GOVERNANCE',
      actionText: 'View Disputes',
      variant: 'amber' as const,
    },
    {
      title: 'Certificates',
      description:
        'Inspect cryptographic ownership certificates, preview verifiable QR codes, and validate tamper-evident credential records.',
      icon: Award,
      link: ROUTES.CERTIFICATES.DETAIL('overview'),
      badge: 'CREDENTIALS',
      actionText: 'View Certificates',
      variant: 'teal' as const,
    },
  ];

  return (
    <div className="space-y-8 pb-12">
      {/* 1. Welcome Section */}
      <DashboardWelcome user={user} />

      {/* 2. Quick Actions Grid */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-bold text-white tracking-tight">
            Quick Actions & Capabilities
          </h3>
          <p className="text-xs sm:text-sm text-slate-400">
            Direct access to core project registry and verification operations.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {actionCards.map((card) => (
            <DashboardActionCard
              key={card.title}
              title={card.title}
              description={card.description}
              icon={card.icon}
              link={card.link}
              badge={card.badge}
              actionText={card.actionText}
              variant={card.variant}
            />
          ))}
        </div>
      </div>

      {/* 3. 5-Step Pipeline Overview */}
      <GettingStarted />

      {/* 4. Subsystems Architecture Overview */}
      <DashboardOverview />
    </div>
  );
};
