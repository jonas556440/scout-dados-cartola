/**
 * LocalStorage Persistor for React Query
 * Salva e restaura cache automaticamente
 */

export const createLocalStoragePersistor = (storageKey: string) => {
  return {
    /**
     * Salva dados no localStorage
     */
    persistData: (data: unknown) => {
      try {
        const serialized = JSON.stringify(data);
        localStorage.setItem(storageKey, serialized);
      } catch (error) {
        console.warn(`Erro ao persistir ${storageKey}:`, error);
      }
    },

    /**
     * Restaura dados do localStorage
     */
    restoreData: () => {
      try {
        const stored = localStorage.getItem(storageKey);
        return stored ? JSON.parse(stored) : undefined;
      } catch (error) {
        console.warn(`Erro ao restaurar ${storageKey}:`, error);
        return undefined;
      }
    },

    /**
     * Limpa dados do localStorage
     */
    clearData: () => {
      try {
        localStorage.removeItem(storageKey);
      } catch (error) {
        console.warn(`Erro ao limpar ${storageKey}:`, error);
      }
    },
  };
};

/**
 * Utilitários globais de cache
 */
export const cacheUtils = {
  // Dashboard cache
  dashboard: createLocalStoragePersistor('scoutdados:dashboard'),
  // Escalação cache
  escalacao: createLocalStoragePersistor('scoutdados:escalacao'),
  // Confrontos cache
  confrontos: createLocalStoragePersistor('scoutdados:confrontos'),
  // Mercado cache
  mercado: createLocalStoragePersistor('scoutdados:mercado'),
  // Histórico cache
  historico: createLocalStoragePersistor('scoutdados:historico'),

  /**
   * Limpa TODO cache do aplicativo
   */
  clearAll: () => {
    Object.values(cacheUtils).forEach((cache) => {
      if (cache.clearData) cache.clearData();
    });
  },

  /**
   * Retorna o tamanho do cache em bytes
   */
  getSize: () => {
    let total = 0;
    for (const key in localStorage) {
      if (key.startsWith('scoutdados:')) {
        total += (localStorage[key]?.length || 0);
      }
    }
    return total;
  },
};
