import { useState, useEffect } from 'react';
import axios from 'axios';
import { QRCodeSVG } from 'qrcode.react';

interface PairingModalProps {
    onClose: () => void;
}

export default function PairingModal({ onClose }: PairingModalProps) {
    const [pairingData, setPairingData] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        axios.get('http://localhost:5000/dispatcher/get_pairing_data')
            .then(res => setPairingData(res.data))
            .catch(err => setError("Błąd pobierania danych logowania: " + err.message));
    }, []);

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()} style={{ textAlign: 'center', width: '350px' }}>
                <h3 style={{ color: '#fff', marginTop: 0 }}>Sparuj urządzenie</h3>
                <p style={{ color: '#aaa', fontSize: '0.9rem', marginBottom: '20px' }}>
                    Zeskanuj ten kod w aplikacji mobilnej doDECK, aby skonfigurować połączenie.
                </p>

                <div style={{ background: '#fff', padding: '20px', borderRadius: '10px', display: 'inline-block' }}>
                    {error ? (
                        <p style={{ color: 'red' }}>{error}</p>
                    ) : pairingData ? (
                        <QRCodeSVG
                            value={JSON.stringify(pairingData)}
                            size={200}
                            level="M"
                        />
                    ) : (
                        <p style={{ color: '#000' }}>Generowanie kodu...</p>
                    )}
                </div>

                <div style={{ background: '#fff', padding: '15px', borderRadius: '10px' }}>
                    <p style={{ color: '#000', fontWeight: 'bold', margin: '0 0 10px 0' }}>Przeglądarka (iOS/Web)</p>
                    <QRCodeSVG
                        value={`http://${pairingData.ip}:5000/?secret=${pairingData.secret}`}
                        size={150}
                    />
                </div>

                <div style={{ marginTop: '20px' }}>
                    {pairingData && <p style={{ color: '#5865F2', fontWeight: 'bold' }}>IP: {pairingData.ip}</p>}
                    <button className="btn btn-dark" style={{ width: '100%', marginTop: '10px' }} onClick={onClose}>
                        Zamknij
                    </button>
                </div>
            </div>
        </div>
    );
}
