import { useState, useEffect } from 'react';

interface AudioApp {
    App: string;
    Volume: number;
}

interface AudioMixerModalProps {
    appsVolume: { aplikacje: AudioApp[] };
    onClose: () => void;
    onVolumeChange: (appName: string, volume: number) => void;
}

export default function AudioMixerModal({ appsVolume, onClose, onVolumeChange }: AudioMixerModalProps) {
    const [apps, setApps] = useState<AudioApp[]>([]);

    useEffect(() => {
        if (appsVolume && Array.isArray(appsVolume.aplikacje)) {
            setApps(appsVolume.aplikacje);
        }
    }, [appsVolume]);

    const handleSliderChange = (index: number, newVolume: number) => {
        const updatedApps = [...apps];
        updatedApps[index].Volume = newVolume;
        setApps(updatedApps);
    };

    const handleSlidingComplete = (appName: string, finalVolume: number) => {
        onVolumeChange(appName, finalVolume);
    };

    return (
        <div className="modal-overlay">
            <div className="modal-content" style={{ width: '400px', maxHeight: '80vh' }}>
                <h3 style={{ margin: '0 0 15px 0', borderBottom: '1px solid #333', paddingBottom: '10px', color: '#fff' }}>MIXER AUDIO</h3>

                <div style={{ overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '15px', paddingRight: '5px' }}>
                    {apps.map((app, index) => (
                        <div key={index} style={{ display: 'flex', flexDirection: 'column', gap: '8px', background: '#111', padding: '15px', borderRadius: '8px', border: '1px solid #333' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', color: '#ddd' }}>
                                <span style={{ fontWeight: 'bold', fontSize: '0.95rem' }}>{app.App}</span>
                                <span style={{ fontWeight: 'bold' }}>{Math.round(app.Volume)}%</span>
                            </div>
                            <input
                                type="range"
                                min="0"
                                max="100"
                                value={Math.round(app.Volume)}
                                onChange={(e) => handleSliderChange(index, Number(e.target.value))}
                                onMouseUp={(e) => handleSlidingComplete(app.App, Number((e.target as HTMLInputElement).value))}
                                onTouchEnd={(e) => handleSlidingComplete(app.App, Number((e.target as HTMLInputElement).value))}
                                style={{ width: '100%', cursor: 'pointer', accentColor: '#2ecc71' }}
                            />
                        </div>
                    ))}
                </div>

                <button className="btn btn-red" onClick={onClose} style={{ marginTop: '20px', width: '100%', padding: '12px', fontSize: '1.1rem' }}>
                    ZAMKNIJ
                </button>
            </div>
        </div>
    );
}
