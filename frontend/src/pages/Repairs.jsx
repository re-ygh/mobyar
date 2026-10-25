import React, { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import {
  fetchCustomers,
  fetchCustomerPhones,
  fetchServices,
  createRepair,
  listRepairs,
  updateRepairStatus,
} from "../api.js";

export default function RepairsPage() {
  const { showToast } = useOutletContext();

  const [customers, setCustomers] = useState([]);
  const [phones, setPhones] = useState([]);
  const [services, setServices] = useState([]);
  const [repairs, setRepairs] = useState([]);

  const [customerId, setCustomerId] = useState("");
  const [phoneId, setPhoneId] = useState("");
  const [serviceId, setServiceId] = useState("");
  const [notes, setNotes] = useState("");

  const loadBase = async () => {
    try {
      const [custs, srvs] = await Promise.all([fetchCustomers(), fetchServices(false)]);
      setCustomers(custs);
      setServices(srvs);
    } catch (e) {
      showToast("error", e.message);
    }
  };

  const loadRepairs = async () => {
    try {
      const rs = await listRepairs("");
      setRepairs(rs);
    } catch (e) {
      showToast("error", e.message);
    }
  };

  useEffect(() => {
    loadBase();
    loadRepairs();
  }, []);

  useEffect(() => {
    if (!customerId) {
      setPhones([]);
      setPhoneId("");
      return;
    }
    (async () => {
      try {
        const ph = await fetchCustomerPhones(Number(customerId));
        setPhones(ph);
        setPhoneId(ph.length ? ph[0].phone_id : "");
      } catch (e) {
        showToast("error", e.message);
      }
    })();
  }, [customerId]);

  const submit = async (e) => {
    e.preventDefault();
    try {
      await createRepair({
        customer_id: Number(customerId),
        phone_id: Number(phoneId),
        service_id: Number(serviceId),
        notes: notes || null,
      });
      showToast("success", "سفارش تعمیر ثبت شد.");
      setNotes("");
      await loadRepairs();
    } catch (e) {
      showToast("error", e.message);
    }
  };

  const changeStatus = async (repairId, status) => {
    try {
      await updateRepairStatus(repairId, status);
      showToast("success", "وضعیت بروزرسانی شد.");
      await loadRepairs();
    } catch (e) {
      showToast("error", e.message);
    }
  };

  return (
    <div>
      <h2>Repairs</h2>

      <div className="grid">
        <div className="card">
          <h3>ثبت سفارش تعمیر</h3>
          <form className="form" onSubmit={submit}>
            <label>مشتری</label>
            <select value={customerId} onChange={(e) => setCustomerId(e.target.value)} required>
              <option value="">انتخاب کنید...</option>
              {customers.map((c) => (
                <option key={c.user_id} value={c.user_id}>
                  {c.user_id} - {c.name} ({c.phone})
                </option>
              ))}
            </select>

            <label>گوشی مشتری</label>
            <select value={phoneId} onChange={(e) => setPhoneId(e.target.value)} required>
              {phones.length === 0 && <option value="">(گوشی‌ای برای این مشتری ثبت نشده)</option>}
              {phones.map((p) => (
                <option key={p.phone_id} value={p.phone_id}>
                  {p.phone_id} - {p.brand_name} {p.model_name} (IMEI: {p.imei})
                </option>
              ))}
            </select>

            <label>خدمت</label>
            <select value={serviceId} onChange={(e) => setServiceId(e.target.value)} required>
              <option value="">انتخاب کنید...</option>
              {services.map((s) => (
                <option key={s.service_id} value={s.service_id}>
                  {s.service_id} - {s.service_name} (price={Number(s.current_price).toLocaleString()})
                </option>
              ))}
            </select>

            <label>یادداشت</label>
            <input value={notes} onChange={(e) => setNotes(e.target.value)} />

            <button className="btn primary">ثبت</button>
          </form>

          <div className="muted small">
            نکته: price_at_time از قیمت لحظه‌ای سرویس کپی می‌شود و بعداً تغییر نمی‌کند (DB Trigger).
          </div>
        </div>

        <div className="card">
          <h3>لیست سفارشات تعمیر</h3>
          <button className="btn" onClick={loadRepairs}>Refresh</button>
          <table className="table">
            <thead>
              <tr>
                <th>#</th>
                <th>Customer</th>
                <th>Service</th>
                <th>Status</th>
                <th>PriceAtTime</th>
                <th>Change</th>
              </tr>
            </thead>
            <tbody>
              {repairs.map((r) => (
                <tr key={r.repair_id}>
                  <td>{r.repair_id}</td>
                  <td>{r.customer_id}</td>
                  <td>{r.service_id}</td>
                  <td>{r.status}</td>
                  <td>{Number(r.price_at_time).toLocaleString()}</td>
                  <td>
                    <select value={r.status} onChange={(e) => changeStatus(r.repair_id, e.target.value)}>
                      <option value="pending">pending</option>
                      <option value="in_progress">in_progress</option>
                      <option value="ready">ready</option>
                      <option value="delivered">delivered</option>
                      <option value="cancelled">cancelled</option>
                    </select>
                  </td>
                </tr>
              ))}
              {repairs.length === 0 && <tr><td colSpan="6" className="muted">داده‌ای موجود نیست.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
