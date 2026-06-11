'use client';

import Link from 'next/link';
import { Levantamento } from '@/contexts/LevantamentoContext';

export function LevantamentoCard({ lev }: { lev: Levantamento }) {
  const statusColors: Record<string, string> = {
    processando: 'bg-blue-100 text-blue-800',
    revisao: 'bg-yellow-100 text-yellow-800',
    pronto: 'bg-green-100 text-green-800',
    erro: 'bg-red-100 text-red-800',
  };

  const statusLabel: Record<string, string> = {
    processando: 'Processando...',
    revisao: 'Revisão',
    pronto: 'Pronto',
    erro: 'Erro',
  };

  return (
    <Link href={`/dashboard/levantamentos/${lev.id}`}>
      <div className="border rounded-lg p-4 hover:shadow-lg transition-shadow cursor-pointer bg-white">
        <div className="flex justify-between items-start mb-2">
          <div>
            <h3 className="font-semibold text-lg">{lev.nome}</h3>
            <p className="text-sm text-gray-600">ORC {lev.orc_numero}</p>
          </div>
          <span className={`px-2 py-1 rounded text-xs font-semibold ${statusColors[lev.status]}`}>
            {statusLabel[lev.status]}
          </span>
        </div>

        <div className="text-sm text-gray-700 space-y-1">
          <p><strong>Cliente:</strong> {lev.cliente}</p>
          <p><strong>Empreendimento:</strong> {lev.empreendimento}</p>
          <p><strong>Tipo:</strong> {lev.tipologia}</p>
        </div>

        <div className="flex gap-4 mt-3 pt-3 border-t text-xs text-gray-600">
          <div>
            {lev.tem_dados && '✓ Dados extraídos'}
          </div>
          <div>
            {lev.tem_excel && '✓ Excel gerado'}
          </div>
        </div>
      </div>
    </Link>
  );
}
