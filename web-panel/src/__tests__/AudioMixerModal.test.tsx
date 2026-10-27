import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import AudioMixerModal from '../components/AudioMixerModal';
import type { AudioVolumeData } from '../types';

describe('AudioMixerModal Component', () => {
    const audioData: AudioVolumeData = {
        ilosc: 2,
        aplikacje: [
            { App: 'Spotify.exe', Volume: 60 },
            { App: 'Chrome.exe', Volume: 30 },
        ],
    };

    it('renderuje aplikacje i ich poziomy głośności', () => {
        render(
            <AudioMixerModal
                appsVolume={audioData}
                onClose={vi.fn()}
                onVolumeChange={vi.fn()}
            />
        );

        expect(screen.getByText('MIXER AUDIO')).not.toBeNull();
        expect(screen.getByText('Spotify.exe')).not.toBeNull();
        expect(screen.getByText('Chrome.exe')).not.toBeNull();
        expect(screen.getByText('60%')).not.toBeNull();
        expect(screen.getByText('30%')).not.toBeNull();
    });

    it('wywołuje onVolumeChange po zakończeniu przesuwania suwaka (onMouseUp)', () => {
        const handleVolumeChange = vi.fn();
        render(
            <AudioMixerModal
                appsVolume={audioData}
                onClose={vi.fn()}
                onVolumeChange={handleVolumeChange}
            />
        );

        const sliders = screen.getAllByRole('slider');
        fireEvent.mouseUp(sliders[0], { target: { value: '80' } });

        expect(handleVolumeChange).toHaveBeenCalledWith('Spotify.exe', 80);
    });

    it('wywołuje onClose po kliknięciu ZAMKNIJ', () => {
        const handleClose = vi.fn();
        render(
            <AudioMixerModal
                appsVolume={audioData}
                onClose={handleClose}
                onVolumeChange={vi.fn()}
            />
        );

        fireEvent.click(screen.getByText('ZAMKNIJ'));
        expect(handleClose).toHaveBeenCalledTimes(1);
    });
});
