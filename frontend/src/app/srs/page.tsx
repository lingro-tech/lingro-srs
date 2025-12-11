"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchNextCard, submitReview, type SRSCard } from "@/lib/api";

export default function SrsPage() {
    const [token, setToken] = useState<string | null>(null);
    const [card, setCard] = useState<SRSCard | null>(null);
    const [showTranslation, setShowTranslation] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [noCards, setNoCards] = useState(false);
    const [lastGrade, setLastGrade] = useState<number | null>(null);


    // Берём токен из localStorage при загрузке
    useEffect(() => {
        const stored = localStorage.getItem("auth_token");
        if (stored) {
            setToken(stored);
            void loadNext(stored);
        }
    }, []);

    async function loadNext(tok?: string) {
        const t = tok ?? token;
        if (!t) return;

        try {
            setLoading(true);
            setError(null);
            setShowTranslation(false);
            const next = await fetchNextCard(t);
            console.log("fetchNextCard →", next);  // <= добавили
            
            if (!next) {
                setCard(null);
                setNoCards(true);
            } else {
                setCard(next);
                setNoCards(false);
            }
        } catch (err: any) {
            console.error("loadNext error:", err);
            setError(err.message ?? "Ошибка загрузки карточки");
            setCard(null);
        } finally {
            setLoading(false);
        }
    }

    async function handleGrade(grade: number) {
        if (!token || !card) return;
        try {
            setLoading(true);
            setError(null);
            setLastGrade(grade);               // запомним последнюю оценку
            await submitReview(token, card.id, grade);
            await loadNext(token);
        } catch (err: any) {
            console.error("submitReview error:", err);
            setError(err.message ?? "Ошибка отправки оценки");
        } finally {
            setLoading(false);
        }
    }

    if (!token) {
        return (
            <main style={{ padding: "2rem", fontFamily: "sans-serif" }}>
                <h1 style={{ fontSize: 28, fontWeight: 600 }}>Lingro SRS — обучение</h1>
                <p style={{ marginTop: 16 }}>
                    Нет токена авторизации. Сначала выполните вход на&nbsp;
                    <Link href="/" style={{ color: "blue", textDecoration: "underline" }}>
                        главной странице
                    </Link>
                    .
                </p>
            </main>
        );
    }

    return (
        <main style={{ padding: "2rem", fontFamily: "sans-serif" }}>
            <header
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "1.5rem",
                }}
            >
                <h1 style={{ fontSize: 28, fontWeight: 600 }}>Lingro SRS — обучение</h1>
                <Link href="/" style={{ fontSize: 14, textDecoration: "underline" }}>
                    dev-login
                </Link>
            </header>

            {loading && !card && <p>Загрузка карточки…</p>}

            {error && (
                <p style={{ color: "red", marginBottom: "1rem" }}>Ошибка: {error}</p>
            )}

            {noCards && !card && (
                <p style={{ marginTop: "1rem" }}>
                    Сейчас для вас нет карточек. Попробуйте позже.
                </p>
            )}

            {card && (
                <section
                    style={{
                        border: "1px solid #ddd",
                        borderRadius: 8,
                        padding: "1.5rem",
                        maxWidth: 600,
                        marginBottom: "1.5rem",
                    }}
                >
                    <div style={{ marginBottom: "1rem", fontSize: 12, color: "#666" }}>
                        Card ID: {card.id} · language: {card.language}
                    </div>

                    <div style={{ fontSize: 24, marginBottom: "1rem" }}>{card.text}</div>

                    <div style={{ marginBottom: "1rem" }}>
                        <button
                            type="button"
                            onClick={() => setShowTranslation((v) => !v)}
                            style={{
                                padding: "6px 12px",
                                borderRadius: 4,
                                border: "1px solid #888",
                                fontSize: 14,
                            }}
                        >
                            {showTranslation ? "Скрыть перевод" : "Показать перевод"}
                        </button>
                    </div>

                    <div
                        style={{
                            minHeight: "2rem",
                            fontSize: 18,
                            color: showTranslation ? "#111" : "#bbb",
                            fontStyle: showTranslation ? "normal" : "italic",
                        }}
                    >
                        {card.translation
                            ? showTranslation
                                ? card.translation
                                : "Перевод скрыт"
                            : "Перевода нет"}
                    </div>
                </section>
            )}

            <section style={{ maxWidth: 600 }}>
                <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: "0.75rem" }}>
                    Оценка карточки
                </h2>
                <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.5rem" }}>
                    {[1, 2, 3, 4].map((g) => (
                        <button
                            key={g}
                            type="button"
                            onClick={() => handleGrade(g)}
                            disabled={loading || !card}
                            style={{
                                flex: 1,
                                padding: "0.75rem 0",
                                borderRadius: 6,
                                border: "1px solid #333",
                                background: "#111",
                                color: "white",
                                fontSize: 16,
                                cursor: loading || !card ? "default" : "pointer",
                            }}
                        >
                            {g}
                        </button>
                    ))}
                </div>
                {lastGrade !== null && (
                    <div style={{ fontSize: 12, color: "#666", marginTop: "0.5rem" }}>
                        Последняя оценка: {lastGrade}
                    </div>
                )}

                <div style={{ fontSize: 12, color: "#666" }}>
                    1 — совсем не помню · 4 — легко и уверенно.
                </div>
            </section>
        </main>
    );
}
