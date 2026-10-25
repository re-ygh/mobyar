import React, { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import {
  fetchProducts,
  createSale,
  addSaleItem,
  removeSaleItem,
  finalizeSale,
  getSale,
  fetchCustomers,
} from "../api.js";

export default function SalesPage() {
  const { showToast } = useOutletContext();

  const [products, setProducts] = useState([]);
  const [customers, setCustomers] = useState([]);

  const [saleId, setSaleId] = useState(null);
  const [saleDetail, setSaleDetail] = useState(null);

  const [customerId, setCustomerId] = useState("");
  const [productId, setProductId] = useState("");
  const [qty, setQty] = useState(1);

  const loadBase = async () => {
    try {
      const [prods, custs] = await Promise.all([fetchProducts(false), fetchCustomers()]);
      setProducts(prods);
      setCustomers(custs);
    } catch (e) {
      showToast("error", e.message);
    }
  };

  useEffect(() => {
    loadBase();
  }, []);

  const startSale = async () => {
    try {
      const sale = await createSale(customerId ? Number(customerId) : null);
      setSaleId(sale.sale_id);
      const detail = await getSale(sale.sale_id);
      setSaleDetail(detail);
      showToast("success", `فروش جدید ایجاد شد: #${sale.sale_id}`);
    } catch (e) {
      showToast("error", e.message);
    }
  };

  const refreshSale = async () => {
    if (!saleId) return;
    try {
      const detail = await getSale(saleId);
      setSaleDetail(detail);
    } catch (e) {
      showToast("error", e.message);
    }
  };

  const addItem = async () => {
    if (!saleId) {
      showToast("error", "ابتدا فروش را ایجاد کنید.");
      return;
    }
    if (!productId) {
      showToast("error", "کالا را انتخاب کنید.");
      return;
    }
    try {
      const detail = await addSaleItem(saleId, Number(productId), Number(qty));
      setSaleDetail(detail);
      showToast("success", "آیتم اضافه شد.");
    } catch (e) {
      showToast("error", e.message);
    }
  };

  const removeItem = async (pid) => {
    try {
      const detail = await removeSaleItem(saleId, pid);
      setSaleDetail(detail);
      showToast("info", "آیتم حذف شد.");
    } catch (e) {
      showToast("error", e.message);
    }
  };

  const finalize = async () => {
    try {
      const sale = await finalizeSale(saleId);
      showToast("success", `فروش نهایی شد. مبلغ کل: ${Number(sale.total_price).toLocaleString()}`);
      await refreshSale();
    } catch (e) {
      showToast("error", e.message);
    }
  };

  return (
    <div>
      <h2>Sales</h2>

      <div className="grid">
        <div className="card">
          <h3>شروع فروش جدید</h3>
          <label>مشتری (اختیاری)</label>
          <select value={customerId} onChange={(e) => setCustomerId(e.target.value)}>
            <option value="">بدون مشتری (Walk-in)</option>
            {customers.map((c) => (
              <option key={c.user_id} value={c.user_id}>
                {c.user_id} - {c.name} ({c.phone})
              </option>
            ))}
          </select>

          <button className="btn primary" onClick={startSale}>ایجاد فروش</button>

          {saleDetail && (
            <div className="muted small">
              <div>Sale ID: {saleDetail.sale.sale_id}</div>
              <div>Status: {saleDetail.sale.status}</div>
              <div>Total: {Number(saleDetail.sale.total_price).toLocaleString()}</div>
            </div>
          )}
        </div>

        <div className="card">
          <h3>افزودن آیتم</h3>
          <label>کالا</label>
          <select value={productId} onChange={(e) => setProductId(e.target.value)}>
            <option value="">انتخاب کنید...</option>
            {products.map((p) => (
              <option key={p.product_id} value={p.product_id}>
                {p.product_id} - {p.name} (stock={p.stock})
              </option>
            ))}
          </select>

          <label>تعداد</label>
          <input type="number" value={qty} min="1" onChange={(e) => setQty(e.target.value)} />

          <button className="btn" onClick={addItem}>Add</button>

          {saleDetail && (
            <>
              <h4>اقلام فروش</h4>
              <table className="table">
                <thead>
                  <tr>
                    <th>کالا</th>
                    <th>تعداد</th>
                    <th>قیمت لحظه‌ای</th>
                    <th>جمع</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {saleDetail.items.length === 0 && <tr><td colSpan="5" className="muted">هنوز آیتمی اضافه نشده.</td></tr>}
                  {saleDetail.items.map((it) => (
                    <tr key={it.sale_item_id}>
                      <td>{it.product_name}</td>
                      <td>{it.quantity}</td>
                      <td>{Number(it.price_at_time).toLocaleString()}</td>
                      <td>{Number(it.line_total).toLocaleString()}</td>
                      <td>
                        <button className="btn danger" onClick={() => removeItem(it.product_id)}>Remove</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="row">
                <button className="btn primary" onClick={finalize} disabled={saleDetail.sale.status !== "draft"}>
                  Finalize
                </button>
                <button className="btn" onClick={refreshSale}>Refresh</button>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="muted small">
        نکته: کاهش موجودی و جلوگیری از موجودی منفی در DB با Trigger enforce شده است.
      </div>
    </div>
  );
}
