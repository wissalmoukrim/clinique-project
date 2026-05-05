export const API_BASE_URL = "http://127.0.0.1:8000";
export const API_URL = `${API_BASE_URL}/api`;

// JWTs are stored in localStorage to keep this academic/dev project simple.
// In production, prefer short-lived access tokens with refresh tokens in HTTP-only secure cookies.
export function getAccessToken() {
  return localStorage.getItem("access");
}

export function getRefreshToken() {
  return localStorage.getItem("refresh");
}

export function getCurrentUser() {
  const rawUser = localStorage.getItem("user");

  if (!rawUser) {
    return null;
  }

  try {
    return JSON.parse(rawUser);
  } catch {
    logout();
    return null;
  }
}

export function saveAuth({ access, refresh, user }) {
  localStorage.setItem("access", access);
  if (refresh) {
    localStorage.setItem("refresh", refresh);
  }
  localStorage.setItem("user", JSON.stringify(user));
}

export function logout() {
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
  localStorage.removeItem("user");
}

export function isTokenExpired(token) {
  if (!token) {
    return true;
  }

  try {
    const payload = JSON.parse(window.atob(token.split(".")[1]));
    return payload.exp ? payload.exp * 1000 <= Date.now() : false;
  } catch {
    return true;
  }
}

export async function login(username, password) {
  let response;

  try {
    response = await fetch("http://127.0.0.1:8000/api/auth/jwt/login/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    });
  } catch {
    throw new Error("Erreur reseau: impossible de contacter Django sur http://127.0.0.1:8000. Verifiez que le backend est lance et que CORS est active.");
  }

  const data = await readJson(response);

  if (!response.ok) {
    throw new Error(data?.error || data?.detail || "Identifiants invalides");
  }

  if (!data?.access || !data?.user?.role) {
    throw new Error("Invalid login response");
  }

  saveAuth(data);
  return data;
}

export async function publicFetch(endpoint, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  let response;

  try {
    response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
    });
  } catch {
    throw new Error("Erreur reseau: backend Django indisponible sur http://127.0.0.1:8000.");
  }

  const data = await readJson(response);

  if (!response.ok) {
    throw new Error(data?.error || data?.detail || "Erreur API");
  }

  return data;
}

export async function apiFetch(endpoint, options = {}) {
  const token = getAccessToken();

  if (!token || isTokenExpired(token)) {
    logout();
    window.location.href = "/login";
    throw new Error("Session expired");
  }

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
    Authorization: `Bearer ${token}`,
  };

  let response;

  try {
    response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
    });
  } catch {
    throw new Error("Erreur reseau: backend Django indisponible sur http://127.0.0.1:8000.");
  }

  const data = await readJson(response);

  if (!response.ok) {
    if (response.status === 401) {
      logout();
      window.location.href = "/login";
    }

    throw new Error(data?.error || data?.detail || "Erreur API");
  }

  return data;
}

async function readJson(response) {
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    return null;
  }
  return response.json();
}
