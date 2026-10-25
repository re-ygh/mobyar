import React, { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { apiRequest, fetchCategories, fetchProducts } from "../api.js";

export default function ProductsPage() {
  const { showToast } = useOutletContext();
  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  // Create form
  const [form, setForm] = useState({
    name: "",
    description: "",
    current_price: 0,
    stock: 0,
    category_id: "",
    is_active: true,
  });

  const load = async () => {
    setLoading(true);
    try {
      const [cats, prods] = await Promise.all([fetchCategories(), fetchProducts(true)]);
      setCategories(cats);
      setProducts(prods);
    } catch (e) {
      showToast("error", e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const createProduct = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...form,
        current_price: Number(form.current_price),
        stock: Number(form.stock),
        category_id: Number(form.category_id),
      };
      const created = await apiRequest("/products", { method: "POST", body: payload });
      showToast("success", `کالا ایجاد شد: #${created.product_id}`);
      setForm({ name: "", description: "", current_price: 0, stock: 0, category_id: "", is_active: true });
      await load();
    } catch (e) {
      showToast("error", e.message);
    }
  };

  const updateProduct = async (productId, fields) => {
    try {
      await apiRequest(`/products/${productId}`, { method: "PUT", body: fields });
      showToast("success", "بروزرسانی شد.");
      await load();
    } catch (e) {
      showToast("error", e.message);
    }
  };

  const deactivateProduct = async (productId) => {
    try {
      await apiRequest(`/products/${productId}`, { method: "DELETE" });
      showToast("info", "کالا غیرفعال شد.");
      await load();
    } catch (e) {
      showToast("error", e.message);
    }
  };

  return (
    <div>
      <h2>Products</h2>

      <div className="grid">
        <div className="card">
          <h3>افزودن کالا</h3>
          <form className="form" onSubmit={createProduct}>
            <label>نام</label>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />

            <label>توضیح</label>
            <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />

            <label>قیمت</label>
            <input type="number" value={form.current_price} onChange={(e) => setForm({ ...form, current_price: e.target.value })} min="0" />

            <label>موجودی</label>
            <input type="number" value={form.stock} onChange={(e) => setForm({ ...form, stock: e.target.value })} min="0" />

            <label>دسته</label>
            <select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })} required>
              <option value="">انتخاب کنید...</option>
              {categories.map((c) => <option key={c.category_id} value={c.category_id}>{c.category_name}</option>)}
            </select>

            <button className="btn primary">ایجاد</button>
          </form>
        </div>

        <div className="card">
          <h3>لیست کالاها</h3>
          {loading ? <p>در حال بارگذاری...</p> : (
            <table className="table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>نام</th>
                  <th>دسته</th>
                  <th>قیمت</th>
                  <th>موجودی</th>
                  <th>فعال</th>
                  <th>عملیات</th>
                </tr>
              </thead>
              <tbody>
                {products.map((p) => (
                  <ProductRow
                    key={p.product_id}
                    product={p}
                    categories={categories}
                    onUpdate={updateProduct}
                    onDeactivate={deactivateProduct}
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

function ProductRow({ product, categories, onUpdate, onDeactivate }) {
  const [price, setPrice] = useState(product.current_price);
  const [stock, setStock] = useState(product.stock);
  const [categoryId, setCategoryId] = useState(product.category_id);

  const save = () => {
    onUpdate(product.product_id, {
      current_price: Number(price),
      stock: Number(stock),
      category_id: Number(categoryId),
      is_active: product.is_active,
    });
  };

  return (
    <tr className={product.is_active ? "" : "mutedRow"}>
      <td>{product.product_id}</td>
      <td>{product.name}</td>
      <td>
        <select value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
          {categories.map((c) => <option key={c.category_id} value={c.category_id}>{c.category_name}</option>)}
        </select>
      </td>
      <td>
        <input type="number" value={price} min="0" onChange={(e) => setPrice(e.target.value)} style={{ width: "110px" }} />
      </td>
      <td>
        <input type="number" value={stock} min="0" onChange={(e) => setStock(e.target.value)} style={{ width: "90px" }} />
      </td>
      <td>{product.is_active ? "✓" : "×"}</td>
      <td>
        <button className="btn" onClick={save}>Save</button>
        {product.is_active && <button className="btn danger" onClick={() => onDeactivate(product.product_id)}>Deactivate</button>}
      </td>
    </tr>
  );
}
