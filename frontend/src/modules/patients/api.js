import { apiFetch } from "../../api/client";

export async function getPatients(token) {
  return await apiFetch("/patients/", "GET", null, token);
}

export async function createPatient(data, token) {
  return await apiFetch("/patients/", "POST", data, token);
}

export async function deletePatient(id, token) {
  return await apiFetch(`/patients/${id}/`, "DELETE", null, token);
}