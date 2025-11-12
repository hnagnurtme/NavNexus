import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { TreeNodeUI } from '@/types';

interface NavigationState {
  history: string[];
  currentIndex: number;
  bookmarks: Set<string>;
  searchQuery: string;
  searchResults: TreeNodeUI[];

  // Actions
  visitNode: (nodeId: string) => void;
  goBack: () => string | null;
  goForward: () => string | null;
  canGoBack: () => boolean;
  canGoForward: () => boolean;
  jumpTo: (nodeId: string) => void;
  toggleBookmark: (nodeId: string) => void;
  setSearchQuery: (query: string) => void;
  setSearchResults: (results: TreeNodeUI[]) => void;
  clearSearch: () => void;
  reset: () => void;
}

export const useNavigationStore = create<NavigationState>()(
  persist(
    (set, get) => ({
      history: [],
      currentIndex: -1,
      bookmarks: new Set(),
      searchQuery: '',
      searchResults: [],

      visitNode: (nodeId: string) => {
        const { history, currentIndex } = get();
        const newHistory = history.slice(0, currentIndex + 1);
        newHistory.push(nodeId);
        set({ 
          history: newHistory, 
          currentIndex: newHistory.length - 1 
        });
      },

      goBack: () => {
        const { history, currentIndex } = get();
        if (currentIndex > 0) {
          const newIndex = currentIndex - 1;
          set({ currentIndex: newIndex });
          return history[newIndex];
        }
        return null;
      },

      goForward: () => {
        const { history, currentIndex } = get();
        if (currentIndex < history.length - 1) {
          const newIndex = currentIndex + 1;
          set({ currentIndex: newIndex });
          return history[newIndex];
        }
        return null;
      },

      canGoBack: () => get().currentIndex > 0,
      
      canGoForward: () => {
        const { history, currentIndex } = get();
        return currentIndex < history.length - 1;
      },

      jumpTo: (nodeId: string) => {
        const { history } = get();
        const index = history.indexOf(nodeId);
        if (index !== -1) {
          set({ currentIndex: index });
        }
      },

      toggleBookmark: (nodeId: string) => {
        set(state => {
          const newBookmarks = new Set(state.bookmarks);
          if (newBookmarks.has(nodeId)) {
            newBookmarks.delete(nodeId);
          } else {
            newBookmarks.add(nodeId);
          }
          return { bookmarks: newBookmarks };
        });
      },

      setSearchQuery: (query: string) => set({ searchQuery: query }),
      
      setSearchResults: (results: TreeNodeUI[]) => set({ searchResults: results }),
      
      clearSearch: () => set({ searchQuery: '', searchResults: [] }),

      reset: () => set({ 
        history: [], 
        currentIndex: -1, 
        searchQuery: '', 
        searchResults: [] 
      })
    }),
    {
      name: 'navigation-storage',
      partialize: (state) => ({ 
        bookmarks: Array.from(state.bookmarks) 
      }),
    }
  )
);
