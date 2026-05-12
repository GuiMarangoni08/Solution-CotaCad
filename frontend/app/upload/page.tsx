"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import toast from "react-hot-toast";
import UploadZone from "@/components/UploadZone";

const API = process.env.NEXT_PUBLIC_API_URL || "https://cotacad-solution.duckdns.org/api";

export default function UploadPage() {
  const router = useRouter();
  const [dxf, setDxf] = useState<File | null>(null);
  const [pdf, setPdf] = useState<File | null>(null);
  const [nome, setNome] = useState("");
  const [unidade, setUnidade] = useState("mm");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!dxf && !pdf) {
      toast.error("Envie pelo menos um arquivo DXF ou PDF");
      return;
    }

    const form = new FormData();
    if (dxf) form.append("dxf_file", dxf);
    if (pdf) form.append("pdf_file", pdf);
    form.append("nome", nome || dxf?.name || pdf?.name || "Projeto");
    form.append("unidade", unidade);

    setLoading(true);
    const t = toast.loading("Analisando projeto... isso pode levar alguns segundos");

    try {
      const res = await axios.post(`${API}/upload`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success("Projeto analisado com sucesso!", { id: t });
      router.push(`/projeto/${res.data.id}`);
    } catch (err: unknown) {
      const msg =
        axios.isAxiosError(err) && err.response?.data?.detail
          ? err.response.data.detail
          : "Erro ao processar arquivo";
      toast.error(msg, { id: t });
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-brand">Novo projeto</h1>
        <p className="text-gray-500 text-sm mt-1">
          Envie o DXF, o PDF ou ambos. O sistema extrai as medidas automaticamente.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="card space-y-5">
        {/* Nome */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Nome do projeto
          </label>
          <input
            type="text"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            placeholder="Ex: Apartamento Silva — Planta Baixa"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/40"
          />
        </div>

        {/* Unidade */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Unidade do projeto
          </label>
          <select
            value={unidade}
            onChange={(e) => setUnidade(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/40"
          >
            <option value="mm">Milímetros (mm) — padrão brasileiro</option>
            <option value="cm">Centímetros (cm)</option>
            <option value="m">Metros (m)</option>
          </select>
          <p className="text-xs text-gray-400 mt-1">
            Tudo será convertido para metros (m²) no resultado.
          </p>
        </div>

        {/* Arquivos */}
        <UploadZone
          label="Arquivo DXF (AutoCAD / SketchUp)"
          accept={{ "application/dxf": [".dxf"] }}
          file={dxf}
          onFile={setDxf}
        />

        <UploadZone
          label="Arquivo PDF (opcional — complementa o DXF ou substitui)"
          accept={{ "application/pdf": [".pdf"] }}
          file={pdf}
          onFile={setPdf}
        />

        {/* Info modo */}
        {dxf && pdf && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 text-sm text-blue-800">
            <strong>Modo DXF + PDF:</strong> O sistema vai comparar os dois arquivos e usar o PDF para complementar medidas faltantes do DXF.
          </div>
        )}
        {!dxf && pdf && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-3 text-sm text-yellow-800">
            <strong>Modo só PDF:</strong> Medidas extraídas do PDF. Precisão depende da qualidade do arquivo.
          </div>
        )}

        <button type="submit" disabled={loading} className="btn-primary w-full">
          {loading ? "Analisando..." : "Analisar projeto"}
        </button>
      </form>
    </div>
  );
}
