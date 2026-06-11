'use client';

import { Ambiente } from '@/contexts/LevantamentoContext';

interface DataPreviewProps {
  ambientes: Ambiente[];
  onEdit?: (amb: Ambiente) => void;
}

export function DataPreview({ ambientes, onEdit }: DataPreviewProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-slate-900 text-white">
            <th className="border p-2 text-left">Ambiente</th>
            <th className="border p-2 text-right">Área (m²)</th>
            <th className="border p-2 text-right">Perímetro (m)</th>
            <th className="border p-2 text-right">Largura (m)</th>
            <th className="border p-2 text-right">Comprimento (m)</th>
            <th className="border p-2 text-left">Piso</th>
            <th className="border p-2 text-left">Rodapé</th>
            {onEdit && <th className="border p-2 text-center">Ação</th>}
          </tr>
        </thead>
        <tbody>
          {ambientes.map((amb, idx) => (
            <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="border p-2 font-semibold">{amb.ambiente}</td>
              <td className="border p-2 text-right">{amb.area.toFixed(2)}</td>
              <td className="border p-2 text-right">{amb.perimetro.toFixed(2)}</td>
              <td className="border p-2 text-right">{amb.largura.toFixed(2)}</td>
              <td className="border p-2 text-right">{amb.comprimento.toFixed(2)}</td>
              <td className="border p-2 text-xs text-gray-700">{amb.piso || '—'}</td>
              <td className="border p-2 text-xs text-gray-700">{amb.rodape || '—'}</td>
              {onEdit && (
                <td className="border p-2 text-center">
                  <button
                    onClick={() => onEdit(amb)}
                    className="text-blue-600 hover:underline text-xs"
                  >
                    Editar
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>

      <div className="mt-4 pt-4 border-t">
        <p className="text-sm font-semibold">
          Total: {ambientes.reduce((sum, a) => sum + a.area, 0).toFixed(2)} m²
        </p>
      </div>
    </div>
  );
}
