// Frontend Route Constants

export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/dashboard',
  PROJECTS: {
    LIST: '/projects',
    NEW: '/projects/new',
    DETAIL: (projectId: string = ':projectId') => `/projects/${projectId}`,
    ARTIFACTS: (projectId: string = ':projectId') => `/projects/${projectId}/artifacts`,
    VERSIONS: (projectId: string = ':projectId') => `/projects/${projectId}/versions`,
  },
  VERIFICATION: {
    PORTAL: '/verify',
    DETAIL: (registrationId: string = ':registrationId') => `/verify/${registrationId}`,
  },
  DISPUTES: {
    LIST: '/disputes',
    DETAIL: (disputeId: string = ':disputeId') => `/disputes/${disputeId}`,
  },
  CERTIFICATES: {
    DETAIL: (registrationId: string = ':registrationId') => `/certificates/${registrationId}`,
  },
} as const;
