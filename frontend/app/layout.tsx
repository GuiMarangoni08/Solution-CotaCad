import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Toaster } from "react-hot-toast";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "CotaCAD — Leitura de Projetos",
  description: "Extração automática de medidas de projetos arquitetônicos",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className={inter.className}>
        <header className="bg-brand text-white px-6 py-4 shadow-md">
          <div className="max-w-5xl mx-auto flex items-center gap-3">
            <span className="text-2xl font-bold tracking-tight">CotaCAD</span>
            <span className="text-brand-accent text-sm font-medium mt-1">
              — Leitura automática de projetos
            </span>
          </div>
        </header>
        <main className="max-w-5xl mx-auto px-4 py-8">{children}</main>
        <Toaster position="top-right" />
      </body>
    </html>
  );
}
