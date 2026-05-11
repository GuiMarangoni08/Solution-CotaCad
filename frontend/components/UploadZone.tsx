"use client";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import clsx from "clsx";

interface Props {
  label: string;
  accept: Record<string, string[]>;
  file: File | null;
  onFile: (f: File | null) => void;
  required?: boolean;
}

export default function UploadZone({ label, accept, file, onFile, required }: Props) {
  const onDrop = useCallback(
    (accepted: File[]) => { if (accepted[0]) onFile(accepted[0]); },
    [onFile]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    maxFiles: 1,
  });

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      <div
        {...getRootProps()}
        className={clsx(
          "border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors",
          isDragActive ? "border-brand bg-brand/5" : "border-gray-300 hover:border-brand/50",
          file && "border-green-400 bg-green-50"
        )}
      >
        <input {...getInputProps()} />
        {file ? (
          <div className="space-y-1">
            <p className="text-green-700 font-medium">✓ {file.name}</p>
            <p className="text-xs text-gray-400">
              {(file.size / 1024 / 1024).toFixed(1)} MB — clique para trocar
            </p>
          </div>
        ) : (
          <div className="space-y-1">
            <p className="text-gray-500">
              {isDragActive ? "Solte o arquivo aqui" : "Arraste ou clique para selecionar"}
            </p>
            <p className="text-xs text-gray-400">
              {Object.values(accept).flat().join(", ")}
            </p>
          </div>
        )}
      </div>
      {file && (
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); onFile(null); }}
          className="text-xs text-red-400 hover:text-red-600 mt-1"
        >
          Remover arquivo
        </button>
      )}
    </div>
  );
}
