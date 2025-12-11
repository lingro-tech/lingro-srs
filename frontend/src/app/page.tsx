"use client";

import { useEffect, useState } from "react";
import { devLogin, fetchMe, type User } from "@/lib/api";

export default function HomePage() {
  const [telegramId, setTelegramId] = useState("123");
  const [username, setUsername] = useState("testuser");

  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Загружаем токен из localStorage при старте
  useEffect(() => {
    const stored = localStorage.getItem("auth_token");
    if (stored) {
      setToken(stored);
      loadUser(stored);
    }
  }, []);

  async function loadUser(tok: string) {
    try {
      setLoading(true);
      setError(null);
      const u = await fetchMe(tok);
      setUser(u);
    } catch (err: any) {
      console.error("loadUser error:", err);        // ← добавили лог
      setError(err.message ?? "Ошибка загрузки пользователя");
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  async function handleDevLogin(e: React.FormEvent) {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);

      const resp = await devLogin(Number(telegramId), username);
      const tok = resp.access_token;

      setToken(tok);
      localStorage.setItem("auth_token", tok);

      await loadUser(tok);
    } catch (err: any) {
      setError(err.message ?? "Ошибка dev-login");
    } finally {
      setLoading(false);
    }
  }

  function handleLogout() {
    setToken(null);
    setUser(null);
    localStorage.removeItem("auth_token");
  }

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1 style={{ fontSize: 28, fontWeight: 600 }}>
        Lingro SRS — dev login
      </h1>

      <section style={{ marginTop: 20, maxWidth: 400 }}>
        <form onSubmit={handleDevLogin}>
          <div style={{ marginBottom: 12 }}>
            <label>telegram_id</label>
            <input
              value={telegramId}
              onChange={(e) => setTelegramId(e.target.value)}
              style={{ width: "100%", padding: 6, border: "1px solid #aaa" }}
            />
          </div>

          <div style={{ marginBottom: 12 }}>
            <label>username</label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={{ width: "100%", padding: 6, border: "1px solid #aaa" }}
            />
          </div>

          <button
            type="submit"
            style={{
              padding: "8px 16px",
              background: "black",
              color: "white",
              borderRadius: 4,
            }}
            disabled={loading}
          >
            {loading ? "Загрузка…" : "Войти (dev)"}
          </button>

          {token && (
            <button
              type="button"
              onClick={handleLogout}
              style={{
                padding: "8px 16px",
                marginLeft: 10,
                border: "1px solid #888",
                borderRadius: 4,
              }}
            >
              Выйти
            </button>
          )}
        </form>

        {error && (
          <p style={{ color: "red", marginTop: 12 }}>
            Ошибка: {error}
          </p>
        )}
      </section>

      <section style={{ marginTop: 30, maxWidth: 400 }}>
        <h2 style={{ fontSize: 20, fontWeight: 600 }}>
          Состояние пользователя (/api/v1/me)
        </h2>

        {loading && <p>Загрузка…</p>}
        {!loading && !user && <p>Не авторизован.</p>}

        {user && (
          <pre
            style={{
              background: "#f0f0f0",
              padding: 12,
              borderRadius: 6,
              fontSize: 12,
            }}
          >
            {JSON.stringify(user, null, 2)}
          </pre>
        )}
      </section>
    </main>
  );
}

