'use client';

import React, { createContext, useState, useCallback, ReactNode } from 'react';

export interface Ambiente {
  ambiente: string;
  tipo: string;
  area: number;
  perimetro: number;
  largura: number;
  comprimento: number;
  piso?: string;
  rodape?: string;
  parede?: string;
  forro?: string;
  pd?: string;
}

export interface DadosExtraidos {
  tipo: string;
  arquivo: string;
  status: string;
  ambientes: Ambiente[];
  area_total: number;
  area_interna: number;
  area_externa: number;
  erro_msg?: string;
}

export interface Levantamento {
  id: string;
  orc_numero: string;
  nome: string;
  cliente: string;
  empreendimento: string;
  tipologia: string;
  status: 'processando' | 'revisao' | 'pronto' | 'erro';
  tipo_detectado?: string;
  dados_extraidos?: DadosExtraidos;
  dados_ajustados?: Ambiente[];
  arquivo_excel_url?: string;
  erro_msg?: string;
  criado_em?: string;
  processado_em?: string;
  finalizado_em?: string;
}

interface LevantamentoContextType {
  levantamentos: Levantamento[];
  levantamentoAtual: Levantamento | null;
  loading: boolean;
  error: string | null;

  // Ações
  listarLevantamentos: () => Promise<void>;
  carregarLevantamento: (id: string) => Promise<void>;
  criarLevantamento: (data: FormData) => Promise<string>; // retorna ID
  atualizarAjustes: (id: string, dados: Ambiente[]) => Promise<void>;
  gerarExcel: (id: string) => Promise<string>; // retorna job_id
  aguardarJobCompleto: (jobId: string) => Promise<void>;
  limparErro: () => void;
}

const LevantamentoContext = createContext<LevantamentoContextType | undefined>(undefined);

export function LevantamentoProvider({ children }: { children: ReactNode }) {
  const [levantamentos, setLevantamentos] = useState<Levantamento[]>([]);
  const [levantamentoAtual, setLevantamentoAtual] = useState<Levantamento | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;

  const listarLevantamentos = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiUrl}/api/levantamentos`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`${res.status}`);
      const data = await res.json();
      setLevantamentos(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao listar');
    } finally {
      setLoading(false);
    }
  }, [apiUrl, token]);

  const carregarLevantamento = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiUrl}/api/levantamentos/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`${res.status}`);
      const data = await res.json();
      setLevantamentoAtual(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar');
    } finally {
      setLoading(false);
    }
  }, [apiUrl, token]);

  const criarLevantamento = useCallback(async (formData: FormData): Promise<string> => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiUrl}/api/levantamentos`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!res.ok) throw new Error(`${res.status}`);
      const data = await res.json();

      // Atualiza lista
      await listarLevantamentos();

      return data.id;
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Erro ao criar';
      setError(msg);
      throw e;
    } finally {
      setLoading(false);
    }
  }, [apiUrl, token, listarLevantamentos]);

  const atualizarAjustes = useCallback(async (id: string, dados: Ambiente[]) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiUrl}/api/levantamentos/${id}`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ dados_ajustados: dados }),
      });
      if (!res.ok) throw new Error(`${res.status}`);

      // Recarrega
      await carregarLevantamento(id);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao atualizar');
    } finally {
      setLoading(false);
    }
  }, [apiUrl, token, carregarLevantamento]);

  const gerarExcel = useCallback(async (id: string): Promise<string> => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiUrl}/api/levantamentos/${id}/gerar-excel`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`${res.status}`);
      const data = await res.json();
      return data.job_id;
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Erro ao gerar Excel';
      setError(msg);
      throw e;
    } finally {
      setLoading(false);
    }
  }, [apiUrl, token]);

  const aguardarJobCompleto = useCallback(async (jobId: string) => {
    let tentativas = 0;
    const maxTentativas = 30; // ~5 minutos com delay de 10s

    while (tentativas < maxTentativas) {
      try {
        const res = await fetch(`${apiUrl}/api/levantamentos/jobs/${jobId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error(`${res.status}`);
        const data = await res.json();

        if (data.status === 'pronto') {
          // Recarrega levantamento atual
          if (levantamentoAtual) {
            await carregarLevantamento(levantamentoAtual.id);
          }
          return;
        } else if (data.status === 'erro') {
          throw new Error(data.erro_msg || 'Erro ao gerar');
        }

        // Aguarda 10s antes de próxima tentativa
        await new Promise(resolve => setTimeout(resolve, 10000));
        tentativas++;
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Erro');
        throw e;
      }
    }

    throw new Error('Timeout ao gerar Excel');
  }, [apiUrl, token, levantamentoAtual, carregarLevantamento]);

  const limparErro = useCallback(() => {
    setError(null);
  }, []);

  return (
    <LevantamentoContext.Provider
      value={{
        levantamentos,
        levantamentoAtual,
        loading,
        error,
        listarLevantamentos,
        carregarLevantamento,
        criarLevantamento,
        atualizarAjustes,
        gerarExcel,
        aguardarJobCompleto,
        limparErro,
      }}
    >
      {children}
    </LevantamentoContext.Provider>
  );
}

export function useLevantamento() {
  const context = React.useContext(LevantamentoContext);
  if (!context) {
    throw new Error('useLevantamento deve ser usado dentro de LevantamentoProvider');
  }
  return context;
}
