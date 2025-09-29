import { create } from 'zustand'

interface NavigationState {
  isCollapsed: boolean
  toggleCollapsed: () => void
  setCollapsed: (collapsed: boolean) => void
}

export const useNavigationStore = create<NavigationState>((set) => ({
  isCollapsed: false,
  toggleCollapsed: () => set((state) => ({ isCollapsed: !state.isCollapsed })),
  setCollapsed: (collapsed: boolean) => set({ isCollapsed: collapsed }),
}))
