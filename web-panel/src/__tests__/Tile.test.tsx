import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Tile from '../components/Tile';
import type { TileButton, SystemData } from '../types';

describe('Tile Component', () => {
    const systemData: SystemData = { cpu: '45', ram: '70' };

    const actionBtn: TileButton = {
        id: '1',
        title: 'Calculator',
        color: '#ff0000',
        type: 'ACTION',
        x: 1,
        y: 1,
        w: 1,
        h: 1,
        payload: { command: 'hotkey', args: 'win+r' },
    };

    const liveDataBtn: TileButton = {
        id: '2',
        title: 'RAM',
        color: '#00ff00',
        type: 'LIVE DATA',
        x: 2,
        y: 1,
        w: 1,
        h: 1,
        payload: { sensor: 'ram' },
    };

    it('renders normal action tile with title', () => {
        render(
            <Tile
                btn={actionBtn}
                isEditMode={false}
                systemData={systemData}
                onEdit={vi.fn()}
                onClick={vi.fn()}
            />
        );
        expect(screen.getByText('Calculator')).not.toBeNull();
    });

    it('renders LIVE DATA tile with value from systemData', () => {
        render(
            <Tile
                btn={liveDataBtn}
                isEditMode={false}
                systemData={systemData}
                onEdit={vi.fn()}
                onClick={vi.fn()}
            />
        );
        expect(screen.getByText('70%')).not.toBeNull();
    });

    it('calls onClick when pressed in normal mode', () => {
        const handleClick = vi.fn();
        render(
            <Tile
                btn={actionBtn}
                isEditMode={false}
                systemData={systemData}
                onEdit={vi.fn()}
                onClick={handleClick}
            />
        );

        fireEvent.pointerDown(screen.getByText('Calculator'));
        expect(handleClick).toHaveBeenCalledWith(actionBtn);
    });

    it('does not call onClick in edit mode, but renders Edit button', () => {
        const handleClick = vi.fn();
        const handleEdit = vi.fn();
        render(
            <Tile
                btn={actionBtn}
                isEditMode={true}
                systemData={systemData}
                onEdit={handleEdit}
                onClick={handleClick}
            />
        );

        const editBtn = screen.getByText('Edit');
        expect(editBtn).not.toBeNull();

        fireEvent.pointerDown(editBtn);
        expect(handleEdit).toHaveBeenCalledWith(actionBtn);
        expect(handleClick).not.toHaveBeenCalled();
    });
});
