import React, { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { reportDailySales, reportLowStock, reportOpenRepairs } from "../api.js";

export default function DashboardPage() {
  const { showToast } = useOutletContext();
  const [daily, setDaily] = useState([]);
  const [lowStock, setLowStock] = useState([]);
  const [openRepairs, setOpenRepairs] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const d = await reportDailySales();
      const ls = await reportLowStock(5);
      const or = await reportOpenRepairs();
      setDaily(d);
      setLowStock(ls);
      setOpenRepairs(or);
    } catch (e) {
      showToast("error", e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div>
      <h2>Dashboard</h2>
      <button className="btn" onClick={load} disabled={loading}>
        {loading ? "در حال بروزرسانی..." : "Refresh"}
      </button>

      <div className="grid">
        <div className="card">
          <h3>فروش روزانه (Finalized)</h3>
          <table className="table">
            <thead>
              <tr>
                <th>روز</th>
                <th>تعداد فروش</th>
                <th>درآمد</th>
              </tr>
            </thead>
            <tbody>
              {daily.length === 0 && <tr><td colSpan="3" className="muted">داده‌ای موجود نیست.</td></tr>}
              {daily.map((r) => (
                <tr key={r.sale_day}>
                  <td>{r.sale_day}</td>
                  <td>{r.sales_count}</td>
                  <td>{Number(r.revenue).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card">
          <h3>کمبود موجودی (≤ 5)</h3>
          <div className="muted small">تعداد: {lowStock.length}</div>
          <table className="table">
            <thead>
              <tr>
                <th>کالا</th>
                <th>دسته</th>
                <th>موجودی</th>
              </tr>
            </thead>
            <tbody>
              {lowStock.length === 0 && <tr><td colSpan="3" className="muted">همه چیز اوکی است.</td></tr>}
              {lowStock.map((p) => (
                <tr key={p.product_id}>
                  <td>{p.name}</td>
                  <td>{p.category_name}</td>
                  <td>{p.stock}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card">
          <h3>تعمیرات باز</h3>
          <div className="muted small">تعداد: {openRepairs.length}</div>
          <table className="table">
            <thead>
              <tr>
                <th>کد</th>
                <th>مشتری</th>
                <th>خدمت</th>
                <th>وضعیت</th>
              </tr>
            </thead>
            <tbody>
              {openRepairs.length === 0 && <tr><td colSpan="4" className="muted">موردی موجود نیست.</td></tr>}
              {openRepairs.map((r) => (
                <tr key={r.repair_id}>
                  <td>{r.repair_id}</td>
                  <td>{r.customer_name}</td>
                  <td>{r.service_name}</td>
                  <td>{r.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
