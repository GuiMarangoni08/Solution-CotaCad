'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useLevantamento } from '@/contexts/LevantamentoContext';
import { LevantamentoCard } from '@/components/LevantamentoCard';

export default function LevantamentosPage() {
  const { levantamentos, loading, error, listarLevantamentos, limparErro } = useLevantamento();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    listarLevantamentos();
  }, []);

  if (!mounted) return null;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Levantamentos</h1>
            <p className="text-gray-600 mt-2">Gerencie seus levantamentos de stands e decorados</p>
          </div>
          <Link
            href="/dashboard/levantamentos/novo"
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
          >
            + Novo Levantamento
          </Link>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex justify-between items-center">
            <p className="text-red-800">{error}</p>
            <button
              onClick={limparErro}
              className="text-red-600 hover:text-red-800 font-semibold"
            >
              ✕
            </button>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin">⟳</div>
            <p className="text-gray-600 mt-4">Carregando levantamentos...</p>
          </div>
        )}

        {/* List */}
        {!loading && levantamentos.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {levantamentos.map((lev) => (
              <LevantamentoCard key={lev.id} lev={lev} />
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && levantamentos.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-600 mb-4">Nenhum levantamento criado ainda</p>
            <Link
              href="/dashboard/levantamentos/novo"
              className="text-blue-600 hover:underline font-semibold"
            >
              Criar primeiro levantamento
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
