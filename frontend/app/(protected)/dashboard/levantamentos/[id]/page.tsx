'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useLevantamento, Ambiente } from '@/contexts/LevantamentoContext';
import { DataPreview } from '@/components/DataPreview';

export default function DetalheLevantamentoPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const {
    levantamentoAtual: lev,
    loading,
    error,
    carregarLevantamento,
    atualizarAjustes,
    gerarExcel,
    aguardarJobCompleto,
    limparErro,
  } = useLevantamento();

  const [mounted, setMounted] = useState(false);
  const [generatingExcel, setGeneratingExcel] = useState(false);

  useEffect(() => {
    setMounted(true);
    carregarLevantamento(id);
  }, [id]);

  if (!mounted || loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center py-12">
            <div className="inline-block animate-spin">⟳</div>
            <p className="text-gray-600 mt-4">Carregando levantamento...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!lev) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-6xl mx-auto text-center py-12">
          <p className="text-red-600 mb-4">Levantamento não encontrado</p>
          <Link href="/dashboard/levantamentos" className="text-blue-600 hover:underline">
            Voltar à lista
          </Link>
        </div>
      </div>
    );
  }

  const statusColors: Record<string, string> = {
    processando: 'bg-blue-100 text-blue-800',
    revisao: 'bg-yellow-100 text-yellow-800',
    pronto: 'bg-green-100 text-green-800',
    erro: 'bg-red-100 text-red-800',
  };

  const handleGerarExcel = async () => {
    try {
      limparErro();
      setGeneratingExcel(true);
      const jobId = await gerarExcel(id);
      await aguardarJobCompleto(jobId);
      // Atualiza página
      await carregarLevantamento(id);
    } catch (err) {
      // Erro no context
    } finally {
      setGeneratingExcel(false);
    }
  };

  const ambientes = lev.dados_ajustados || lev.dados_extraidos?.ambientes || [];

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-start mb-8">
          <div>
            <Link href="/dashboard/levantamentos" className="text-blue-600 hover:underline mb-4 block">
              ← Voltar
            </Link>
            <h1 className="text-3xl font-bold text-gray-900">{lev.nome}</h1>
            <p className="text-gray-600 mt-1">ORC {lev.orc_numero}</p>
          </div>
          <span className={`px-3 py-1 rounded text-sm font-semibold ${statusColors[lev.status]}`}>
            {lev.status === 'processando' && 'Processando...'}
            {lev.status === 'revisao' && 'Revisão'}
            {lev.status === 'pronto' && 'Pronto'}
            {lev.status === 'erro' && 'Erro'}
          </span>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">{error || lev.erro_msg}</p>
          </div>
        )}

        {/* Info Cards */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg p-4">
            <p className="text-sm text-gray-600">Cliente</p>
            <p className="font-semibold text-lg">{lev.cliente}</p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <p className="text-sm text-gray-600">Empreendimento</p>
            <p className="font-semibold text-lg">{lev.empreendimento}</p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <p className="text-sm text-gray-600">Tipologia</p>
            <p className="font-semibold text-lg">{lev.tipologia}</p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <p className="text-sm text-gray-600">Tipo Detectado</p>
            <p className="font-semibold text-lg">{lev.tipo_detectado || '—'}</p>
          </div>
        </div>

        {/* Data Section */}
        {lev.status === 'revisao' || lev.status === 'pronto' ? (
          <>
            <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
              <h2 className="text-2xl font-semibold mb-4">Dados Extraídos</h2>
              {ambientes.length > 0 ? (
                <DataPreview ambientes={ambientes} />
              ) : (
                <p className="text-gray-600">Nenhum dado disponível</p>
              )}
            </div>

            {lev.status === 'revisao' && !lev.arquivo_excel_url && (
              <div className="flex gap-4">
                <button
                  onClick={handleGerarExcel}
                  disabled={generatingExcel}
                  className="flex-1 bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 transition disabled:opacity-50"
                >
                  {generatingExcel ? 'Gerando Excel...' : 'Gerar Excel'}
                </button>
              </div>
            )}

            {lev.arquivo_excel_url && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-green-800 font-semibold mb-2">✓ Excel gerado com sucesso!</p>
                <a
                  href={lev.arquivo_excel_url}
                  download
                  className="text-green-600 hover:underline"
                >
                  Baixar arquivo
                </a>
              </div>
            )}
          </>
        ) : lev.status === 'processando' ? (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
            <div className="inline-block animate-spin text-3xl mb-2">⟳</div>
            <p className="text-blue-800 font-semibold">Processando arquivo...</p>
            <p className="text-sm text-blue-700 mt-1">Volte em alguns segundos</p>
          </div>
        ) : (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <p className="text-red-800 font-semibold">Erro ao processar</p>
            <p className="text-sm text-red-700 mt-1">{lev.erro_msg}</p>
          </div>
        )}
      </div>
    </div>
  );
}
