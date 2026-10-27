import type { FullLayoutConfig, LayoutData } from '../types';

interface HeaderProps {
    layoutData: FullLayoutConfig | null;
    isEditMode: boolean;
    profileStack: string[];
    onSwitchProfile: (id: string) => void;
    onAddProfile: () => void;
    onDeleteProfile: () => void;
    onToggleEdit: () => void;
    onAddTile: () => void;
    onSave: () => void;
    onGoBack: () => void;
    onOpenPairing: () => void;
}

export default function Header({
    layoutData,
    isEditMode,
    profileStack,
    onSwitchProfile,
    onAddProfile,
    onDeleteProfile,
    onToggleEdit,
    onAddTile,
    onSave,
    onGoBack,
    onOpenPairing,
}: HeaderProps) {
    if (!layoutData) return null;

    return (
        <div className="header-bar">
            <div className="header-left">
                <h2 style={{ margin: 0, marginRight: 20 }}>doDECK Web</h2>

                {profileStack.length > 0 && (
                    <button className="btn btn-blue" onClick={onGoBack} style={{ marginRight: 10 }}>
                        ⬅ Wstecz
                    </button>
                )}

                <select
                    className="header-select"
                    value={layoutData.active_layout_id}
                    onChange={(e) => onSwitchProfile(e.target.value)}
                >
                    {layoutData.layouts.map((l: LayoutData) => (
                        <option key={l.id} value={l.id}>
                            {l.name}
                        </option>
                    ))}
                </select>
                <button className="btn btn-dark" onClick={onAddProfile}>
                    + Profil
                </button>
                <button className="btn btn-red" onClick={onDeleteProfile} title="Usuń obecny profil">
                    - Usuń
                </button>
            </div>

            <div className="header-right">
                {isEditMode && (
                    <button className="btn btn-blue" onClick={onAddTile}>
                        + Kafelek
                    </button>
                )}
                <button
                    className={`btn ${isEditMode ? 'btn-red' : 'btn-gray'}`}
                    onClick={onToggleEdit}
                >
                    {isEditMode ? 'Wyłącz Edycję' : 'Tryb Edycji'}
                </button>
                {isEditMode && (
                    <button className="btn btn-green" onClick={onSave}>
                        Zapisz układ
                    </button>
                )}
                <button className="btn btn-dark" onClick={onOpenPairing} style={{ marginRight: 15 }}>
                    Paruj
                </button>
            </div>
        </div>
    );
}
