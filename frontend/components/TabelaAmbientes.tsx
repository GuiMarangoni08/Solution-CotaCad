"use client";
import { useState } from "react";
import axios from "axios";
import toast from "react-hot-toast";
import clsx from "clsx";

const API = process.env.NEXT_PUBLIC_API_URL || "https://cotacad-solution.duckdns.org/api";

export interface Ambiente {
  id: string;
  nome: string | null;
  nome_flag: string;
  area: number | null;
  area_flag: string;
  comprimento: number | null;
  largura: number | null;
  perimetro: number | null;
  perimetro_flag: string;
  pe_direito: number | null;
  pe_direito_flag: string;
  camada: string | null;
  fonte: string;
  ordem: number;
}

interface Props {
  ambientes: Ambiente[];
  onChange: (updated: Ambiente[]) => void;
}

const FLAG_ICON: Record<string, string> = {
  confirmed: "✓",
  estimated: "⚠️",
  missing:   "✗",
};

const FLAG_CLASS: Record<string, string> = {
  confirmed: "text-green-600",
  estimated: "text-yellow-600",
  missing:   "text-red-500",
};

function FlagBadge({ flag }: { flag: string }) {
  return (
    <span className={clsx("text-xs font-bold ml-1", FLAG_CLASS[flag])}>
      {FLAG_ICON[flag]}
    </span>
  );
}

interface EditState {
  ambienteId: string;
  field: "nome" | "area" | "perimetro" | "pe_direito";
  value: string;
}

export default function TabelaAmbientes({ ambientes, onChange }: Props) {
  const [editing, setEditing] = useState<EditState | null>(null);
  const [saving, setSaving] = useState(false);

  function startEdit(ambienteId: string, field: EditState["field"], currentValue: string) {
    setEditing({ ambienteId, field, value: currentValue });
  }

  async function saveEdit() {
    if (!editing) return;
    setSaving(true);
    try {
      const payload: Record<string, string | number> = {};
      const val = editing.value.trim();

      if (editing.field === "nome") {
        payload.nome = val;
      } else {
        const num = parseFloat(val.replace(",", "."));
        if (isNaN(num)) { toast.error("Valor inválido"); setSaving(false); return; }
        payload[editing.field] = num;
      }

      await axios.patch(`${API}/ambiente/${editing.ambienteId}`, payload);

      const updated = ambientes.map((a) => {
        if (a.id !== editing.ambienteId) return a;
        const copy = { ...a };
        if (editing.field === "nome") {
          copy.nome = val;
          copy.nome_flag = "confirmed";
        } else {
          const num = parseFloat(val.replace(",", "."));
          (copy as Record<string, unknown>)[editing.field] = num;
          (copy as Record<string, unknown>)[`${editing.field}_flag`] = "confirmed";
        }
        return copy;
      });

      onChange(updated);
      toast.success("Salvo!");
      setEditing(null);
    } catch {
      toast.error("Erro ao salvar");
    } finally {
      setSaving(false);
    }
  }

  function EditableCell({
    ambienteId, field, value, flag, placeholder,
  }: {
    ambienteId: string;
    field: EditState["field"];
    value: string | null;
    flag: string;
    placeholder?: string;
  }) {
    const isEditing = editing?.ambienteId === ambienteId && editing?.field === field;

    if (isEditing) {
      return (
        <div className="flex items-center gap-1">
          <input
            autoFocus
            className="border border-brand rounded px-2 py-0.5 text-sm w-28 focus:outline-none focus:ring-1 focus:ring-brand"
            value={editing.value}
            onChange={(e) => setEditing({ ...editing, value: e.target.value })}
            onKeyDown={(e) => {
              if (e.key === "Enter") saveEdit();
              if (e.key === "Escape") setEditing(null);
            }}
          />
          <button
            disabled={saving}
            onClick={saveEdit}
            className="text-xs bg-brand text-white px-2 py-0.5 rounded hover:bg-brand-light"
          >
            OK
          </button>
        </div>
      );
    }

    return (
      <button
        onClick={() => startEdit(ambienteId, field, value ?? "")}
        className={clsx(
          "text-left w-full group",
          flag === "missing" && "text-red-400 italic"
        )}
        title="Clique para editar"
      >
        {value != null ? (
          <>
            {value}
            <FlagBadge flag={flag} />
          </>
        ) : (
          <span className="text-red-400 italic">
            {placeholder || "✗ preencher"}
          </span>
        )}
        <span className="ml-1 opacity-0 group-hover:opacity-100 text-gray-400 text-xs">✏️</span>
      </button>
    );
  }

  const totalArea = ambientes
    .filter((a) => a.area != null)
    .reduce((sum, a) => sum + (a.area ?? 0), 0);

  const missingCount = ambientes.filter(
    (a) => a.nome_flag === "missing" || a.area_flag === "missing"
  ).length;

  return (
    <div className="space-y-3">
      {missingCount > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-3 text-sm text-yellow-800">
          <strong>{missingCount} ambiente(s)</strong> com dados incompletos — clique nas células vermelhas para preencher.
        </div>
      )}

      <div className="overflow-x-auto rounded-xl border border-gray-200 shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-brand text-white">
              <th className="px-4 py-3 text-left font-semibold">Ambiente</th>
              <th className="px-4 py-3 text-left font-semibold">Camada</th>
              <th className="px-4 py-3 text-right font-semibold">Área (m²)</th>
              <th className="px-4 py-3 text-right font-semibold">C (m)</th>
              <th className="px-4 py-3 text-right font-semibold">L (m)</th>
              <th className="px-4 py-3 text-right font-semibold">Perímetro (m)</th>
              <th className="px-4 py-3 text-right font-semibold">Pé Direito (m)</th>
              <th className="px-4 py-3 text-center font-semibold">Fonte</th>
            </tr>
          </thead>
          <tbody>
            {ambientes
              .sort((a, b) => a.ordem - b.ordem)
              .map((amb, idx) => (
                <tr
                  key={amb.id}
                  className={clsx(
                    "border-t border-gray-100 hover:bg-brand/5 transition-colors",
                    idx % 2 === 0 ? "bg-white" : "bg-gray-50/50"
                  )}
                >
                  <td className="px-4 py-3 font-medium">
                    <EditableCell
                      ambienteId={amb.id}
                      field="nome"
                      value={amb.nome}
                      flag={amb.nome_flag}
                      placeholder="✗ nome do ambiente"
                    />
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{amb.camada ?? "—"}</td>
                  <td className="px-4 py-3 text-right">
                    <EditableCell
                      ambienteId={amb.id}
                      field="area"
                      value={amb.area != null ? amb.area.toFixed(2) : null}
                      flag={amb.area_flag}
                    />
                  </td>
                  <td className="px-4 py-3 text-right text-gray-700">
                    {amb.comprimento != null ? amb.comprimento.toFixed(2) : <span className="text-gray-300">—</span>}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-700">
                    {amb.largura != null ? amb.largura.toFixed(2) : <span className="text-gray-300">—</span>}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <EditableCell
                      ambienteId={amb.id}
                      field="perimetro"
                      value={amb.perimetro != null ? amb.perimetro.toFixed(2) : null}
                      flag={amb.perimetro_flag}
                    />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <EditableCell
                      ambienteId={amb.id}
                      field="pe_direito"
                      value={amb.pe_direito != null ? amb.pe_direito.toFixed(2) : null}
                      flag={amb.pe_direito_flag}
                    />
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="text-xs bg-gray-100 px-2 py-0.5 rounded-full text-gray-600">
                      {amb.fonte}
                    </span>
                  </td>
                </tr>
              ))}
          </tbody>
          <tfoot>
            <tr className="bg-brand/10 border-t-2 border-brand/20 font-bold">
              <td colSpan={2} className="px-4 py-3 text-brand">TOTAL</td>
              <td className="px-4 py-3 text-right text-brand">{totalArea.toFixed(2)} m²</td>
              <td colSpan={5} />
            </tr>
          </tfoot>
        </table>
      </div>

      <div className="flex gap-4 text-xs text-gray-500">
        <span><strong className="text-green-600">✓</strong> extraído</span>
        <span><strong className="text-yellow-600">⚠️</strong> estimado</span>
        <span><strong className="text-red-500">✗</strong> preencher</span>
      </div>
    </div>
  );
}
