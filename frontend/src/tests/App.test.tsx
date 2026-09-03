import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '../App';

describe('Frontend Application Shell', () => {
  it('renders the top-level application with header branding', () => {
    render(<App />);

    expect(
      screen.getByRole('heading', { level: 1, name: /Student Project Registry/i })
    ).toBeInTheDocument();
    expect(screen.getByText(/SIH 2026 • CYB05/i)).toBeInTheDocument();
  });

  it('renders primary navigation links', () => {
    render(<App />);

    expect(screen.getByRole('link', { name: /^Dashboard$/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /^Projects$/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /^Verify$/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /^Disputes$/i })).toBeInTheDocument();
  });

  it('renders footer metadata', () => {
    render(<App />);

    expect(
      screen.getByText(/Blockchain-Based Student Project Ownership Registry • SIH 2026 CYB05/i)
    ).toBeInTheDocument();
  });
});
