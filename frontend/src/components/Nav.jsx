import React from "react";
import { NavLink } from "react-router-dom";

export default function Nav() {
  const linkClass = ({ isActive }) => isActive ? "navLink active" : "navLink";

  return (
    <nav className="nav">
      <NavLink to="/" className={linkClass} end>Dashboard</NavLink>
      <NavLink to="/products" className={linkClass}>Products</NavLink>
      <NavLink to="/services" className={linkClass}>Services</NavLink>
      <NavLink to="/sales" className={linkClass}>Sales</NavLink>
      <NavLink to="/repairs" className={linkClass}>Repairs</NavLink>
    </nav>
  );
}
