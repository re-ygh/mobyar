import React, { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { apiRequest, fetchServices } from "../api.js";

export default function ServicesPage() {
  const { showToast } = useOutletContext();
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);

  const [form, setForm] = useState({
    service_name: "",
    description: "",
    current_price: 0,
    is_active: true,
  });

  const load = async () => {
    setLoading(true);
    try {
      const s = await fetchServices(true);
      setServices(s);
    } catch (e) {
      showToast("error", e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const createService = async (e) => {
    e.preventDefault();
    try {
      await apiRequest("/services", { method: "POST", body: { ...form, current_price: Number(form.current_price) } });
      showToast("success", "خدمت ایجاد شد.");
      setForm({ service_name: "", description: "", current_price: 0, is_active: true });
      await load();
    } catch (e) {
      showToast("error", e.message);
    }
  };

  const updateService = async (serviceId, fields) => {
    try {
      await apiRequest(`/services/${serviceId}`, { method: "PUT", body: fields });
      showToast("success", "بروزرسانی شد.");
      await load();
    } catch (e) {
      showToast("error", e.message);
    }
  };

  const deactivateService = async (serviceId) => {
    try {
      await apiRequest(`/services/${serviceId}`, { method: "DELETE" });
      showToast("info", "خدمت غیرفعال شد.");
      await load();
    } catch (e) {
      showToast("error", e.message);
    }
  };

  return (
    <div>
      <h2>Services</h2>

      <div className="grid">
        <div className="card">
          <h3>افزودن خدمت</h3>
          <form className="form" onSubmit={createService}>
            <label>نام خدمت</label>
            <input value={form.service_name} onChange={(e) => setForm({ ...form, service_name: e.target.value })} required />

            <label>توضیح</label>
            <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />

            <label>قیمت</label>
            <input type="number" value={form.current_price} min="0" onChange={(e) => setForm({ ...form, current_price: e.target.value })} />

            <button className="btn primary">ایجاد</button>
          </form>
        </div>

        <div className="card">
          <h3>لیست خدمات</h3>
          {loading ? <p>در حال بارگذاری...</p> : (
            <table className="table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>نام</th>
                  <th>قیمت</th>
                  <th>فعال</th>
                  <th>عملیات</th>
                </tr>
              </thead>
              <tbody>
                {services.map((s) => (
                  <ServiceRow
                    key={s.service_id}
                    service={s}
                    onUpdate={updateService}
                    onDeactivate={deactivateService}
                  />
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

function ServiceRow({ service, onUpdate, onDeactivate }) {
  const [price, setPrice] = useState(service.current_price);

  const save = () => {
    onUpdate(service.service_id, { current_price: Number(price) });
  };

  return (
    <tr className={service.is_active ? "" : "mutedRow"}>
      <td>{service.service_id}</td>
      <td>{service.service_name}</td>
      <td>
        <input type="number" value={price} min="0" onChange={(e) => setPrice(e.target.value)} style={{ width: "110px" }} />
      </td>
      <td>{service.is_active ? "✓" : "×"}</td>
      <td>
        <button className="btn" onClick={save}>Save</button>
        {service.is_active && <button className="btn danger" onClick={() => onDeactivate(service.service_id)}>Deactivate</button>}
      </td>
    </tr>
  );
}
