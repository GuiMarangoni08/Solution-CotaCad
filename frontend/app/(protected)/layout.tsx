"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { LevantamentoProvider } from "@/contexts/LevantamentoContext";

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, loading, router]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <p className="text-gray-400">Carregando...</p>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return (
    <LevantamentoProvider>
      {children}
    </LevantamentoProvider>
  );
}
