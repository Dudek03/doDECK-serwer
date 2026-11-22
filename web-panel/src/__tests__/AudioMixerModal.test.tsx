import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import AudioMixerModal from '../components/AudioMixerModal';
import type { AudioVolumeData } from '../types';

describe('AudioMixerModal Component', () => {
    const audioData: AudioVolumeData = {
        count: 2,
        apps: [
            { App: 'Spotify.exe', Volume: 60 },
            { App: 'Chrome.exe', Volume: 30 },
        ],
        ilosc: 2,
        aplikacje: [
            { App: 'Spotify.exe', Volume: 60 },
            { App: 'Chrome.exe', Volume: 30 },
        ],
    };

    it('renders applications and volume levels', () => {
        render(
            <AudioMixerModal
                appsVolume={audioData}
                onClose={vi.fn()}
                onVolumeChange={vi.fn()}
            />
        );

        expect(screen.getByText('AUDIO MIXER')).not.toBeNull();
        expect(screen.getByText('Spotify.exe')).not.toBeNull();
        expect(screen.getByText('Chrome.exe')).not.toBeNull();
        expect(screen.getByText('60%')).not.toBeNull();
        expect(screen.getByText('30%')).not.toBeNull();
    });

    it('calls onVolumeChange on slider mouse up', () => {
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

    it('calls onClose when clicking CLOSE', () => {
        const handleClose = vi.fn();
        render(
            <AudioMixerModal
                appsVolume={audioData}
                onClose={handleClose}
                onVolumeChange={vi.fn()}
            />
        );

        fireEvent.click(screen.getByText('CLOSE'));
        expect(handleClose).toHaveBeenCalledTimes(1);
    });
});
