import { useState, useEffect } from 'react';
import axios from 'axios';
import { QRCodeSVG } from 'qrcode.react';
import type { PairingData } from '../types';

interface PairingModalProps {
    onClose: () => void;
}

export default function PairingModal({ onClose }: PairingModalProps) {
    const [pairingData, setPairingData] = useState<PairingData | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'app' | 'browser'>('app');
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        axios
            .get<PairingData>('/api/pairing')
            .then((res) => {
                setPairingData(res.data);
            })
            .catch(() => {
                setError(
                    'Nie udało się pobrać danych parowania. Upewnij się, że używasz edytora na maszynie hosta (localhost).'
                );
            });
    }, []);

    const handleCopySecret = () => {
        if (!pairingData) return;
        navigator.clipboard.writeText(pairingData.secret).then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        });
    };

    return (
        <div
            style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundColor: 'rgba(0,0,0,0.85)',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                zIndex: 9999,
            }}
        >
            <div
                style={{
                    backgroundColor: '#1e293b',
                    padding: '28px',
                    borderRadius: '16px',
                    textAlign: 'center',
                    maxWidth: '520px',
                    width: '90%',
                    boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
                    border: '1px solid #334155',
                }}
            >
                <h2 style={{ color: '#fff', marginTop: 0, marginBottom: '16px', fontSize: '22px' }}>
                    Parowanie Urządzenia
                </h2>

                {error && <p style={{ color: '#ef4444', fontWeight: 'bold' }}>{error}</p>}

                {!error && !pairingData && <p style={{ color: '#94a3b8' }}>Ładowanie bezpiecznego klucza...</p>}

                {pairingData && (
                    <div>
                        {/* Zakładki wyboru trybu parowania */}
                        <div
                            style={{
                                display: 'flex',
                                justifyContent: 'center',
                                gap: '10px',
                                marginBottom: '20px',
                            }}
                        >
                            <button
                                onClick={() => setActiveTab('app')}
                                style={{
                                    padding: '8px 16px',
                                    borderRadius: '8px',
                                    border: 'none',
                                    cursor: 'pointer',
                                    fontWeight: 'bold',
                                    backgroundColor: activeTab === 'app' ? '#2ecc71' : '#334155',
                                    color: activeTab === 'app' ? '#000' : '#cbd5e1',
                                    transition: 'all 0.2s',
                                }}
                            >
                                Aplikacja mobilna
                            </button>
                            <button
                                onClick={() => setActiveTab('browser')}
                                style={{
                                    padding: '8px 16px',
                                    borderRadius: '8px',
                                    border: 'none',
                                    cursor: 'pointer',
                                    fontWeight: 'bold',
                                    backgroundColor: activeTab === 'browser' ? '#3b82f6' : '#334155',
                                    color: activeTab === 'browser' ? '#fff' : '#cbd5e1',
                                    transition: 'all 0.2s',
                                }}
                            >
                                Przeglądarka (iOS/Web)
                            </button>
                        </div>

                        {/* Kontener z kodem QR */}
                        <div
                            style={{
                                background: '#fff',
                                padding: '18px',
                                borderRadius: '12px',
                                display: 'inline-block',
                                margin: '0 auto 16px auto',
                            }}
                        >
                            {activeTab === 'app' ? (
                                <QRCodeSVG value={JSON.stringify(pairingData)} size={190} marginSize={2} />
                            ) : (
                                <QRCodeSVG
                                    value={`http://${pairingData.ip}:5000/?secret=${pairingData.secret}`}
                                    size={190}
                                    marginSize={2}
                                />
                            )}
                        </div>

                        {/* Szczegóły tekstowe do ręcznego wpisania w razie problemów z kamerą */}
                        <div
                            style={{
                                backgroundColor: '#0f172a',
                                padding: '12px',
                                borderRadius: '8px',
                                textAlign: 'left',
                                fontSize: '13px',
                                color: '#94a3b8',
                                marginBottom: '16px',
                                border: '1px solid #1e293b',
                            }}
                        >
                            <div style={{ marginBottom: '6px' }}>
                                <strong style={{ color: '#e2e8f0' }}>IP serwera:</strong>{' '}
                                <span style={{ color: '#2ecc71', fontFamily: 'monospace' }}>{pairingData.ip}</span>
                            </div>
                            <div
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'space-between',
                                    gap: '8px',
                                }}
                            >
                                <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                    <strong style={{ color: '#e2e8f0' }}>Klucz:</strong>{' '}
                                    <span style={{ color: '#cbd5e1', fontFamily: 'monospace' }}>
                                        {pairingData.secret.slice(0, 16)}...
                                    </span>
                                </div>
                                <button
                                    onClick={handleCopySecret}
                                    style={{
                                        backgroundColor: copied ? '#2ecc71' : '#334155',
                                        color: copied ? '#000' : '#fff',
                                        border: 'none',
                                        padding: '4px 10px',
                                        borderRadius: '4px',
                                        cursor: 'pointer',
                                        fontSize: '11px',
                                        fontWeight: 'bold',
                                        flexShrink: 0,
                                    }}
                                >
                                    {copied ? '✓ Skopiowano' : 'Kopiuj klucz'}
                                </button>
                            </div>
                            <div style={{ marginTop: '6px', fontSize: '11px', color: '#64748b' }}>
                                💡 Jeśli aparat ma problem z odczytem, wpisz IP i klucz w aplikacji: Ustawienia → Opcje zaawansowane.
                            </div>
                        </div>
                    </div>
                )}

                <button
                    onClick={onClose}
                    style={{
                        padding: '10px 24px',
                        backgroundColor: '#e74c3c',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontWeight: 'bold',
                        fontSize: '14px',
                    }}
                >
                    Zamknij
                </button>
            </div>
        </div>
    );
}
