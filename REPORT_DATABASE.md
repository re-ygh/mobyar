# REPORT_DATABASE — سامانه موبیار (PostgreSQL)

این گزارش روی **طراحی منطقی (Phase 2)** و **پیاده‌سازی دیتابیس (Phase 3)** تمرکز دارد.

---

## 1) معرفی دیتابیس

هدف دیتابیس موبیار:
- مدیریت کاربران و نقش‌ها
- مدیریت کالاها (محصولات) و دسته‌بندی
- مدیریت خدمات تعمیر
- ثبت فروش و اقلام فروش + کنترل موجودی
- ثبت سفارشات تعمیر + نگهداری قیمت لحظه‌ای سرویس
- ثبت تاریخچه قیمت و تاریخچه موجودی
- فراهم کردن View های گزارش مدیریتی

---

## 2) جدول به جدول: ستون‌ها، قیود و چرایی

> نکته: برای هر جدول، نوع داده و قیود با هدف یکپارچگی داده و اجرای سناریوهای واقعی انتخاب شده است.

### 2.1) role
**هدف:** نگهداری نقش‌ها به صورت lookup (حذف تکرار رشته نقش)

- PK: `role_id`
- UNIQUE: `role_name`
- CHECK: فقط `admin | staff | customer`

---

### 2.2) users
**هدف:** نگهداری کاربران سامانه (مدیر/کارمند/مشتری)

- PK: `user_id` (bigserial)  
  چون تعداد رکوردهای فروش/تعمیر در بلندمدت زیاد می‌شود و بهتر است کلیدهای اصلی bigint باشند.
- UNIQUE: `phone`, `email`
- `password_hash` (text): رمز در DB به صورت hash ذخیره می‌شود (نه plaintext)
- FK: `role_id → role`
- CHECK:
  - status محدود (`active | inactive`)
  - phone با regex (حداقل کنترل ظاهری)
- timestamps: `signup_date, created_at, updated_at`

---

### 2.3) brand / phone_model
**هدف:** داده عمومی و ثابت برای برند و مدل گوشی‌ها

- `phone_model` دارای FK به `brand`
- UNIQUE مرکب `(brand_id, model_name)` برای جلوگیری از تکرار مدل در یک برند

---

### 2.4) customer_phone
**هدف:** گوشی‌های متعلق به مشتری

- FK: `customer_id → users`
- FK: `model_id → phone_model`
- UNIQUE: `imei` (فرض پروژه: IMEI یکتا است)

---

### 2.5) category
**هدف:** دسته‌بندی کالاها

- UNIQUE: `category_name`
- CHECK: `type IN ('public','private')`  
  (معادل عمومی/اختصاصی در فاز ۱)

---

### 2.6) product
**هدف:** کالاهای فروشگاه

- `current_price numeric(12,2)`:
  - numeric برای پول از float دقیق‌تر است
- `stock int`:
  - موجودی باید عدد صحیح باشد
- CHECK:
  - قیمت و موجودی غیرمنفی
- `updated_by_user_id`:
  - برای اینکه Trigger بتواند `changed_by` را در تاریخچه‌ها پر کند

---

### 2.7) service
**هدف:** خدمات تعمیر (تعویض باتری، تعویض LCD، ...)

- `current_price numeric(12,2)`
- `updated_by_user_id` برای ثبت تاریخچه قیمت

---

### 2.8) product_price_history / service_price_history
**هدف:** ثبت تاریخچه تغییر قیمت

**چرا دو جدول جدا؟**  
چون حالت polymorphic در یک جدول (target_type/target_id) با FK استاندارد قابل enforce نیست و پیچیدگی Trigger و خطا را بالا می‌برد.

ستون‌ها:
- FK به product/service
- `old_price`, `new_price`
- `changed_by` (nullable، ON DELETE SET NULL)
- `change_date` (default now)

---

### 2.9) inventory_history
**هدف:** ثبت تاریخچه تغییر موجودی

- FK به product
- `old_stock`, `new_stock`  
  نگهداری مقدار قبل و بعد باعث می‌شود:
  - delta قابل محاسبه باشد
  - گزارش گیری و audit آسان شود
- `changed_by` و `update_date`

---

### 2.10) repair_order
**هدف:** ثبت سفارشات تعمیر

- `price_at_time`:
  - snapshot قیمت سرویس در لحظه ثبت
- CHECK status: `pending | in_progress | ready | delivered | cancelled`
- Trigger:
  - قیمت لحظه‌ای سرویس را کپی می‌کند
  - اعتبارسنجی می‌کند phone_id واقعاً متعلق به customer_id باشد
  - بعد از delivered/cancelled اجازه تغییر وضعیت نمی‌دهد
  - اجازه تغییر customer/phone/service را بعد از ایجاد نمی‌دهد

---

### 2.11) sale / sale_item
**هدف:** ثبت فروش کالا

- sale:
  - status: `draft | finalized | void`
  - `total_price` ذخیره شده اما مشتق است (denormalized controlled)
- sale_item:
  - UNIQUE `(sale_id, product_id)` (هر کالا یک بار در فاکتور، با quantity)
  - `price_at_time`: snapshot قیمت کالا در لحظه اضافه شدن به فاکتور

**نکته حیاتی:** کاهش موجودی فقط هنگام finalize انجام می‌شود.

---

## 3) روابط و چرایی

- users N→1 role  
- brand 1→N phone_model  
- users 1→N customer_phone  
- category 1→N product  
- product 1→N inventory_history  
- product 1→N product_price_history  
- service 1→N service_price_history  
- customer_phone 1→N repair_order  
- service 1→N repair_order  
- sale 1→N sale_item  
- product 1→N sale_item  
- users 0..1→N sale (customer_id nullable)

---

## 4) نرمال‌سازی (تا 3NF)

- **1NF:** همه ستون‌ها اتمیک هستند.
- **2NF:** هیچ وابستگی جزئی روی کلید مرکب مشکل‌زا وجود ندارد (sale_item با unique مرکب عملاً وابستگی‌ها را رعایت می‌کند).
- **3NF:** داده‌های وابسته به غیرکلید جدا شده‌اند (role، brand، category، histories).

### Denormalization کنترل‌شده
- `sale.total_price`  
- `product.stock`  
هر دو با Trigger ها **همیشه سازگار** نگه داشته می‌شوند.

---

## 5) Trigger ها و Function ها (Phase 3) — دقیق و رویداد محور

> فایل: `sql/02_triggers.sql`

### 5.1) tg_log_product_price_change
- **Event:** BEFORE UPDATE OF `product.current_price`
- **Action:** درج رکورد در `product_price_history`
- **Reason:** تاریخچه قیمت باید اتوماتیک و DB-level باشد.

**مثال:**
```sql
UPDATE product
SET current_price = 470000, updated_by_user_id = 2
WHERE product_id = 10;
```
⇒ یک رکورد در `product_price_history` ثبت می‌شود.

---

### 5.2) tg_log_service_price_change
- **Event:** BEFORE UPDATE OF `service.current_price`
- **Action:** درج رکورد در `service_price_history`

---

### 5.3) tg_log_product_stock_change
- **Event:** BEFORE UPDATE OF `product.stock`
- **Action:**
  - جلوگیری از stock منفی (RAISE EXCEPTION)
  - درج رکورد در `inventory_history(old_stock,new_stock,changed_by)`

---

### 5.4) tg_sale_item_before_write (INSERT/UPDATE)
- **Event:** BEFORE INSERT/UPDATE on `sale_item`
- **Actions:**
  - فقط اگر sale در حالت `draft` باشد اجازه تغییر می‌دهد
  - روی INSERT: `price_at_time` را از `product.current_price` می‌گیرد (snapshot)
  - روی INSERT/UPDATE: موجودی را چک می‌کند و اجازه quantity بیشتر از stock را نمی‌دهد

---

### 5.5) tg_sale_item_after_change (INSERT/UPDATE/DELETE)
- **Event:** AFTER INSERT/UPDATE/DELETE on `sale_item`
- **Action:** اجرای function `recalc_sale_total(sale_id)` برای sync شدن `sale.total_price`

---

### 5.6) tg_sale_before_status_update
- **Event:** BEFORE UPDATE OF `sale.status`
- **Finalize flow:** وقتی `draft → finalized`
  - اگر فاکتور خالی باشد، خطا
  - برای هر آیتم، stock چک می‌شود
  - stock هر محصول به اندازه quantity کم می‌شود (و inventory_history ثبت می‌گردد)
  - `finalized_at` پر می‌شود
  - `total_price` مجدد محاسبه می‌شود (ایمنی)

---

### 5.7) tg_repair_before_insert
- **Event:** BEFORE INSERT on `repair_order`
- **Actions:**
  - بررسی می‌کند phone متعلق به customer باشد
  - `price_at_time` را از `service.current_price` کپی می‌کند
  - status پیش‌فرض `pending`

---

### 5.8) tg_repair_before_update
- **Event:** BEFORE UPDATE on `repair_order`
- **Actions:**
  - customer/phone/service غیرقابل تغییر
  - price_at_time غیرقابل تغییر
  - بعد از delivered/cancelled وضعیت تغییر نکند
  - updated_at بروزرسانی شود

---

## 6) View ها (گزارش‌های مدیریتی)

> فایل: `sql/03_views.sql`

### 6.1) v_daily_sales
- فروش‌های finalized را روزانه گروه‌بندی می‌کند.

### 6.2) v_low_stock
- محصولات فعال با موجودی ≤ 5

### 6.3) v_open_repairs
- تعمیرات باز (pending/in_progress/ready)

### 6.4) v_top_products_30d
- 10 محصول پرفروش 30 روز اخیر

### 6.5) v_service_revenue_30d
- درآمد خدمات (تعمیرات delivered) در 30 روز اخیر

---

## 7) حداقل 10 کوئری نمونه کاربردی

### Query 1 — لیست کالاها همراه دسته
```sql
SELECT p.product_id, p.name, p.current_price, p.stock, c.category_name
FROM product p
JOIN category c ON c.category_id = p.category_id
ORDER BY p.product_id;
```

### Query 2 — کالاهای کم‌موجودی (threshold=3)
```sql
SELECT p.product_id, p.name, p.stock
FROM product p
WHERE p.is_active = TRUE AND p.stock <= 3
ORDER BY p.stock ASC;
```

### Query 3 — تاریخچه قیمت یک کالا
```sql
SELECT *
FROM product_price_history
WHERE product_id = 1
ORDER BY change_date DESC;
```

### Query 4 — تاریخچه قیمت یک خدمت
```sql
SELECT *
FROM service_price_history
WHERE service_id = 2
ORDER BY change_date DESC;
```

### Query 5 — تاریخچه تغییر موجودی یک کالا
```sql
SELECT *
FROM inventory_history
WHERE product_id = 1
ORDER BY update_date DESC;
```

### Query 6 — فاکتور و اقلام آن
```sql
SELECT s.sale_id, s.status, s.total_price, si.product_id, si.quantity, si.price_at_time
FROM sale s
JOIN sale_item si ON si.sale_id = s.sale_id
WHERE s.sale_id = 1;
```

### Query 7 — درآمد روزانه (View)
```sql
SELECT * FROM v_daily_sales;
```

### Query 8 — تعمیرات باز (View)
```sql
SELECT * FROM v_open_repairs;
```

### Query 9 — تعداد تعمیرات به تفکیک وضعیت
```sql
SELECT status, COUNT(*) AS cnt
FROM repair_order
GROUP BY status
ORDER BY cnt DESC;
```

### Query 10 — پرفروش‌ترین کالاها 30 روز اخیر
```sql
SELECT * FROM v_top_products_30d;
```

### Query 11 — فروش به تفکیک دسته‌بندی (تحلیل)
```sql
SELECT
  c.category_name,
  SUM(si.quantity * si.price_at_time) AS revenue
FROM sale_item si
JOIN sale s ON s.sale_id = si.sale_id
JOIN product p ON p.product_id = si.product_id
JOIN category c ON c.category_id = p.category_id
WHERE s.status = 'finalized'
GROUP BY c.category_name
ORDER BY revenue DESC;
```

### Query 12 — مشتریان پرتعمیر (Top 5)
```sql
SELECT
  u.user_id,
  u.name,
  COUNT(*) AS repair_count
FROM repair_order r
JOIN users u ON u.user_id = r.customer_id
GROUP BY u.user_id, u.name
ORDER BY repair_count DESC
LIMIT 5;
```

---

## 8) نکات اجرایی

- تمام تریگرها در DB enforce شده‌اند؛ یعنی حتی اگر API وجود نداشته باشد، دیتابیس از نظر موجودی/قیمت/فروش سازگار می‌ماند.
- برای اجرای دیتابیس: از docker-compose استفاده کنید تا فایل‌های SQL به صورت خودکار اجرا شوند.
