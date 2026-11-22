import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import axios from 'axios';
import PairingModal from '../components/PairingModal';

vi.mock('axios');
const mockedAxios = vi.mocked(axios, true);

describe('PairingModal Component', () => {
    it('renders loading state and displays QR code on data fetch', async () => {
        mockedAxios.get.mockResolvedValueOnce({
            data: {
                ip: '192.168.1.100',
                port: 5000,
                secret: 'mock_secret_key',
            },
        });

        render(<PairingModal onClose={vi.fn()} />);

        expect(screen.getByText('Device Pairing')).not.toBeNull();

        await waitFor(() => {
            expect(screen.getByText('Mobile App')).not.toBeNull();
            expect(screen.getByText('Browser (iOS/Web)')).not.toBeNull();
        });
    });

    it('displays error message when data fetching fails', async () => {
        mockedAxios.get.mockRejectedValueOnce(new Error('Network error'));

        render(<PairingModal onClose={vi.fn()} />);

        await waitFor(() => {
            expect(
                screen.getByText(
                    'Failed to load pairing data. Ensure you are accessing the editor from the host machine (localhost).'
                )
            ).not.toBeNull();
        });
    });

    it('calls onClose when clicking Close', () => {
        mockedAxios.get.mockReturnValue(new Promise(() => {}));
        const handleClose = vi.fn();

        render(<PairingModal onClose={handleClose} />);

        fireEvent.click(screen.getByText('Close'));
        expect(handleClose).toHaveBeenCalledTimes(1);
    });

    it('switches to Browser tab and renders QR svg', async () => {
        mockedAxios.get.mockResolvedValueOnce({
            data: {
                ip: '192.168.1.50',
                port: 5000,
                secret: 'secure_secret_token_123',
            },
        });

        const { container } = render(<PairingModal onClose={vi.fn()} />);

        await waitFor(() => {
            expect(screen.getByText('Browser (iOS/Web)')).not.toBeNull();
        });

        fireEvent.click(screen.getByText('Browser (iOS/Web)'));

        const svgElement = container.querySelector('svg');
        expect(svgElement).not.toBeNull();
    });
});
