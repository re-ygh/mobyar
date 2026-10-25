# Mobyar (موبیار) — Database Course Project (Phase 2 + Phase 3)

> نسخهٔ آموزشی برای اجرای محلی است. کاربران و رمزهای عبور بخش Seed نمونه‌اند؛ قبل از هر استقرار واقعی باید آن‌ها و `JWT_SECRET_KEY` تغییر کنند. کد Python از نظر نحو، فایل Compose و build رابط React بررسی شدند. اجرای کامل با Docker در این آماده‌سازی تأیید نشد، چون دانلود وابستگی‌های Python از PyPI در محیط بررسی timeout شد.

یک سامانه یکپارچه برای **مدیریت فروشگاه موبایل** + **مرکز تعمیرات موبایل** (تک‌مرکز / تک‌فروشگاهی).

## تکنولوژی‌ها

- **DBMS:** PostgreSQL
- **Backend:** FastAPI (Python) + SQLAlchemy (Query های متنی)
- **Frontend:** React + Vite
- **Run:** Docker Compose

---

## اجرای سریع (پیشنهادی)

### 1) پیش‌نیاز
- Docker و Docker Compose نصب باشد.

### 2) اجرا
در ریشه پروژه:

```bash
docker compose up --build
```

### 3) لینک‌ها
- Frontend: `http://localhost:5173`
- Backend (Swagger UI): `http://localhost:8000/api/v1/docs`
- Health check: `http://localhost:8000/health`

PostgreSQL فقط در شبکهٔ داخلی Compose در دسترس است و پورت میزبان را اشغال نمی‌کند.

### 4) کاربران نمونه (Seed)
| نقش | phone | password |
|---|---|---|
| Admin | 09120000000 | admin123 |
| Staff | 09121111111 | staff123 |
| Customer | 09123333333 | cust123 |

---

## ساختار پوشه‌ها

```text
mobyar/
  sql/
    01_schema.sql
    02_triggers.sql
    03_views.sql
    04_seed.sql
  backend/
    app/
      core/
      routers/
      schemas/
      main.py
    requirements.txt
    Dockerfile
  frontend/
    src/
      pages/
      components/
      api.js
      App.jsx
      main.jsx
      styles.css
    package.json
    vite.config.js
    Dockerfile
  docker-compose.yml
  PHASE2_LOGICAL_DESIGN.md
  REPORT_DATABASE.md
  REPORT_FINAL.md
  .env.example
  README.md
```

---

## نکات مهم دیتابیس (مطابق نیازمندی پروژه)

- **کاهش موجودی و جلوگیری از موجودی منفی** با Trigger در DB enforce شده است.
- در **RepairOrder** ستون `price_at_time` در لحظه ثبت از `service.current_price` کپی می‌شود و بعداً تغییر نمی‌کند.
- در **SaleItem** ستون `price_at_time` در لحظه ثبت از `product.current_price` کپی می‌شود و بعداً تغییر نمی‌کند.
- `sale.total_price` مشتق شده از اقلام فروش است؛ اما برای کارایی ذخیره شده و با Trigger همیشه sync می‌شود.

---

## ریست کردن دیتابیس

اگر قبلاً اجرا کرده‌اید و می‌خواهید از ابتدا seed دوباره اعمال شود:

```bash
docker compose down -v
docker compose up --build
```

(گزینه `-v` باعث حذف Volume دیتابیس می‌شود.)
