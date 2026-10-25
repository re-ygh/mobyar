import React from "react";
import { Outlet } from "react-router-dom";
import Nav from "./Nav.jsx";

export default function Layout({ user, onLogout, showToast }) {
  return (
    <div className="app">
      <header className="header">
        <div>
          <h1 className="title">موبیار</h1>
          <div className="subtitle">پنل مدیریت فروشگاه و تعمیرات موبایل (تک‌مرکز)</div>
        </div>

        <div className="userBox">
          <div className="userLine">{user.name} ({user.role_name})</div>
          <div className="userLine small">{user.phone}</div>
          <button className="btn" onClick={onLogout}>خروج</button>
        </div>
      </header>

      <div className="main">
        <Nav />
        <section className="content">
          <Outlet context={{ user, showToast }} />
        </section>
      </div>

      <footer className="footer">
        Mobyar - DB Course Project
      </footer>
    </div>
  );
}
