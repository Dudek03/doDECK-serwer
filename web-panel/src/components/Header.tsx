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
                        Back
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
                    + Profile
                </button>
                <button className="btn btn-red" onClick={onDeleteProfile} title="Delete current profile">
                    - Delete
                </button>
            </div>

            <div className="header-right">
                {isEditMode && (
                    <button className="btn btn-blue" onClick={onAddTile}>
                        + Tile
                    </button>
                )}
                <button
                    className={`btn ${isEditMode ? 'btn-red' : 'btn-gray'}`}
                    onClick={onToggleEdit}
                >
                    {isEditMode ? 'Exit Edit Mode' : 'Edit Mode'}
                </button>
                {isEditMode && (
                    <button className="btn btn-green" onClick={onSave}>
                        Save Layout
                    </button>
                )}
                <button className="btn btn-dark" onClick={onOpenPairing} style={{ marginRight: 15 }}>
                    Pair
                </button>
            </div>
        </div>
    );
}
