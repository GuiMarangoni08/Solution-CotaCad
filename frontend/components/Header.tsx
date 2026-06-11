"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

export default function Header() {
  const { user, logout, isAuthenticated, loading } = useAuth();
  const router = useRouter();

  function handleLogout() {
    logout();
    router.push("/login");
  }

  return (
    <header className="bg-brand text-white px-6 py-4 shadow-md">
      <div className="max-w-5xl mx-auto flex items-center justify-between">
        <Link href={isAuthenticated ? "/dashboard" : "/login"} className="flex items-center gap-3">
          <span className="text-2xl font-bold tracking-tight">QuanttunAI</span>
          <span className="text-brand-accent text-sm font-medium mt-1 hidden sm:block">
            — Leitura automática de projetos
          </span>
        </Link>

        {!loading && (
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <>
                <span className="text-sm text-white/70 hidden sm:block">{user?.email}</span>
                <button
                  onClick={handleLogout}
                  className="text-sm border border-white/30 px-3 py-1.5 rounded-lg hover:bg-white/10 transition-colors"
                >
                  Sair
                </button>
              </>
            ) : (
              <Link
                href="/login"
                className="text-sm bg-brand-accent text-white font-semibold px-4 py-1.5 rounded-lg hover:opacity-90 transition-opacity"
              >
                Entrar
              </Link>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
