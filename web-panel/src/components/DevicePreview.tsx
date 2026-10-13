import { useRef, useEffect, useState, useCallback } from 'react';
import { Responsive as ResponsiveGridLayout } from 'react-grid-layout';
import type { TileButton } from '../types';
import Tile from './Tile';

// Wariant Responsive wymusza na bibliotece użycie naszych kolumn bez domyślnych 12
const Grid = ResponsiveGridLayout as any;

interface DevicePreviewProps {
    buttons: TileButton[];
    activeProfile: any;
    isEditMode: boolean;
    systemData: any;
    onLayoutChange: (newLayout: any) => void;
    onTileClick: (btn: TileButton) => void;
    onTileEdit: (btn: TileButton) => void;
}

export default function DevicePreview({ buttons, activeProfile, isEditMode, systemData, onLayoutChange, onTileClick, onTileEdit }: DevicePreviewProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const [dimensions, setDimensions] = useState({ width: 1200, height: 675 });

    const updateDimensions = useCallback(() => {
        if (containerRef.current) {
            const { clientWidth, clientHeight } = containerRef.current;
            setDimensions({
                width: clientWidth - 30, // Minus padding ramki
                height: clientHeight - 30
            });
        }
    }, []);

    useEffect(() => {
        updateDimensions();
        window.addEventListener('resize', updateDimensions);
        const timeout = setTimeout(updateDimensions, 100);
        return () => {
            window.removeEventListener('resize', updateDimensions);
            clearTimeout(timeout);
        };
    }, [updateDimensions]);

    const columns = Number(activeProfile?.grid?.columns) || 4;
    const rows = Number(activeProfile?.grid?.rows) || 4;
    const gridGap = 10;

    const calculatedRowHeight = Math.max(20, Math.floor((dimensions.height - (rows - 1) * gridGap) / rows));

    const layoutParams = buttons.map(btn => ({
        i: String(btn.id),
        x: Math.min(btn.x - 1, columns - 1),
        y: Math.min(btn.y - 1, rows - 1),
        w: Math.min(btn.w, columns),
        h: Math.min(btn.h, rows),
        static: !isEditMode,
        maxW: columns,
        maxH: rows
    }));

    const bgLayoutParams = Array.from({ length: columns * rows }).map((_, i) => ({
        i: `bg-${i}`,
        x: i % columns,
        y: Math.floor(i / columns),
        w: 1,
        h: 1,
        static: true
    }));

    return (
        <div className="preview-container">
            <div ref={containerRef} className="tablet-frame">

                {/* SIATKA TŁA */}
                {isEditMode && (
                    <div style={{ position: 'absolute', top: 15, left: 15, zIndex: 0, pointerEvents: 'none' }}>
                        <Grid
                            key={`bg-${columns}-${rows}`}
                            layouts={{ custom_bp: bgLayoutParams }}
                            breakpoints={{ custom_bp: 0 }}
                            cols={{ custom_bp: columns }}
                            width={dimensions.width}
                            maxRows={rows}
                            rowHeight={calculatedRowHeight}
                            margin={[gridGap, gridGap]}
                            containerPadding={[0, 0]}
                            isBounded={true}
                            preventCollision={true}
                            compactType={null}
                            isDraggable={false}
                            isResizable={false}
                        >
                            {bgLayoutParams.map(bg => (
                                <div key={bg.i}>
                                    <div style={{ width: '100%', height: '100%', border: '2px dashed #444', borderRadius: '8px', boxSizing: 'border-box' }} />
                                </div>
                            ))}
                        </Grid>
                    </div>
                )}

                {/* WŁAŚCIWE KAFELKI */}
                <div style={{ position: 'relative', zIndex: 1 }}>
                    <Grid
                        key={`fg-${activeProfile?.id}-${columns}-${rows}`}
                        className="layout"
                        layouts={{ custom_bp: layoutParams }}
                        breakpoints={{ custom_bp: 0 }} // "custom_bp" obejmuje każdą szerokość ekranu od zera wzwyż
                        cols={{ custom_bp: columns }}  // Wymusza dokładnie Twoje kolumny, ignorując wbudowane "12"
                        width={dimensions.width}
                        maxRows={rows}
                        rowHeight={calculatedRowHeight}
                        margin={[gridGap, gridGap]}
                        containerPadding={[0, 0]}
                        isBounded={true}
                        preventCollision={true}
                        onLayoutChange={(currentLayout: any) => onLayoutChange(currentLayout)}
                        isDraggable={isEditMode}
                        isResizable={isEditMode}
                        compactType={null}
                    >
                        {buttons.map((btn: TileButton) => (
                            <div key={String(btn.id)}>
                                <Tile btn={btn} isEditMode={isEditMode} systemData={systemData} onClick={onTileClick} onEdit={onTileEdit} />
                            </div>
                        ))}
                    </Grid>
                </div>

            </div>
        </div>
    );
}
