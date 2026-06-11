'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useLevantamento } from '@/contexts/LevantamentoContext';

export default function NovoLevantamentoPage() {
  const router = useRouter();
  const { criarLevantamento, loading, error, limparErro } = useLevantamento();

  const [formData, setFormData] = useState({
    orc_numero: '',
    nome: '',
    cliente: '',
    empreendimento: '',
    tipologia: 'decorado',
    dxf_file: null as File | null,
  });

  const [dragActive, setDragActive] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFileSelect = (file: File) => {
    if (file.name.endsWith('.dxf') || file.type === 'application/octet-stream') {
      setFormData(prev => ({ ...prev, dxf_file: file }));
      limparErro();
    } else {
      alert('Por favor, selecione um arquivo .dxf');
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === 'dragenter' || e.type === 'dragover');
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    limparErro();

    if (!formData.dxf_file) {
      alert('Selecione um arquivo DXF');
      return;
    }

    try {
      const fd = new FormData();
      fd.append('dxf_file', formData.dxf_file);
      fd.append('orc_numero', formData.orc_numero);
      fd.append('nome', formData.nome);
      fd.append('cliente', formData.cliente);
      fd.append('empreendimento', formData.empreendimento);
      fd.append('tipologia', formData.tipologia);

      const levId = await criarLevantamento(fd);
      router.push(`/dashboard/levantamentos/${levId}`);
    } catch (err) {
      // Erro já está no context
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Novo Levantamento</h1>
        <p className="text-gray-600 mb-8">Envie um arquivo DXF para processar automaticamente</p>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-lg p-8 space-y-6">
          {/* Informações do Projeto */}
          <div>
            <h2 className="text-lg font-semibold mb-4">Informações do Projeto</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ORC Número
                </label>
                <input
                  type="text"
                  name="orc_numero"
                  value={formData.orc_numero}
                  onChange={handleChange}
                  required
                  className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="21463"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipologia
                </label>
                <select
                  name="tipologia"
                  value={formData.tipologia}
                  onChange={handleChange}
                  className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="stand">Stand de Vendas</option>
                  <option value="decorado">Apartamento Decorado</option>
                  <option value="triplex">Triplex</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome
                </label>
                <input
                  type="text"
                  name="nome"
                  value={formData.nome}
                  onChange={handleChange}
                  required
                  className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Exemplar Morais"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cliente
                </label>
                <input
                  type="text"
                  name="cliente"
                  value={formData.cliente}
                  onChange={handleChange}
                  className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Solution"
                />
              </div>

              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Empreendimento
                </label>
                <input
                  type="text"
                  name="empreendimento"
                  value={formData.empreendimento}
                  onChange={handleChange}
                  className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Morais de Barros"
                />
              </div>
            </div>
          </div>

          {/* Upload DXF */}
          <div>
            <h2 className="text-lg font-semibold mb-4">Arquivo DXF</h2>
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                dragActive
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 bg-gray-50 hover:border-gray-400'
              }`}
            >
              <input
                type="file"
                accept=".dxf"
                onChange={(e) => e.target.files && handleFileSelect(e.target.files[0])}
                className="hidden"
                id="dxf-input"
              />
              <label htmlFor="dxf-input" className="cursor-pointer">
                <div className="text-4xl mb-2">📁</div>
                <p className="font-semibold text-gray-900 mb-1">
                  {formData.dxf_file ? formData.dxf_file.name : 'Arraste um arquivo DXF aqui'}
                </p>
                <p className="text-sm text-gray-600">ou clique para selecionar</p>
              </label>
            </div>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Processando...' : 'Criar Levantamento'}
          </button>
        </form>
      </div>
    </div>
  );
}
