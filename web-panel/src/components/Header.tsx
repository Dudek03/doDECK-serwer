interface HeaderProps {
    layoutData: any;
    isEditMode: boolean;
    onSwitchProfile: (id: string) => void;
    onAddProfile: () => void;
    onToggleEdit: () => void;
    onAddTile: () => void;
    onSave: () => void;
}

export default function Header({ layoutData, isEditMode, onSwitchProfile, onAddProfile, onToggleEdit, onAddTile, onSave }: HeaderProps) {
    if (!layoutData) return null;

    return (
        <div className="header-bar">
            <div className="header-left">
                <h2 style={{ margin: 0, marginRight: 20 }}>doDECK Web</h2>
                <select className="header-select" value={layoutData.active_layout_id} onChange={(e) => onSwitchProfile(e.target.value)}>
                    {layoutData.layouts.map((l: any) => (
                        <option key={l.id} value={l.id}>{l.name}</option>
                    ))}
                </select>
                <button className="btn btn-dark" onClick={onAddProfile}>+ Profil</button>
            </div>

            <div className="header-right">
                {isEditMode && <button className="btn btn-blue" onClick={onAddTile}>+ Kafelek</button>}
                <button className={`btn ${isEditMode ? 'btn-red' : 'btn-gray'}`} onClick={onToggleEdit}>
                    {isEditMode ? 'Wyłącz Edycję' : 'Tryb Edycji'}
                </button>
                {isEditMode && <button className="btn btn-green" onClick={onSave}>Zapisz układ</button>}
            </div>
        </div>
    );
}
