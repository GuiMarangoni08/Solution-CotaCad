"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import axios from "axios";

const API = process.env.NEXT_PUBLIC_API_URL || "https://unlock-method-kingston-partition.trycloudflare.com/api";

interface ProjetoItem {
  id: string;
  nome: string;
  modo: string;
  criado_em: string;
}

const MODO_LABEL: Record<string, string> = {
  dxf: "DXF",
  pdf: "PDF",
  "dxf+pdf": "DXF + PDF",
};

export default function Home() {
  const [projetos, setProjetos] = useState<ProjetoItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/projetos`).then((r) => {
      setProjetos(r.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-brand">Projetos</h1>
        <Link href="/upload" className="btn-primary">
          + Novo projeto
        </Link>
      </div>

      {loading && (
        <p className="text-gray-400 text-center py-12">Carregando...</p>
      )}

      {!loading && projetos.length === 0 && (
        <div className="card text-center py-16 text-gray-400">
          <p className="text-lg">Nenhum projeto ainda.</p>
          <Link href="/upload" className="btn-primary inline-block mt-4">
            Enviar primeiro projeto
          </Link>
        </div>
      )}

      {projetos.length > 0 && (
        <div className="space-y-3">
          {projetos.map((p) => (
            <Link key={p.id} href={`/projeto/${p.id}`}>
              <div className="card hover:border-brand transition-colors cursor-pointer flex items-center justify-between">
                <div>
                  <p className="font-semibold text-gray-800">{p.nome}</p>
                  <p className="text-sm text-gray-400">{p.criado_em}</p>
                </div>
                <span className="text-xs font-medium bg-brand/10 text-brand px-3 py-1 rounded-full">
                  {MODO_LABEL[p.modo] || p.modo}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
