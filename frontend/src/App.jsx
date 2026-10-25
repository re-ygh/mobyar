import React, { useEffect, useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";

import { getMe, clearToken } from "./api.js";
import Layout from "./components/Layout.jsx";
import Toast from "./components/Toast.jsx";

import LoginPage from "./pages/Login.jsx";
import DashboardPage from "./pages/Dashboard.jsx";
import ProductsPage from "./pages/Products.jsx";
import ServicesPage from "./pages/Services.jsx";
import SalesPage from "./pages/Sales.jsx";
import RepairsPage from "./pages/Repairs.jsx";

export default function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);
  const [toast, setToast] = useState(null);

  const showToast = (type, message) => {
    setToast({ type, message, ts: Date.now() });
  };

  const logout = () => {
    clearToken();
    setUser(null);
    showToast("info", "خروج انجام شد.");
  };

  useEffect(() => {
    // On app load, try to validate token
    (async () => {
      try {
        const me = await getMe();
        setUser(me);
      } catch (e) {
        setUser(null);
      } finally {
        setChecking(false);
      }
    })();
  }, []);

  if (checking) {
    return <div className="container"><p>در حال بارگذاری...</p></div>;
  }

  return (
    <>
      {toast && <Toast type={toast.type} message={toast.message} />}
      <Routes>
        <Route path="/login" element={
          user
            ? <Navigate to="/" replace />
            : <LoginPage onLogin={(u) => { setUser(u); showToast("success", "ورود موفق!"); }} onError={(m) => showToast("error", m)} />
        } />

        <Route path="/" element={
          user
            ? <Layout user={user} onLogout={logout} showToast={showToast} />
            : <Navigate to="/login" replace />
        }>
          <Route index element={<DashboardPage />} />
          <Route path="products" element={<ProductsPage />} />
          <Route path="services" element={<ServicesPage />} />
          <Route path="sales" element={<SalesPage />} />
          <Route path="repairs" element={<RepairsPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
