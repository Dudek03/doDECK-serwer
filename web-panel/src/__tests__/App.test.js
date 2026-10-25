import { render, screen, fireEvent } from '@testing-library/react';
import Header from '../components/Header';
const mockLayoutData = {
    active_layout_id: 'profile_1',
    layouts: [
        { id: 'profile_1', name: 'Główny' },
        { id: 'profile_2', name: 'Muzyka' }
    ]
};
describe('Header Component', () => {
    it('nie renderuje przycisku Wstecz gdy stos (profileStack) jest pusty', () => {
        render(<Header layoutData={mockLayoutData} isEditMode={false} profileStack={[]} onSwitchProfile={jest.fn()} onAddProfile={jest.fn()} onDeleteProfile={jest.fn()} onToggleEdit={jest.fn()} onAddTile={jest.fn()} onSave={jest.fn()} onGoBack={jest.fn()}/>);
        expect(screen.queryByText('⬅ Wstecz')).not.toBeInTheDocument();
    });
    it('renderuje przycisk Wstecz gdy jesteśmy w podfolderze (stos ma elementy)', () => {
        const mockGoBack = jest.fn();
        render(<Header layoutData={mockLayoutData} isEditMode={false} profileStack={['profile_1']} onSwitchProfile={jest.fn()} onAddProfile={jest.fn()} onDeleteProfile={jest.fn()} onToggleEdit={jest.fn()} onAddTile={jest.fn()} onSave={jest.fn()} onGoBack={mockGoBack}/>);
        const backBtn = screen.getByText('⬅ Wstecz');
        expect(backBtn).toBeInTheDocument();
        fireEvent.click(backBtn);
        expect(mockGoBack).toHaveBeenCalledTimes(1);
    });
    it('renderuje przyciski dodawania kafelka i zapisu tylko w trybie edycji', () => {
        const { rerender } = render(<Header layoutData={mockLayoutData} isEditMode={false} profileStack={[]} onSwitchProfile={jest.fn()} onAddProfile={jest.fn()} onDeleteProfile={jest.fn()} onToggleEdit={jest.fn()} onAddTile={jest.fn()} onSave={jest.fn()} onGoBack={jest.fn()}/>);
        expect(screen.queryByText('+ Kafelek')).not.toBeInTheDocument();
        expect(screen.queryByText('Zapisz układ')).not.toBeInTheDocument();
        rerender(<Header layoutData={mockLayoutData} isEditMode={true} profileStack={[]} onSwitchProfile={jest.fn()} onAddProfile={jest.fn()} onDeleteProfile={jest.fn()} onToggleEdit={jest.fn()} onAddTile={jest.fn()} onSave={jest.fn()} onGoBack={jest.fn()}/>);
        expect(screen.getByText('+ Kafelek')).toBeInTheDocument();
        expect(screen.getByText('Zapisz układ')).toBeInTheDocument();
    });
});
