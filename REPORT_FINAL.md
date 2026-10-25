# REPORT_FINAL — سامانه موبیار (Phase 2 + Phase 3)

## 1) معرفی سامانه

**موبیار** یک سامانه یکپارچه برای مدیریت یک مرکز (تک‌فروشگاهی) است که هم فروش کالا (محصولات موبایل) و هم سفارش‌های تعمیرات را مدیریت می‌کند.

اهداف اصلی:
- مدیریت کاربران و نقش‌ها
- مدیریت کالاها/دسته‌ها/خدمات
- ثبت فروش و کنترل موجودی
- ثبت تعمیرات و کنترل قیمت لحظه‌ای سرویس
- گزارش‌های مدیریتی روزانه و عملیاتی

---

## 2) نقش‌ها (Roles)

### Admin
- مدیریت کامل سیستم
- ایجاد/ویرایش دسته‌ها/کالاها/خدمات
- مشاهده گزارش‌ها

### Staff
- ثبت فروش و finalize فروش
- ثبت و بروزرسانی سفارش تعمیر
- بروزرسانی موجودی و قیمت

### Customer
- در این نسخه UI جداگانه ندارد (برای سادگی پروژه)، ولی در DB وجود دارد و می‌تواند به عنوان مشتری فروش/تعمیر ثبت شود.

---

## 3) سناریوهای اصلی (Use-cases)

### 3.1) مدیریت کالا
1) کارمند وارد می‌شود  
2) کالا را ایجاد می‌کند  
3) قیمت یا موجودی را تغییر می‌دهد  
4) دیتابیس به صورت خودکار:
   - تاریخچه قیمت/موجودی را ثبت می‌کند
   - از موجودی منفی جلوگیری می‌کند

### 3.2) ثبت فروش
1) کارمند یک sale (draft) می‌سازد  
2) اقلام را اضافه می‌کند  
3) سیستم قیمت هر قلم را همان لحظه snapshot می‌کند (price_at_time)  
4) کارمند finalize می‌کند  
5) دیتابیس:
   - موجودی را کم می‌کند
   - منفی شدن موجودی را غیرممکن می‌کند
   - total_price را sync می‌کند

### 3.3) ثبت تعمیرات
1) کارمند مشتری و گوشی مشتری را انتخاب می‌کند  
2) خدمت تعمیر را انتخاب می‌کند  
3) سفارش تعمیر ثبت می‌شود  
4) دیتابیس:
   - قیمت لحظه‌ای سرویس را در repair_order.price_at_time ثبت می‌کند
   - تضمین می‌کند phone واقعاً متعلق به customer باشد
   - بعد از delivered/cancelled اجازه تغییر وضعیت نمی‌دهد

---

## 4) معماری سیستم

### 4.1) Database (PostgreSQL)
- جداول، قیود، تریگرها، ویوها
- همه قوانین حیاتی (Consistency) در DB enforce می‌شوند.

### 4.2) Backend (FastAPI)
- REST API برای عملیات CRUD و workflow ها
- احراز هویت با JWT
- Role-based access (admin/staff)

### 4.3) Frontend (React)
- UI حداقلی اما قابل ارائه
- اتصال واقعی به API
- نمایش پیام موفقیت/خطا

---

## 5) پوشه‌بندی پروژه

- `sql/` تمام اسکریپت‌های دیتابیس
- `backend/` سرویس API
- `frontend/` رابط کاربری
- `docker-compose.yml` اجرای یک‌پارچه

جزئیات کامل در `README.md` آمده است.

---

## 6) جریان‌های اصلی در API

### Auth
- `POST /api/v1/auth/login`
- `GET  /api/v1/auth/me`

### Products
- `GET  /api/v1/products`
- `POST /api/v1/products`
- `PUT  /api/v1/products/{id}`
- `DELETE /api/v1/products/{id}` (soft deactivate)

### Services
- مشابه محصولات

### Sales
- `POST /api/v1/sales` (create draft)
- `POST /api/v1/sales/{id}/items`
- `POST /api/v1/sales/{id}/finalize`

### Repairs
- `POST /api/v1/repairs`
- `PATCH /api/v1/repairs/{id}/status`

### Reports
- `GET /api/v1/reports/daily-sales`
- `GET /api/v1/reports/low-stock`
- `GET /api/v1/reports/open-repairs`

---

## 7) راه‌اندازی قدم به قدم

### روش Docker (پیشنهادی)
```bash
docker compose up --build
```

سپس:
- Frontend: `http://localhost:5173`
- Backend docs: `http://localhost:8000/api/v1/docs`

### ریست دیتابیس
```bash
docker compose down -v
docker compose up --build
```

---

## 8) داده‌های دمو (Seed)

اسکریپت `sql/04_seed.sql` داده‌های نمونه ایجاد می‌کند:
- نقش‌ها
- کاربران
- محصولات/خدمات
- چند فروش finalized
- یک سفارش تعمیر
- چند تغییر قیمت/موجودی برای ایجاد تاریخچه

---

## 9) نکات کیفیت و انطباق با الزامات پروژه

- کدها کامنت‌گذاری شده‌اند (SQL/Backend/Frontend)
- نام‌گذاری snake_case
- status ها محدود و مستند
- enforce موجودی منفی در DB
- snapshot قیمت در SaleItem و RepairOrder
- گزارش‌ها با View + endpoint
- پروژه قابل اجرا با docker-compose
