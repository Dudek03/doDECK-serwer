import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Header from '../components/Header';
import { getSecretFromUrl } from '../App';
import type { FullLayoutConfig } from '../types';

const mockLayoutData: FullLayoutConfig = {
    active_layout_id: 'profile_1',
    layouts: [
        { id: 'profile_1', name: 'Main', grid: { columns: 4, rows: 4 }, buttons: [] },
        { id: 'profile_2', name: 'Music', grid: { columns: 4, rows: 4 }, buttons: [] },
    ],
};

describe('Header Component', () => {
    it('does not render Back button when profileStack is empty', () => {
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

        expect(screen.queryByText('Back')).toBeNull();
    });

    it('renders Back button when profileStack is not empty', () => {
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

        const backBtn = screen.getByText('Back');
        expect(backBtn).not.toBeNull();
        fireEvent.click(backBtn);
        expect(mockGoBack).toHaveBeenCalledTimes(1);
    });

    it('renders Add Tile and Save Layout buttons only in edit mode', () => {
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

        expect(screen.queryByText('+ Tile')).toBeNull();
        expect(screen.queryByText('Save Layout')).toBeNull();

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

        expect(screen.getByText('+ Tile')).not.toBeNull();
        expect(screen.getByText('Save Layout')).not.toBeNull();
    });

    it('calls onSwitchProfile when profile select changes', () => {
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

    it('calls onOpenPairing when clicking Pair button', () => {
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

        fireEvent.click(screen.getByText('Pair'));
        expect(mockOpenPairing).toHaveBeenCalledTimes(1);
    });
});

describe('getSecretFromUrl Utility (RFC 3986 Pairing Security)', () => {
    it('securely reads secret from URL fragment (#secret=...) without network transmission', () => {
        const secret = getSecretFromUrl('', '#secret=abc123token');
        expect(secret).toBe('abc123token');
    });

    it('prioritizes hash fragment over query string for security', () => {
        const secret = getSecretFromUrl('?secret=old_insecure', '#secret=secure_hash_token');
        expect(secret).toBe('secure_hash_token');
    });

    it('supports backwards compatibility with query string (?secret=...)', () => {
        const secret = getSecretFromUrl('?secret=legacy_token', '');
        expect(secret).toBe('legacy_token');
    });

    it('returns null when no secret is present in URL', () => {
        expect(getSecretFromUrl('', '')).toBeNull();
        expect(getSecretFromUrl('?other=123', '#section=test')).toBeNull();
    });
});
