"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import axios from "axios";
import Link from "next/link";
import TabelaAmbientes, { type Ambiente } from "@/components/TabelaAmbientes";
import ExportBar from "@/components/ExportBar";

const API = process.env.NEXT_PUBLIC_API_URL;

interface Projeto {
  id: string;
  nome: string;
  unidade: string;
  modo: string;
  fidelidade_score: number | null;
  confianca_score: number | null;
  ambientes: Ambiente[];
}

const MODO_LABEL: Record<string, string> = {
  dxf: "DXF",
  pdf: "PDF",
  "dxf+pdf": "DXF + PDF",
};

function ScoreBadge({ label, value, threshold = 70 }: { label: string; value: number | null; threshold?: number }) {
  if (value == null) return null;
  const color = value >= threshold ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700";
  return (
    <span className={`text-xs font-semibold px-3 py-1 rounded-full ${color}`}>
      {label}: {value}%
    </span>
  );
}

export default function ProjetoPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [projeto, setProjeto] = useState<Projeto | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios
      .get(`${API}/projeto/${id}`)
      .then((r) => { setProjeto(r.data); setLoading(false); })
      .catch(() => { setLoading(false); router.push("/"); });
  }, [id, router]);

  if (loading) {
    return <p className="text-center py-16 text-gray-400">Carregando projeto...</p>;
  }

  if (!projeto) return null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <Link href="/" className="text-sm text-gray-400 hover:text-brand mb-1 inline-block">
            ← Todos os projetos
          </Link>
          <h1 className="text-2xl font-bold text-brand">{projeto.nome}</h1>
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <span className="text-xs bg-brand/10 text-brand px-3 py-1 rounded-full font-medium">
              {MODO_LABEL[projeto.modo] || projeto.modo}
            </span>
            <span className="text-xs text-gray-400">Unidade original: {projeto.unidade}</span>
            <ScoreBadge label="Fidelidade DXF×PDF" value={projeto.fidelidade_score} />
            <ScoreBadge label="Confiança PDF" value={projeto.confianca_score} />
          </div>
        </div>

        <ExportBar projetoId={projeto.id} ambientes={projeto.ambientes} />
      </div>

      {/* Alerta baixa fidelidade */}
      {projeto.fidelidade_score != null && projeto.fidelidade_score < 70 && (
        <div className="bg-orange-50 border border-orange-200 rounded-lg px-4 py-3 text-sm text-orange-800">
          <strong>⚠️ Fidelidade baixa ({projeto.fidelidade_score}%)</strong> — poucas medidas do PDF coincidem com o DXF.
          Os dados do DXF foram mantidos sem complemento do PDF. Verifique as medidas manualmente.
        </div>
      )}

      {/* Tabela */}
      <TabelaAmbientes
        ambientes={projeto.ambientes}
        onChange={(updated) => setProjeto({ ...projeto, ambientes: updated })}
      />

      {/* Resumo */}
      <div className="card text-sm text-gray-500">
        <p>
          <strong>{projeto.ambientes.length}</strong> ambiente(s) detectado(s) —&nbsp;
          <strong>{projeto.ambientes.filter((a) => a.area != null).length}</strong> com área &nbsp;·&nbsp;
          <strong>{projeto.ambientes.filter((a) => a.pe_direito != null).length}</strong> com pé direito
        </p>
      </div>
    </div>
  );
}
