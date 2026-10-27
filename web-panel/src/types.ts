export interface WindowTarget {
    title: string;
    x: number;
    y: number;
    width: number;
    height: number;
    exec_path?: string;
}

export type ButtonType = 'ACTION' | 'WIDGET' | 'LIVE DATA' | 'FOLDER' | 'WORKSPACE' | 'MACRO';

export interface MacroStep {
    command: string;
    args?: string | WindowTarget[];
    delay?: number;
}

export interface ButtonPayload {
    command?: string;
    args?: string | WindowTarget[] | MacroStep[];
    sensor?: 'cpu' | 'ram' | string;
    steps?: MacroStep[];
}

export interface TileButton {
    id: string | number;
    title: string;
    color: string;
    type: ButtonType;
    x: number;
    y: number;
    w: number;
    h: number;
    payload: ButtonPayload;
}

export interface LayoutGrid {
    columns: number;
    rows: number;
}

export interface LayoutData {
    id: string;
    name: string;
    grid: LayoutGrid;
    buttons: TileButton[];
}

export interface FullLayoutConfig {
    active_layout_id: string;
    layouts: LayoutData[];
}

export interface SystemData {
    cpu: string;
    ram: string;
}

export interface AudioApp {
    App: string;
    Volume: number;
    isMuted?: number;
}

export interface AudioVolumeData {
    ilosc: number;
    aplikacje: AudioApp[];
}

export interface PairingData {
    ip: string;
    port: number;
    secret: string;
}

export interface GridLayoutItem {
    i: string;
    x: number;
    y: number;
    w: number;
    h: number;
    static?: boolean;
    maxW?: number;
    maxH?: number;
}

export interface AppState {
    layout_data: FullLayoutConfig;
    system_data: SystemData;
    audio_data: AudioVolumeData | null;
}
