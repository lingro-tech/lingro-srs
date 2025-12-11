export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://192.168.1.66:8000";

/* ===== Типы ===== */

export type User = {
  id: number;
  telegram_id: number;
  username: string | null;
  first_name: string | null;
  last_name: string | null;
  photo_url: string | null;
  created_at: string;
  updated_at: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type SRSCard = {
  id: number;
  text: string;
  translation: string | null;
  language: string;
};

/* ===== Auth ===== */

export async function devLogin(
  telegramId: number,
  username: string | null,
): Promise<TokenResponse> {
  const params = new URLSearchParams();
  params.set("telegram_id", String(telegramId));
  if (username) params.set("username", username);
  params.set("secret", "local_dev_only"); // dev-secret из backend/.env

  const res = await fetch(
    `${API_BASE_URL}/api/v1/auth/dev-login?${params.toString()}`,
    { method: "POST" },
  );

  if (!res.ok) {
    throw new Error(`Dev login failed: ${res.status} ${res.statusText}`);
  }

  return res.json();
}

export async function fetchMe(token: string): Promise<User> {
  const res = await fetch(`${API_BASE_URL}/api/v1/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    throw new Error(`fetchMe failed: ${res.status} ${res.statusText}`);
  }

  return res.json();
}

/* ===== SRS ===== */

export async function fetchNextCard(token: string): Promise<SRSCard | null> {
  const res = await fetch(`${API_BASE_URL}/api/v1/srs/next`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (res.status === 204) {
    // Нет карточек
    return null;
  }

  if (!res.ok) {
    throw new Error(`fetchNextCard failed: ${res.status} ${res.statusText}`);
  }

  return res.json();
}

export async function submitReview(
  token: string,
  cardId: number,
  grade: number,
): Promise<void> {
  const body = JSON.stringify({
    card_id: cardId,
    grade,
  });

  const res = await fetch(`${API_BASE_URL}/api/v1/srs/review`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body,
  });

  if (!res.ok) {
    throw new Error(`submitReview failed: ${res.status} ${res.statusText}`);
  }
}
