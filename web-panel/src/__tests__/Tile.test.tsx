import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Tile from '../components/Tile';
import type { TileButton, SystemData } from '../types';

describe('Tile Component', () => {
    const systemData: SystemData = { cpu: '45', ram: '70' };

    const actionBtn: TileButton = {
        id: '1',
        title: 'Kalkulator',
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

    it('renderuje zwykły kafelek akcji z tytułem', () => {
        render(
            <Tile
                btn={actionBtn}
                isEditMode={false}
                systemData={systemData}
                onEdit={vi.fn()}
                onClick={vi.fn()}
            />
        );
        expect(screen.getByText('Kalkulator')).not.toBeNull();
    });

    it('renderuje kafelek LIVE DATA z poprawną wartością z systemData', () => {
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

    it('wywołuje onClick po naciśnięciu w trybie zwykłym', () => {
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

        fireEvent.pointerDown(screen.getByText('Kalkulator'));
        expect(handleClick).toHaveBeenCalledWith(actionBtn);
    });

    it('nie wywołuje onClick w trybie edycji, ale renderuje przycisk ⚙', () => {
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

        const editBtn = screen.getByText('⚙');
        expect(editBtn).not.toBeNull();

        fireEvent.pointerDown(editBtn);
        expect(handleEdit).toHaveBeenCalledWith(actionBtn);
        expect(handleClick).not.toHaveBeenCalled();
    });
});
