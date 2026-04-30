import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import "./App.css";
import ProtectedRoute from "./routes/ProtectedRoute";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import AdminDashboard from "./pages/admin/AdminDashboard";
import MedecinDashboard from "./pages/medecin/MedecinDashboard";
import PatientDashboard from "./pages/patient/PatientDashboard";
import HomePage from "./pages/public/HomePage";
import Specialites from "./pages/public/Specialites";
import MedecinsPublic from "./pages/public/MedecinsPublic";
import Contact from "./pages/public/Contact";
import PrendreRdvPublic from "./pages/public/PrendreRdvPublic";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/specialites" element={<Specialites />} />
        <Route path="/medecins-public" element={<MedecinsPublic />} />
        <Route path="/contact" element={<Contact />} />
        <Route path="/prendre-rdv" element={<PrendreRdvPublic />} />

        <Route
          path="/admin"
          element={
            <ProtectedRoute allowedRoles={["admin"]}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/medecin"
          element={
            <ProtectedRoute allowedRoles={["medecin"]}>
              <MedecinDashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/patient"
          element={
            <ProtectedRoute allowedRoles={["patient"]}>
              <PatientDashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute allowedRoles={["secretaire", "infirmier", "comptable", "securite", "chauffeur"]}>
              <Dashboard />
            </ProtectedRoute>
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
