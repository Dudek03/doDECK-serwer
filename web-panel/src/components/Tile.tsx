import type { TileButton, SystemData } from '../types';

interface TileProps {
    btn: TileButton;
    isEditMode: boolean;
    systemData: SystemData;
    onEdit: (btn: TileButton) => void;
    onClick: (btn: TileButton) => void;
}

export default function Tile({ btn, isEditMode, systemData, onEdit, onClick }: TileProps) {
    return (
        <div
            className="tile-base"
            style={{
                backgroundColor: btn.color || '#333',
                cursor: isEditMode ? 'grab' : 'pointer',
            }}
            onPointerDown={(e) => {
                if (!isEditMode) {
                    e.stopPropagation();
                    onClick(btn);
                }
            }}
        >
            {isEditMode && (
                <div
                    className="tile-edit-btn"
                    onPointerDown={(e) => {
                        e.stopPropagation();
                        onEdit(btn);
                    }}
                >
                    ⚙
                </div>
            )}

            {btn.type === 'LIVE DATA' ? (
                <>
                    {btn.title}
                    <br />
                    <span className="tile-data-val">
                        {btn.payload.sensor === 'ram' ? `${systemData.ram}%` : `${systemData.cpu}%`}
                    </span>
                </>
            ) : (
                <span className="tile-title">{btn.title}</span>
            )}
        </div>
    );
}
