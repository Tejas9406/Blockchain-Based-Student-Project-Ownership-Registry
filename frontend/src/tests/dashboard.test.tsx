import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { DashboardPage } from '../pages/dashboard/DashboardPage';
import { AuthProvider } from '../context/AuthContext';
import { authService } from '../services/auth.service';
import * as tokenUtils from '../utils/token';
import { ROUTES } from '../constants/routes';
import { UserSummaryResponse } from '../types';

describe('DashboardPage & Layout Subcomponents', () => {
  const mockUser: UserSummaryResponse = {
    public_id: 'USR-202608-8F29A',
    email: 'tejas.sharma@nit.edu',
    full_name: 'Tejas Sharma',
    role: 'STUDENT',
    institution_id: 'NIT-CS-2026-081',
    department: 'Computer Science & Engineering',
  };

  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  const renderDashboard = () => {
    tokenUtils.setAccessToken('valid-jwt-token');
    vi.spyOn(authService, 'getMe').mockResolvedValue(mockUser);

    return render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <DashboardPage />
        </AuthProvider>
      </MemoryRouter>
    );
  };

  it('renders personalized welcome section with authenticated user details', async () => {
    renderDashboard();

    expect(await screen.findByText(/Welcome back,/i)).toBeInTheDocument();
    expect(screen.getByText('Tejas Sharma')).toBeInTheDocument();
    expect(screen.getByText('STUDENT')).toBeInTheDocument();
    expect(screen.getByText('Computer Science & Engineering')).toBeInTheDocument();
    expect(screen.getByText('NIT-CS-2026-081')).toBeInTheDocument();
    expect(screen.getByText('tejas.sharma@nit.edu')).toBeInTheDocument();
  });

  it('renders all four primary quick action cards (My Projects, Verify Ownership, Disputes, Certificates) with accessible links', async () => {
    renderDashboard();

    // Verify 4 required cards are present
    expect(await screen.findByRole('heading', { name: /^My Projects$/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /^Verify Ownership$/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /^Disputes$/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /^Certificates$/i })).toBeInTheDocument();

    // Verify Register New Project is NOT rendered as a quick action card
    expect(screen.queryByRole('heading', { name: /^Register New Project$/i })).not.toBeInTheDocument();

    // Verify correct centralized route paths
    const myProjectsLink = screen.getByRole('link', { name: /My Projects/i });
    expect(myProjectsLink).toHaveAttribute('href', ROUTES.PROJECTS.LIST);

    const verifyLink = screen.getByRole('link', { name: /Verify Ownership/i });
    expect(verifyLink).toHaveAttribute('href', ROUTES.VERIFICATION.PORTAL);

    const disputesLink = screen.getByRole('link', { name: /Disputes/i });
    expect(disputesLink).toHaveAttribute('href', ROUTES.DISPUTES.LIST);

    const certificatesLink = screen.getByRole('link', { name: /Certificates/i });
    expect(certificatesLink).toHaveAttribute('href', ROUTES.CERTIFICATES.DETAIL('overview'));
  });

  it('renders 5-step academic ownership pipeline guide', async () => {
    renderDashboard();

    expect(await screen.findByText(/Academic Ownership Workflow/i)).toBeInTheDocument();
    expect(screen.getByText('Project Setup')).toBeInTheDocument();
    expect(screen.getByText('Version Staging')).toBeInTheDocument();
    expect(screen.getByText('Artifact Intake')).toBeInTheDocument();
    expect(screen.getByText('Blockchain Anchor')).toBeInTheDocument();
    expect(screen.getByText('Ownership Verification')).toBeInTheDocument();
  });

  it('renders platform subsystems overview', async () => {
    renderDashboard();

    expect(await screen.findByText(/Platform Architecture & Subsystems/i)).toBeInTheDocument();
    expect(screen.getByText('Decentralized IPFS Storage')).toBeInTheDocument();
    expect(screen.getByText('EVM Smart Contract Registry')).toBeInTheDocument();
    expect(screen.getByText('Trustless Verification Engine')).toBeInTheDocument();
    expect(screen.getByText('Dispute & Resolution Protocol')).toBeInTheDocument();
  });
});
