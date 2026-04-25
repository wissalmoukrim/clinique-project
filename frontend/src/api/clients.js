const BASE_URL = "http://127.0.0.1:8000/api";

export async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    credentials: "include", // 🔥 SESSION DJANGO
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  let data = {};
  try {
    data = await res.json();
  } catch {}

  if (!res.ok) {
    throw data;
  }

  return data;
}