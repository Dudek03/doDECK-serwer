import { useState, useEffect, useRef } from 'react';
import GridLayout from 'react-grid-layout'; // Usunięto wadliwy import { Layout }
import axios from 'axios';
import { io } from 'socket.io-client';

import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

const socket = io();

// Silne typowanie dla Twoich danych
interface ButtonPayload {
    command?: string;
    args?: string;
    sensor?: string;
}

interface TileButton {
    id: string | number;
    title: string;
    color: string;
    type: string;
    x: number;
    y: number;
    w: number;
    h: number;
    payload: ButtonPayload;
}

function App() {
    const [fullLayoutData, setFullLayoutData] = useState<any>(null);
    const [activeButtons, setActiveButtons] = useState<TileButton[]>([]);
    const [isEditMode, setIsEditMode] = useState(false);
    const [systemData, setSystemData] = useState({ cpu: '...', ram: '...' });
    const [editingTile, setEditingTile] = useState<TileButton | null>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [gridWidth, setGridWidth] = useState(800);

    useEffect(() => {
        if (!containerRef.current) return;
        const observer = new ResizeObserver((entries) => {
            const newWidth = entries[0].contentRect.width;
            if (newWidth > 0) setGridWidth(newWidth);
        });
        observer.observe(containerRef.current);
        return () => observer.disconnect();
    }, []);

    useEffect(() => {
        const fetchLayout = async () => {
            try {
                const res = await axios.get(`/dispatcher/get_layout`);
                setFullLayoutData(res.data);
                const activeProfile = res.data.layouts.find((l: any) => l.id === res.data.active_layout_id) || res.data.layouts[0];
                setActiveButtons(activeProfile.buttons);
            } catch (error) {
                console.error("Błąd pobierania układu:", error);
            }
        };
        fetchLayout();
    }, []);

    useEffect(() => {
        const onConnect = () => socket.emit('subscribe_telemetry');

        if (socket.connected) onConnect();

        socket.on('connect', onConnect);
        socket.on('system_update', (data: any) => {
            setSystemData({ cpu: data.cpu, ram: data.ram });
        });

        return () => {
            socket.off('connect', onConnect);
            socket.off('system_update');
        };
    }, []);

    const handleTileClick = async (btn: TileButton) => {
        if (isEditMode) return;

        console.log("Odpalam kafelek:", btn.title);

        if (btn.type === 'ACTION') {
            try {
                await axios.post(`/dispatcher/trigger`, {
                    command: btn.payload.command,
                    args: btn.payload.args || ''
                });
            } catch (error) {
                console.error("Błąd akcji:", error);
            }
        } else if (btn.type === 'WIDGET' && btn.payload.command === 'open_mixer') {
            socket.emit('get_audio_volume');
        }
    };

    // Omijamy błędne typowanie w samej bibliotece za pomocą "any"
    const onLayoutChange = (newLayout: any) => {
        if (!isEditMode) return;
        const updatedButtons = activeButtons.map(btn => {
            const movedItem = newLayout.find((l: any) => l.i === String(btn.id));
            if (movedItem) {
                return { ...btn, x: movedItem.x + 1, y: movedItem.y + 1, w: movedItem.w, h: movedItem.h };
            }
            return btn;
        });
        setActiveButtons(updatedButtons);
    };

    const saveLayout = async () => {
        try {
            const payload = { ...fullLayoutData };
            const profileIndex = payload.layouts.findIndex((l: any) => l.id === payload.active_layout_id);
            payload.layouts[profileIndex].buttons = activeButtons;

            await axios.post(`/dispatcher/save_layout`, payload);
            alert('Układ zapisany pomyślnie!');
            setIsEditMode(false);
        } catch (error) {
            alert('Błąd podczas zapisywania układu.');
        }
    };

    const addNewTile = () => {
        const newTile: TileButton = {
            id: Date.now().toString(),
            title: "NOWY", color: "#e67e22", type: "ACTION", x: 1, y: 1, w: 1, h: 1,
            payload: { command: "hotkey", args: "enter" }
        };
        setActiveButtons([...activeButtons, newTile]);
    };

    const addNewProfile = () => {
        const profileName = prompt("Podaj nazwę nowego profilu:");
        if (!profileName) return;

        const newProfileId = "profile_" + Date.now();
        const newProfile = { id: newProfileId, name: profileName, grid: { columns: 4, rows: 4 }, buttons: [] };
        const updatedData = { ...fullLayoutData };
        updatedData.layouts.push(newProfile);
        updatedData.active_layout_id = newProfileId;

        setFullLayoutData(updatedData);
        setActiveButtons([]);
    };

    const switchProfile = (profileId: string) => {
        const profile = fullLayoutData.layouts.find((l: any) => l.id === profileId);
        if (!profile) return;

        const updatedData = { ...fullLayoutData };
        const oldProfileIndex = updatedData.layouts.findIndex((l: any) => l.id === updatedData.active_layout_id);
        if (oldProfileIndex > -1) updatedData.layouts[oldProfileIndex].buttons = activeButtons;

        updatedData.active_layout_id = profileId;
        setFullLayoutData(updatedData);
        setActiveButtons(profile.buttons);
    };

    const saveTileEdit = () => {
        if (!editingTile) return;
        const updatedButtons = activeButtons.map(b => b.id === editingTile.id ? editingTile : b);
        setActiveButtons(updatedButtons);
        setEditingTile(null);
    };

    const changeTileType = (newType: string) => {
        if (!editingTile) return;
        let defaultPayload = {};
        if (newType === 'ACTION') defaultPayload = { command: 'hotkey', args: '' };
        else if (newType === 'WIDGET') defaultPayload = { command: 'open_mixer' };
        else if (newType === 'LIVE DATA') defaultPayload = { sensor: 'cpu' };
        setEditingTile({ ...editingTile, type: newType, payload: defaultPayload });
    };

    const updatePayload = (key: keyof ButtonPayload, value: string) => {
        if (!editingTile) return;
        setEditingTile({ ...editingTile, payload: { ...editingTile.payload, [key]: value } });
    };

    if (!fullLayoutData) return <h2 style={{ marginTop: 50 }}>Ładowanie panelu z serwera...</h2>;

    const activeProfile = fullLayoutData.layouts.find((l: any) => l.id === fullLayoutData.active_layout_id) || fullLayoutData.layouts[0];
    const currentLayout = activeButtons.map(btn => ({
        i: String(btn.id), x: btn.x - 1, y: btn.y - 1, w: btn.w, h: btn.h, static: !isEditMode
    }));

    return (
        <>
            <div className="header-bar" style={{ flexWrap: 'wrap', gap: 15 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <h1>doDECK Web</h1>
                    <select value={fullLayoutData.active_layout_id} onChange={(e) => switchProfile(e.target.value)} style={{ padding: '5px 10px', borderRadius: 5, backgroundColor: '#333', color: 'white', border: 'none' }}>
                        {fullLayoutData.layouts.map((l: any) => (
                            <option key={l.id} value={l.id}>{l.name}</option>
                        ))}
                    </select>
                    <button onClick={addNewProfile} style={{ padding: '5px 10px', borderRadius: 5, cursor: 'pointer' }}>+ Profil</button>
                </div>

                <div className="controls" style={{ display: 'flex', gap: 10 }}>
                    {isEditMode && <button style={{ backgroundColor: '#3498db', color: 'white' }} onClick={addNewTile}>+ Kafelek</button>}
                    <button className={isEditMode ? 'active' : ''} onClick={() => setIsEditMode(!isEditMode)}>
                        {isEditMode ? 'Wyłącz Edycję' : 'Tryb Edycji'}
                    </button>
                    {isEditMode && <button style={{ backgroundColor: '#2ecc71', color: 'black' }} onClick={saveLayout}>Zapisz układ</button>}
                </div>
            </div>

            <div className={`grid-container ${isEditMode ? 'edit-mode' : ''}`} ref={containerRef} style={{ width: '100%', maxWidth: '800px', minHeight: 400, position: 'relative' }}>
                <GridLayout
                    className="layout"
                    layout={currentLayout as any}
                    width={gridWidth}
                    {...({ cols: Number(activeProfile.grid.columns) || 4 } as any)}
                    maxRows={Number(activeProfile.grid.rows) || 4}
                    isBounded={true}
                    rowHeight={150}
                    onLayoutChange={onLayoutChange}
                    isDraggable={isEditMode}
                    isResizable={isEditMode}
                    compactType={null}
                    preventCollision={false}
                >
                    {activeButtons.map(btn => (
                        <div
                            key={String(btn.id)}
                            style={{ backgroundColor: btn.color || '#333', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', cursor: isEditMode ? 'grab' : 'pointer', position: 'relative', userSelect: 'none' }}
                            onPointerDown={(e) => {
                                if (!isEditMode) {
                                    e.stopPropagation();
                                    handleTileClick(btn);
                                }
                            }}
                        >
                            {isEditMode && (
                                <div
                                    style={{ position: 'absolute', top: 5, right: 5, cursor: 'pointer', background: 'rgba(0,0,0,0.5)', borderRadius: 5, padding: '2px 5px', zIndex: 10 }}
                                    onPointerDown={(e) => { e.stopPropagation(); setEditingTile({ ...btn }); }}
                                >
                                    ⚙️
                                </div>
                            )}

                            {btn.type === 'LIVE DATA' ? (
                                <>
                                    {btn.title}<br />
                                    <span style={{ fontSize: '1.5rem' }}>
                                        {btn.payload.sensor === 'ram' ? `${systemData.ram}%` : `${systemData.cpu}%`}
                                    </span>
                                </>
                            ) : (
                                btn.title
                            )}
                        </div>
                    ))}
                </GridLayout>
            </div>

            {editingTile && (
                <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
                    <div style={{ background: '#222', padding: 20, borderRadius: 10, width: 320, display: 'flex', flexDirection: 'column', gap: 10 }}>
                        <h3 style={{ margin: '0 0 10px 0' }}>Edytuj Kafelek</h3>

                        <label>Tytuł:</label>
                        <input value={editingTile.title} onChange={e => setEditingTile({ ...editingTile, title: e.target.value })} style={{ padding: '5px', borderRadius: '4px', border: 'none' }} />

                        <label>Kolor:</label>
                        <input type="color" value={editingTile.color} onChange={e => setEditingTile({ ...editingTile, color: e.target.value })} style={{ width: '100%', height: '30px', padding: '0', border: 'none', cursor: 'pointer' }} />

                        <label>Typ:</label>
                        <select value={editingTile.type} onChange={e => changeTileType(e.target.value)} style={{ padding: '5px', borderRadius: '4px', border: 'none' }}>
                            <option value="ACTION">Akcja (ACTION)</option>
                            <option value="WIDGET">Widżet (WIDGET)</option>
                            <option value="LIVE DATA">Dane systemowe (LIVE DATA)</option>
                        </select>

                        {editingTile.type === 'ACTION' && (
                            <>
                                <label>Komenda:</label>
                                <select value={editingTile.payload.command} onChange={e => updatePayload('command', e.target.value)} style={{ padding: '5px', borderRadius: '4px', border: 'none' }}>
                                    <option value="hotkey">Skrót klawiszowy (hotkey)</option>
                                    <option value="open_url">Uruchom stronę WWW (open_url)</option>
                                </select>
                                <label>Argument:</label>
                                <input value={editingTile.payload.args || ''} onChange={e => updatePayload('args', e.target.value)} style={{ padding: '5px', borderRadius: '4px', border: 'none' }} />
                            </>
                        )}

                        {editingTile.type === 'WIDGET' && (
                            <>
                                <label>Narzędzie:</label>
                                <select value={editingTile.payload.command} onChange={e => updatePayload('command', e.target.value)} style={{ padding: '5px', borderRadius: '4px', border: 'none' }}>
                                    <option value="open_mixer">Mikser Audio</option>
                                </select>
                            </>
                        )}

                        {editingTile.type === 'LIVE DATA' && (
                            <>
                                <label>Czujnik:</label>
                                <select value={editingTile.payload.sensor || 'cpu'} onChange={e => updatePayload('sensor', e.target.value)} style={{ padding: '5px', borderRadius: '4px', border: 'none' }}>
                                    <option value="cpu">Użycie Procesora (CPU)</option>
                                    <option value="ram">Użycie Pamięci (RAM)</option>
                                </select>
                            </>
                        )}

                        <div style={{ display: 'flex', gap: 10, marginTop: 15 }}>
                            <button onClick={saveTileEdit} style={{ flex: 1, background: '#2ecc71', color: 'black', padding: 8, border: 'none', borderRadius: 5, cursor: 'pointer', fontWeight: 'bold' }}>Zapisz</button>
                            <button onClick={() => setEditingTile(null)} style={{ flex: 1, background: '#555', color: 'white', padding: 8, border: 'none', borderRadius: 5, cursor: 'pointer' }}>Anuluj</button>
                            <button onClick={() => { setActiveButtons(activeButtons.filter(b => b.id !== editingTile.id)); setEditingTile(null); }} style={{ background: '#e74c3c', color: 'white', border: 'none', borderRadius: 5, cursor: 'pointer', padding: 8 }}>Usuń</button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}

export default App;
