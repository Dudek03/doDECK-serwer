import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Header from '../components/Header';
import type { FullLayoutConfig } from '../types';

const mockLayoutData: FullLayoutConfig = {
    active_layout_id: 'profile_1',
    layouts: [
        { id: 'profile_1', name: 'Główny', grid: { columns: 4, rows: 4 }, buttons: [] },
        { id: 'profile_2', name: 'Muzyka', grid: { columns: 4, rows: 4 }, buttons: [] },
    ],
};

describe('Header Component', () => {
    it('nie renderuje przycisku Wstecz gdy stos (profileStack) jest pusty', () => {
        render(
            <Header
                layoutData={mockLayoutData}
                isEditMode={false}
                profileStack={[]}
                onSwitchProfile={vi.fn()}
                onAddProfile={vi.fn()}
                onDeleteProfile={vi.fn()}
                onToggleEdit={vi.fn()}
                onAddTile={vi.fn()}
                onSave={vi.fn()}
                onGoBack={vi.fn()}
                onOpenPairing={vi.fn()}
            />
        );

        expect(screen.queryByText('⬅ Wstecz')).toBeNull();
    });

    it('renderuje przycisk Wstecz gdy jesteśmy w podfolderze (stos ma elementy)', () => {
        const mockGoBack = vi.fn();
        render(
            <Header
                layoutData={mockLayoutData}
                isEditMode={false}
                profileStack={['profile_1']}
                onSwitchProfile={vi.fn()}
                onAddProfile={vi.fn()}
                onDeleteProfile={vi.fn()}
                onToggleEdit={vi.fn()}
                onAddTile={vi.fn()}
                onSave={vi.fn()}
                onGoBack={mockGoBack}
                onOpenPairing={vi.fn()}
            />
        );

        const backBtn = screen.getByText('⬅ Wstecz');
        expect(backBtn).not.toBeNull();
        fireEvent.click(backBtn);
        expect(mockGoBack).toHaveBeenCalledTimes(1);
    });

    it('renderuje przyciski dodawania kafelka i zapisu tylko w trybie edycji', () => {
        const { rerender } = render(
            <Header
                layoutData={mockLayoutData}
                isEditMode={false}
                profileStack={[]}
                onSwitchProfile={vi.fn()}
                onAddProfile={vi.fn()}
                onDeleteProfile={vi.fn()}
                onToggleEdit={vi.fn()}
                onAddTile={vi.fn()}
                onSave={vi.fn()}
                onGoBack={vi.fn()}
                onOpenPairing={vi.fn()}
            />
        );

        expect(screen.queryByText('+ Kafelek')).toBeNull();
        expect(screen.queryByText('Zapisz układ')).toBeNull();

        rerender(
            <Header
                layoutData={mockLayoutData}
                isEditMode={true}
                profileStack={[]}
                onSwitchProfile={vi.fn()}
                onAddProfile={vi.fn()}
                onDeleteProfile={vi.fn()}
                onToggleEdit={vi.fn()}
                onAddTile={vi.fn()}
                onSave={vi.fn()}
                onGoBack={vi.fn()}
                onOpenPairing={vi.fn()}
            />
        );

        expect(screen.getByText('+ Kafelek')).not.toBeNull();
        expect(screen.getByText('Zapisz układ')).not.toBeNull();
    });

    it('wywołuje onSwitchProfile po zmianie profilu w select', () => {
        const mockSwitch = vi.fn();
        render(
            <Header
                layoutData={mockLayoutData}
                isEditMode={false}
                profileStack={[]}
                onSwitchProfile={mockSwitch}
                onAddProfile={vi.fn()}
                onDeleteProfile={vi.fn()}
                onToggleEdit={vi.fn()}
                onAddTile={vi.fn()}
                onSave={vi.fn()}
                onGoBack={vi.fn()}
                onOpenPairing={vi.fn()}
            />
        );

        const select = screen.getByRole('combobox');
        fireEvent.change(select, { target: { value: 'profile_2' } });
        expect(mockSwitch).toHaveBeenCalledWith('profile_2');
    });

    it('wywołuje onOpenPairing po kliknięciu Paruj', () => {
        const mockOpenPairing = vi.fn();
        render(
            <Header
                layoutData={mockLayoutData}
                isEditMode={false}
                profileStack={[]}
                onSwitchProfile={vi.fn()}
                onAddProfile={vi.fn()}
                onDeleteProfile={vi.fn()}
                onToggleEdit={vi.fn()}
                onAddTile={vi.fn()}
                onSave={vi.fn()}
                onGoBack={vi.fn()}
                onOpenPairing={mockOpenPairing}
            />
        );

        fireEvent.click(screen.getByText('Paruj'));
        expect(mockOpenPairing).toHaveBeenCalledTimes(1);
    });
});
