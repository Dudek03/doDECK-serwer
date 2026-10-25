export interface WindowTarget {
    title: string;
    x: number;
    y: number;
    width: number;
    height: number;
    exec_path?: string;
}

export interface ButtonPayload {
    command?: string;
    args?: string | any; 
    sensor?: string;
}

export interface TileButton {
    id: string | number;
    title: string;
    color: string;
    type: 'ACTION' | 'WIDGET' | 'LIVE DATA' | 'FOLDER' | 'WORKSPACE' | 'MACRO';
    x: number;
    y: number;
    w: number;
    h: number;
    payload: ButtonPayload;
}

export interface LayoutData {
    id: string;
    name: string;
    grid: {
        columns: number;
        rows: number;
    };
    buttons: TileButton[];
}

export interface AppState {
    layout_data: {
        active_layout_id: string;
        layouts: LayoutData[];
    };
    system_data: {
        cpu: string;
        ram: string;
    };
    audio_data: any | null; // Keep as any for now since it's raw data from the server, but typed more strictly than standard any
}
