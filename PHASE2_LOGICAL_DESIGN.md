# فاز ۲ — طراحی منطقی (Logical Design) سامانه موبیار

این طراحی منطقی بر اساس خروجی فاز ۱ شما (ER + موجودیت‌ها و کاردینالیتی‌ها) انجام شده است و برای اجرای فاز ۳ آماده‌سازی شده است.

---

## 1) Relational Schema نهایی

> نکته: برای جلوگیری از مشکل کلمه رزرو شده `user` در PostgreSQL، جدول کاربران را `users` نام‌گذاری کرده‌ایم.  
> نام‌گذاری همه جداول و ستون‌ها snake_case است.

### 1.1) role
- **PK:** `role_id`
- **Unique:** `role_name`

| ستون | نوع | قیود |
|---|---|---|
| role_id | serial | PK |
| role_name | varchar(20) | NOT NULL, UNIQUE, CHECK IN ('admin','staff','customer') |

**Index:** Unique روی role_name (به صورت خودکار ایندکس ایجاد می‌کند)

---

### 1.2) users
- **PK:** `user_id`
- **FK:** `role_id → role(role_id)`
- **Unique:** `phone`, `email`
- **Check:** `status`, فرمت `phone`
- **Default:** `status='active'`, `signup_date=now()`, `created_at=now()`, `updated_at=now()`

| ستون | نوع | قیود |
|---|---|---|
| user_id | bigserial | PK |
| name | varchar(120) | NOT NULL |
| phone | varchar(20) | NOT NULL, UNIQUE, CHECK regex |
| email | varchar(255) | UNIQUE, nullable |
| password_hash | text | NOT NULL |
| role_id | int | NOT NULL, FK |
| status | varchar(20) | NOT NULL, DEFAULT 'active', CHECK IN ('active','inactive') |
| signup_date | timestamptz | DEFAULT now() |
| created_at | timestamptz | DEFAULT now() |
| updated_at | timestamptz | DEFAULT now() |

**Index:** `idx_users_role_id(role_id)`

---

### 1.3) brand
| ستون | نوع | قیود |
|---|---|---|
| brand_id | serial | PK |
| brand_name | varchar(80) | NOT NULL, UNIQUE |

---

### 1.4) phone_model
- **FK:** `brand_id → brand(brand_id)`
- **Unique:** `(brand_id, model_name)`

| ستون | نوع | قیود |
|---|---|---|
| model_id | serial | PK |
| model_name | varchar(120) | NOT NULL |
| brand_id | int | NOT NULL, FK |

**Index:** `idx_phone_model_brand_id(brand_id)`

---

### 1.5) customer_phone
- **FK:** `model_id → phone_model(model_id)`
- **FK:** `customer_id → users(user_id)`
- **Unique:** `imei`

| ستون | نوع | قیود |
|---|---|---|
| phone_id | bigserial | PK |
| model_id | int | NOT NULL, FK |
| color | varchar(40) | nullable |
| imei | varchar(20) | NOT NULL, UNIQUE, CHECK regex |
| customer_id | bigint | NOT NULL, FK |
| created_at | timestamptz | DEFAULT now() |

**Index:**  
- `idx_customer_phone_customer_id(customer_id)`  
- `idx_customer_phone_model_id(model_id)`

---

### 1.6) category
- **Unique:** `category_name`
- **Check:** `type IN ('public','private')`

| ستون | نوع | قیود |
|---|---|---|
| category_id | serial | PK |
| category_name | varchar(120) | NOT NULL, UNIQUE |
| type | varchar(20) | NOT NULL, DEFAULT 'public', CHECK |

---

### 1.7) product
- **FK:** `category_id → category(category_id)`
- **FK:** `updated_by_user_id → users(user_id)` (برای ثبت تاریخچه‌ها)
- **Check:** قیمت و موجودی غیرمنفی

| ستون | نوع | قیود |
|---|---|---|
| product_id | bigserial | PK |
| name | varchar(160) | NOT NULL |
| description | text | nullable |
| image | text | nullable |
| current_price | numeric(12,2) | NOT NULL, CHECK >=0 |
| stock | int | NOT NULL, DEFAULT 0, CHECK >=0 |
| category_id | int | NOT NULL, FK |
| is_active | boolean | NOT NULL, DEFAULT TRUE |
| updated_by_user_id | bigint | FK, nullable, ON DELETE SET NULL |
| created_at | timestamptz | DEFAULT now() |
| updated_at | timestamptz | DEFAULT now() |

**Indexهای مهم:**  
- `idx_product_category_id(category_id)`  
- `idx_product_stock(stock)`  
- `idx_product_active(is_active)`  
- `idx_product_name_lower(lower(name))` برای سرچ

---

### 1.8) service
- **FK:** `updated_by_user_id → users(user_id)` برای ثبت تاریخچه قیمت

| ستون | نوع | قیود |
|---|---|---|
| service_id | bigserial | PK |
| service_name | varchar(160) | NOT NULL, UNIQUE |
| description | text | nullable |
| current_price | numeric(12,2) | NOT NULL, CHECK >=0 |
| is_active | boolean | NOT NULL, DEFAULT TRUE |
| updated_by_user_id | bigint | FK, nullable, ON DELETE SET NULL |
| created_at | timestamptz | DEFAULT now() |
| updated_at | timestamptz | DEFAULT now() |

**Index:** `idx_service_active(is_active)`

---

## 2) تصمیم درباره PriceHistory

در فاز ۱ یک جدول `PriceHistory(target_type, target_id, ...)` وجود داشت.  
در مدل رابطه‌ای، این حالت یک **ارتباط polymorphic** ایجاد می‌کند و با FK عادی قابل تضمین نیست.

### تصمیم نهایی (پیشنهادی و پیاده‌سازی شده)
✅ **دو جدول جداگانه ایجاد شد:**
- `product_price_history(product_id, old_price, new_price, changed_by, change_date)`
- `service_price_history(service_id, old_price, new_price, changed_by, change_date)`

**مزیت‌ها:**
- یکپارچگی کامل با FK واقعی
- ساده‌تر شدن Queryها و گزارش‌ها
- حذف نیاز به Trigger پیچیده برای کنترل target_type/target_id

---

## 3) RepairOrder و snapshot قیمت

### repair_order
- **price_at_time** در لحظه ثبت از `service.current_price` کپی می‌شود (Trigger BEFORE INSERT).
- با تغییر قیمت سرویس، سفارش‌های قبلی تغییر نمی‌کنند.

این الزام دقیقاً مطابق نیاز پروژه enforce شده است.

---

## 4) تصمیم درباره total_price و stock (سازگاری)

### 4.1) sale.total_price
- از لحاظ منطقی: `SUM(quantity * price_at_time)` روی اقلام فروش است.
- برای کارایی و راحتی گزارش‌گیری، در جدول sale ذخیره شده (denormalize کنترل‌شده).
- با Triggerهای `AFTER INSERT/UPDATE/DELETE` روی `sale_item` همیشه recalculated می‌شود ⇒ سازگار می‌ماند.

### 4.2) product.stock
- از لحاظ تحلیلی، stock از تاریخچه موجودی قابل استخراج است، اما در عمل:
  - عملیات فروش باید سریع باشد
  - چک عدم منفی شدن باید در لحظه انجام شود
- بنابراین `product.stock` به عنوان **وضعیت جاری** ذخیره شده (denormalize کنترل‌شده).
- با Trigger:
  - موجودی منفی ممنوع (DB-level)
  - هر تغییر موجودی به `inventory_history` ثبت می‌شود

---

## 5) نرمال‌سازی (حداقل 3NF)

- 1NF: تمام ستون‌ها اتمیک هستند (تلفن/ایمیل/...)، لیست یا چندمقداری داخل ستون نداریم.
- 2NF: جداولی که کلید مرکب ندارند (اکثراً) مشکلی ندارند؛ در sale_item که unique مرکب داریم، وابستگی‌ها به کلید رعایت می‌شود.
- 3NF: داده‌های وابسته به غیرکلید جدا شده‌اند:
  - Role جدا از Users
  - Brand جدا از PhoneModel
  - Category جدا از Product
  - تاریخچه‌ها جدا از داده‌های جاری
- Denormalization کنترل‌شده: فقط `sale.total_price` و `product.stock` (با دلیل کارایی + Trigger برای تضمین سازگاری)

---

## 6) وضعیت‌ها (Status ها)

- `users.status`: `active | inactive`
- `sale.status`: `draft | finalized | void`
- `repair_order.status`: `pending | in_progress | ready | delivered | cancelled`

این مقادیر با CHECK constraint محدود شده‌اند.

---

## 7) فایل‌های SQL پیاده‌سازی

- `sql/01_schema.sql` ساخت جداول + قیود + ایندکس‌ها
- `sql/02_triggers.sql` تریگرهای تاریخچه/موجودی/فروش/تعمیر
- `sql/03_views.sql` ویوهای گزارش مدیریتی
- `sql/04_seed.sql` داده نمونه برای دمو
