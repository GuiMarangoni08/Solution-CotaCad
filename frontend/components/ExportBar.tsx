"use client";
import axios from "axios";
import toast from "react-hot-toast";

const API = process.env.NEXT_PUBLIC_API_URL;

interface Ambiente {
  nome: string | null;
  nome_flag: string;
  area: number | null;
  area_flag: string;
  perimetro: number | null;
  perimetro_flag: string;
  pe_direito: number | null;
  pe_direito_flag: string;
  camada: string | null;
  fonte: string;
}

interface Props {
  projetoId: string;
  ambientes: Ambiente[];
}

const FLAG = { confirmed: "", estimated: " ⚠️", missing: " ✗" } as Record<string, string>;

function toTSV(ambientes: Ambiente[]): string {
  const header = ["Ambiente", "Camada", "Área (m²)", "Perímetro (m)", "Pé Direito (m)", "Fonte"].join("\t");
  const rows = ambientes.map((a) => [
    (a.nome ?? "— sem nome —") + (FLAG[a.nome_flag] ?? ""),
    a.camada ?? "—",
    a.area != null ? `${a.area.toFixed(2)}${FLAG[a.area_flag] ?? ""}` : "✗",
    a.perimetro != null ? `${a.perimetro.toFixed(2)}${FLAG[a.perimetro_flag] ?? ""}` : "✗",
    a.pe_direito != null ? `${a.pe_direito.toFixed(2)}${FLAG[a.pe_direito_flag] ?? ""}` : "✗",
    a.fonte,
  ].join("\t"));
  return [header, ...rows].join("\n");
}

export default function ExportBar({ projetoId, ambientes }: Props) {
  function copiarTabela() {
    const tsv = toTSV(ambientes);
    navigator.clipboard.writeText(tsv).then(() => {
      toast.success("Tabela copiada! Cole direto no Excel (Ctrl+V)");
    });
  }

  async function baixarXlsx() {
    const t = toast.loading("Gerando arquivo...");
    try {
      const res = await axios.get(`${API}/projeto/${projetoId}/export`, {
        responseType: "blob",
      });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `cotacad_${projetoId}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Download iniciado!", { id: t });
    } catch {
      toast.error("Erro ao gerar arquivo", { id: t });
    }
  }

  return (
    <div className="flex gap-3 flex-wrap">
      <button onClick={copiarTabela} className="btn-secondary flex items-center gap-2">
        <span>📋</span> Copiar tabela (Excel)
      </button>
      <button onClick={baixarXlsx} className="btn-primary flex items-center gap-2">
        <span>⬇️</span> Baixar .xlsx
      </button>
    </div>
  );
}
