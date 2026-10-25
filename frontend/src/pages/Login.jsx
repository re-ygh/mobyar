import React, { useState } from "react";
import { login, setToken } from "../api.js";

export default function LoginPage({ onLogin, onError }) {
  const [phone, setPhone] = useState("09120000000");
  const [password, setPassword] = useState("admin123");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await login(phone, password);
      setToken(res.access_token);
      onLogin(res.user);
    } catch (err) {
      onError(err.message || "خطا در ورود");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container center">
      <div className="card">
        <h2>ورود به پنل</h2>
        <p className="muted">برای دمو از کاربران seed استفاده کنید.</p>

        <form onSubmit={submit} className="form">
          <label>شماره موبایل</label>
          <input value={phone} onChange={(e) => setPhone(e.target.value)} />

          <label>رمز عبور</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />

          <button className="btn primary" disabled={loading}>
            {loading ? "در حال ورود..." : "ورود"}
          </button>
        </form>

        <div className="muted small">
          Admin: 09120000000 / admin123 <br/>
          Staff: 09121111111 / staff123 <br/>
          Customer: 09123333333 / cust123
        </div>
      </div>
    </div>
  );
}
