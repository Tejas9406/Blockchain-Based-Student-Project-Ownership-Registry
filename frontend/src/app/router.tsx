import React from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { RootLayout } from '../components/layout/RootLayout';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { ROUTES } from '../constants/routes';

import { LoginPage } from '../pages/auth/LoginPage';
import { RegisterPage } from '../pages/auth/RegisterPage';
import { DashboardPage } from '../pages/dashboard/DashboardPage';
import { ProjectsListPage } from '../pages/projects/ProjectsListPage';
import { NewProjectPage } from '../pages/projects/NewProjectPage';
import { ProjectDetailPage } from '../pages/projects/ProjectDetailPage';
import { ProjectArtifactsPage } from '../pages/projects/ProjectArtifactsPage';
import { ProjectVersionsPage } from '../pages/projects/ProjectVersionsPage';
import { VerificationPortalPage } from '../pages/verification/VerificationPortalPage';
import { VerificationDetailPage } from '../pages/verification/VerificationDetailPage';
import { DisputesPage } from '../pages/disputes/DisputesPage';
import { DisputeDetailPage } from '../pages/disputes/DisputeDetailPage';
import { CertificateDetailPage } from '../pages/certificates/CertificateDetailPage';
import { NotFoundPage } from '../pages/not-found/NotFoundPage';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route element={<RootLayout />}>
        {/* Public routes */}
        <Route path={ROUTES.LOGIN} element={<LoginPage />} />
        <Route path={ROUTES.REGISTER} element={<RegisterPage />} />
        <Route path={ROUTES.VERIFICATION.PORTAL} element={<VerificationPortalPage />} />
        <Route path={ROUTES.VERIFICATION.DETAIL(':registrationId')} element={<VerificationDetailPage />} />
        <Route path={ROUTES.CERTIFICATES.DETAIL(':registrationId')} element={<CertificateDetailPage />} />

        {/* Protected routes */}
        <Route element={<ProtectedRoute />}>
          <Route path={ROUTES.HOME} element={<Navigate to={ROUTES.DASHBOARD} replace />} />
          <Route path={ROUTES.DASHBOARD} element={<DashboardPage />} />
          <Route path={ROUTES.PROJECTS.LIST} element={<ProjectsListPage />} />
          <Route path={ROUTES.PROJECTS.NEW} element={<NewProjectPage />} />
          <Route path={ROUTES.PROJECTS.DETAIL(':projectId')} element={<ProjectDetailPage />} />
          <Route path={ROUTES.PROJECTS.ARTIFACTS(':projectId')} element={<ProjectArtifactsPage />} />
          <Route path={ROUTES.PROJECTS.VERSIONS(':projectId')} element={<ProjectVersionsPage />} />
          <Route path={ROUTES.DISPUTES.LIST} element={<DisputesPage />} />
          <Route path={ROUTES.DISPUTES.DETAIL(':disputeId')} element={<DisputeDetailPage />} />
        </Route>

        {/* 404 Catch-All */}
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
};
