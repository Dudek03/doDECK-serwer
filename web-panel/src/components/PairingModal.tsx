import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { QRCodeSVG } from 'qrcode.react';

interface PairingModalProps {
    onClose: () => void;
}

export default function PairingModal({ onClose }: PairingModalProps) {
    const [pairingData, setPairingData] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        axios.get('/api/pairing')
            .then(res => {
                setPairingData(res.data);
            })
            .catch(() => {
                setError("Nie udało się pobrać danych parowania. Upewnij się, że używasz edytora na maszynie hosta (localhost).");
            });
    }, []);

    return (
        <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.8)', display: 'flex',
            justifyContent: 'center', alignItems: 'center', zIndex: 9999
        }}>
            <div style={{
                backgroundColor: '#2c3e50', padding: '30px',
                borderRadius: '15px', textAlign: 'center', maxWidth: '600px'
            }}>
                <h2 style={{ color: '#fff', marginTop: 0 }}>Parowanie Urządzenia</h2>

                {error && <p style={{ color: '#e74c3c', fontWeight: 'bold' }}>{error}</p>}

                {!error && !pairingData && (
                    <p style={{ color: '#fff' }}>Ładowanie bezpiecznego klucza...</p>
                )}

                {pairingData && (
                    <div style={{ display: 'flex', gap: '20px', justifyContent: 'center', margin: '20px 0' }}>
                        <div style={{ background: '#fff', padding: '15px', borderRadius: '10px' }}>
                            <p style={{ color: '#000', fontWeight: 'bold', margin: '0 0 10px 0' }}>Aplikacja mobilna</p>
                            <QRCodeSVG
                                value={JSON.stringify(pairingData)}
                                size={150}
                            />
                        </div>

                        <div style={{ background: '#fff', padding: '15px', borderRadius: '10px' }}>
                            <p style={{ color: '#000', fontWeight: 'bold', margin: '0 0 10px 0' }}>Przeglądarka (iOS/Web)</p>
                            <QRCodeSVG
                                value={`http://${pairingData.ip}:5000/?secret=${pairingData.secret}`}
                                size={150}
                            />
                        </div>
                    </div>
                )}

                <button
                    onClick={onClose}
                    style={{
                        marginTop: '10px', padding: '10px 20px',
                        backgroundColor: '#e74c3c', color: 'white',
                        border: 'none', borderRadius: '5px', cursor: 'pointer'
                    }}
                >
                    Zamknij
                </button>
            </div>
        </div>
    );
}
