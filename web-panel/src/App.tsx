import { useState, useEffect } from 'react';
import axios from 'axios';
import { io } from 'socket.io-client';
import type { TileButton } from './types';
import Header from './components/Header';
import DevicePreview from './components/DevicePreview';
import EditorModal from './components/EditorModal';

import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import './styles/styles.css';

const socket = io();

export default function App() {
    const [fullLayoutData, setFullLayoutData] = useState<any>(null);
    const [activeButtons, setActiveButtons] = useState<TileButton[]>([]);
    const [isEditMode, setIsEditMode] = useState(false);
    const [systemData, setSystemData] = useState({ cpu: '...', ram: '...' });
    const [editingTile, setEditingTile] = useState<TileButton | null>(null);

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

        socket.on('connect', () => socket.emit('subscribe_telemetry'));
        socket.on('system_update', (data: any) => setSystemData({ cpu: data.cpu, ram: data.ram }));

        return () => {
            socket.off('connect');
            socket.off('system_update');
        };
    }, []);

    const handleTileClick = (btn: TileButton) => {
        if (isEditMode) return;

        if (btn.type === 'ACTION' || btn.type === 'WORKSPACE') {
            socket.emit('trigger_action', { command: btn.payload.command, args: btn.payload.args || '' });
        } else if (btn.type === 'WIDGET' && btn.payload.command === 'open_mixer') {
            socket.emit('get_audio_volume');
        }
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
            alert('Błąd zapisu.');
        }
    };

    const switchProfile = (profileId: string) => {
        const profile = fullLayoutData.layouts.find((l: any) => l.id === profileId);
        if (!profile) return;

        const updatedData = { ...fullLayoutData, active_layout_id: profileId };
        setFullLayoutData(updatedData);
        setActiveButtons(profile.buttons);
    };

    const addNewProfile = () => {
        const name = prompt("Podaj nazwę nowego profilu:");
        if (!name) return;

        const gridInput = prompt("Podaj wymiary siatki w formacie KOLUMNY:WIERSZE (np. 8:4, 4:4, 16:8):", "8:4");
        let cols = 8;
        let rows = 4;

        if (gridInput && gridInput.includes(':')) {
            const parts = gridInput.split(':');
            cols = parseInt(parts[0]) || 8;
            rows = parseInt(parts[1]) || 4;
        }

        const newProfile = { id: "profile_" + Date.now(), name, grid: { columns: cols, rows: rows }, buttons: [] };

        const updatedData = {
            ...fullLayoutData,
            active_layout_id: newProfile.id,
            layouts: [...fullLayoutData.layouts, newProfile]
        };

        setFullLayoutData(updatedData);
        setActiveButtons([]);
    };

    if (!fullLayoutData) return <h2 style={{ textAlign: 'center', marginTop: 50, color: 'white' }}>Ładowanie doDECK...</h2>;
    const activeProfile = fullLayoutData.layouts.find((l: any) => l.id === fullLayoutData.active_layout_id) || fullLayoutData.layouts[0];

    return (
        <div>
            <Header
                layoutData={fullLayoutData}
                isEditMode={isEditMode}
                onSwitchProfile={switchProfile}
                onAddProfile={addNewProfile}
                onToggleEdit={() => setIsEditMode(!isEditMode)}
                onAddTile={() => setActiveButtons([...activeButtons, { id: Date.now().toString(), title: "NOWY", color: "#e67e22", type: "ACTION", x: 1, y: 1, w: 1, h: 1, payload: { command: "hotkey", args: "enter" } }])}
                onSave={saveLayout}
            />

            <DevicePreview
                buttons={activeButtons}
                activeProfile={activeProfile}
                isEditMode={isEditMode}
                systemData={systemData}
                onLayoutChange={(newLayout) => {
                    setActiveButtons(activeButtons.map(btn => {
                        const moved = newLayout.find((l: any) => l.i === String(btn.id));
                        return moved ? { ...btn, x: moved.x + 1, y: moved.y + 1, w: moved.w, h: moved.h } : btn;
                    }));
                }}
                onTileClick={handleTileClick}
                onTileEdit={setEditingTile}
            />

            {editingTile && (
                <EditorModal
                    tile={editingTile}
                    onSave={(updated) => {
                        setActiveButtons(activeButtons.map(b => b.id === updated.id ? updated : b));
                        setEditingTile(null);
                    }}
                    onCancel={() => setEditingTile(null)}
                    onDelete={(id) => {
                        setActiveButtons(activeButtons.filter(b => b.id !== id));
                        setEditingTile(null);
                    }}
                />
            )}
        </div>
    );
}
