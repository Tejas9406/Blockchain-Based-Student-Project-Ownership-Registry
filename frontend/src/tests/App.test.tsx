import { describe, it, expect, vi } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import App from '../App';

// Mock the API client to prevent unhandled network requests in unit tests
vi.mock('../services/api', () => ({
  API_BASE_URL: 'http://localhost:8000/api/v1',
  checkBackendHealth: vi.fn().mockResolvedValue({
    status: 'ok',
    service: 'backend',
    environment: 'test',
  }),
}));

describe('Frontend Environment Shell', () => {
  it('renders the project title heading correctly', async () => {
    await act(async () => {
      render(<App />);
    });
    const heading = screen.getByRole('heading', { level: 1, name: /Student Project Ownership Registry/i });
    expect(heading).toBeInTheDocument();
  });

  it('renders the environment working confirmation message', async () => {
    await act(async () => {
      render(<App />);
    });
    expect(screen.getByText(/Frontend environment is working\./i)).toBeInTheDocument();
  });

  it('displays the three developer module cards', async () => {
    await act(async () => {
      render(<App />);
    });
    expect(screen.getByText(/Developer 1: Frontend/i)).toBeInTheDocument();
    expect(screen.getByText(/Developer 2: Backend/i)).toBeInTheDocument();
    expect(screen.getByText(/Developer 3: Blockchain/i)).toBeInTheDocument();
  });
});
