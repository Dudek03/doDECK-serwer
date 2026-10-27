import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import axios from 'axios';
import PairingModal from '../components/PairingModal';

vi.mock('axios');
const mockedAxios = vi.mocked(axios, true);

describe('PairingModal Component', () => {
    it('renderuje stan ładowania i wyświetla kody QR po pobraniu danych', async () => {
        mockedAxios.get.mockResolvedValueOnce({
            data: {
                ip: '192.168.1.100',
                port: 5000,
                secret: 'mock_secret_key',
            },
        });

        render(<PairingModal onClose={vi.fn()} />);

        expect(screen.getByText('Parowanie Urządzenia')).not.toBeNull();

        await waitFor(() => {
            expect(screen.getByText('Aplikacja mobilna')).not.toBeNull();
            expect(screen.getByText('Przeglądarka (iOS/Web)')).not.toBeNull();
        });
    });

    it('wyświetla komunikat o błędzie gdy pobieranie danych się nie powiodło', async () => {
        mockedAxios.get.mockRejectedValueOnce(new Error('Network error'));

        render(<PairingModal onClose={vi.fn()} />);

        await waitFor(() => {
            expect(
                screen.getByText(
                    'Nie udało się pobrać danych parowania. Upewnij się, że używasz edytora na maszynie hosta (localhost).'
                )
            ).not.toBeNull();
        });
    });

    it('wywołuje onClose po kliknięciu Zamknij', () => {
        mockedAxios.get.mockReturnValue(new Promise(() => {}));
        const handleClose = vi.fn();

        render(<PairingModal onClose={handleClose} />);

        fireEvent.click(screen.getByText('Zamknij'));
        expect(handleClose).toHaveBeenCalledTimes(1);
    });
});
