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
    args?: any; 
    sensor?: string;
}

export interface TileButton {
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
