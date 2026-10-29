import { useState } from 'react';
import axios from 'axios';
import type { TileButton, WindowTarget, LayoutData, ButtonPayload } from '../types';

interface EditorModalProps {
    tile: TileButton;
    profiles: LayoutData[];
    onSave: (updatedTile: TileButton) => void;
    onCancel: () => void;
    onDelete: (id: string | number) => void;
}

export default function EditorModal({ tile, profiles, onSave, onCancel, onDelete }: EditorModalProps) {
    const [editingTile, setEditingTile] = useState<TileButton>(() => {
        const initial = { ...tile };
        if (initial.type === 'FOLDER' && (!initial.payload?.args || typeof initial.payload.args !== 'string')) {
            initial.payload = { ...initial.payload, args: profiles[0]?.id || '' };
        }
        return initial;
    });
    const [scannedWindows, setScannedWindows] = useState<WindowTarget[]>([]);

    const updatePayload = <K extends keyof ButtonPayload>(key: K, value: ButtonPayload[K]) => {
        setEditingTile((prev) => ({
            ...prev,
            payload: { ...prev.payload, [key]: value },
        }));
    };

    const handleSave = () => {
        const finalTile = { ...editingTile };
        if (finalTile.type === 'FOLDER') {
            const currentArg = typeof finalTile.payload?.args === 'string' ? finalTile.payload.args : '';
            if (!currentArg && profiles.length > 0) {
                finalTile.payload = { ...finalTile.payload, args: profiles[0].id };
            }
        }
        onSave(finalTile);
    };

    const handleScanWindows = async () => {
        try {
            const res = await axios.get('/dispatcher/scan_windows');
            if (res.data && res.data.windows) setScannedWindows(res.data.windows);
        } catch {
            alert('Błąd skanowania okien.');
        }
    };

    const toggleWindowSelection = (win: WindowTarget) => {
        const currentArgs = (editingTile.payload.args as WindowTarget[]) || [];
        const exists = currentArgs.find((w) => w.title === win.title);
        const newArgs = exists
            ? currentArgs.filter((w) => w.title !== win.title)
            : [...currentArgs, win];
        updatePayload('args', newArgs);
    };

    const updateWindowPath = (title: string, path: string) => {
        const currentArgs = (editingTile.payload.args as WindowTarget[]) || [];
        const updatedArgs = currentArgs.map((w) => (w.title === title ? { ...w, exec_path: path } : w));
        updatePayload('args', updatedArgs);
    };

    return (
        <div className="modal-overlay">
            <div className="modal-content">
                <h3 style={{ margin: '0 0 10px 0', color: '#fff' }}>Edytuj Kafelek</h3>

                <label className="modal-label">Tytuł:</label>
                <input
                    className="modal-input"
                    value={editingTile.title}
                    onChange={(e) => setEditingTile({ ...editingTile, title: e.target.value })}
                />

                <label className="modal-label">Kolor:</label>
                <input
                    type="color"
                    value={editingTile.color}
                    onChange={(e) => setEditingTile({ ...editingTile, color: e.target.value })}
                    style={{
                        width: '100%',
                        height: '40px',
                        border: 'none',
                        cursor: 'pointer',
                        borderRadius: '4px',
                    }}
                />

                <label className="modal-label">Typ:</label>
                <select
                    className="modal-input"
                    value={editingTile.type}
                    onChange={(e) => {
                        const newType = e.target.value as TileButton['type'];
                        let defPayload: ButtonPayload = {};
                        if (newType === 'ACTION') defPayload = { command: 'hotkey', args: '' };
                        else if (newType === 'WIDGET') defPayload = { command: 'open_mixer' };
                        else if (newType === 'LIVE DATA') defPayload = { sensor: 'cpu' };
                        else if (newType === 'WORKSPACE') defPayload = { command: 'workspace', args: [] };
                        else if (newType === 'FOLDER') defPayload = { args: profiles[0]?.id || '' };
                        setEditingTile({ ...editingTile, type: newType, payload: defPayload });
                    }}
                >
                    <option value="ACTION">Akcja (ACTION)</option>
                    <option value="FOLDER">Folder / Profil (FOLDER)</option>
                    <option value="WIDGET">Widżet (WIDGET)</option>
                    <option value="LIVE DATA">Dane systemowe (LIVE DATA)</option>
                    <option value="WORKSPACE">Przestrzeń robocza (WORKSPACE)</option>
                </select>

                {editingTile.type === 'FOLDER' && (
                    <>
                        <label className="modal-label">Wybierz profil docelowy:</label>
                        <select
                            className="modal-input"
                            value={
                                typeof editingTile.payload?.args === 'string' && editingTile.payload.args
                                    ? editingTile.payload.args
                                    : profiles[0]?.id || ''
                            }
                            onChange={(e) => updatePayload('args', e.target.value)}
                        >
                            {profiles.map((p) => (
                                <option key={p.id} value={p.id}>
                                    {p.name}
                                </option>
                            ))}
                        </select>
                    </>
                )}

                {editingTile.type === 'ACTION' && (
                    <>
                        <label className="modal-label">Komenda:</label>
                        <select
                            className="modal-input"
                            value={editingTile.payload.command || 'hotkey'}
                            onChange={(e) => updatePayload('command', e.target.value)}
                        >
                            <option value="hotkey">Skrót klawiszowy</option>
                            <option value="write">Wpisz tekst (Makro)</option>
                            <option value="open_url">Strona WWW</option>
                        </select>
                        <input
                            className="modal-input"
                            value={typeof editingTile.payload.args === 'string' ? editingTile.payload.args : ''}
                            onChange={(e) => updatePayload('args', e.target.value)}
                            placeholder={
                                editingTile.payload.command === 'write'
                                    ? 'Tekst do wpisania...'
                                    : editingTile.payload.command === 'hotkey'
                                    ? 'np. ctrl+c, alt+tab'
                                    : 'Parametr...'
                            }
                        />
                    </>
                )}

                {editingTile.type === 'WORKSPACE' && (
                    <>
                        <button className="btn btn-blue" onClick={handleScanWindows}>
                            🔍 Skanuj otwarte okna
                        </button>
                        <div className="modal-windows-list">
                            {scannedWindows.map((win, idx) => {
                                const currentArgs = (editingTile.payload.args as WindowTarget[]) || [];
                                const savedWin = currentArgs.find((w) => w.title === win.title);
                                return (
                                    <div key={idx} style={{ marginBottom: '10px' }}>
                                        <div
                                            className="window-item"
                                            onClick={() => toggleWindowSelection(win)}
                                        >
                                            <input
                                                type="checkbox"
                                                checked={!!savedWin}
                                                readOnly
                                                style={{ cursor: 'pointer' }}
                                            />
                                            <span className="window-title">{win.title}</span>
                                        </div>
                                        {!!savedWin && (
                                            <input
                                                className="modal-input"
                                                placeholder="C:\app.exe"
                                                value={savedWin?.exec_path || ''}
                                                onChange={(e) => updateWindowPath(win.title, e.target.value)}
                                                style={{
                                                    marginTop: '5px',
                                                    width: '85%',
                                                    marginLeft: '20px',
                                                    fontSize: '0.75rem',
                                                }}
                                            />
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </>
                )}

                <div style={{ display: 'flex', gap: 10, marginTop: 15 }}>
                    <button className="btn btn-green" style={{ flex: 1 }} onClick={handleSave}>
                        Zapisz
                    </button>
                    <button className="btn btn-dark" style={{ flex: 1 }} onClick={onCancel}>
                        Anuluj
                    </button>
                    <button className="btn btn-red" onClick={() => onDelete(editingTile.id)}>
                        Usuń
                    </button>
                </div>
            </div>
        </div>
    );
}
