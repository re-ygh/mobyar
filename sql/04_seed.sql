-- 04_seed.sql
-- ------------------------------------------------------------
-- Mobyar (موبیار) - Demo Seed Data
-- This file inserts enough sample data to demonstrate the system.
--
-- Login demo users (phone / password):
--  - Admin:   09120000000 / admin123
--  - Staff:   09121111111 / staff123
--  - Customer:09123333333 / cust123
-- ------------------------------------------------------------

-- Roles
INSERT INTO role (role_name) VALUES
  ('admin'),
  ('staff'),
  ('customer');

-- Users
INSERT INTO users (name, phone, email, password_hash, role_id, status)
VALUES
  ('مدیر سیستم', '09120000000', 'admin@mobyar.local', '$2b$12$7d/5J6aEmsRKERmnvZkMoOaF8Kwo6/lHXcd8Ga07jk.ExDYHNLk9y', (SELECT role_id FROM role WHERE role_name='admin'), 'active'),
  ('کارمند ۱',   '09121111111', 'staff1@mobyar.local', '$2b$12$0Nv4LMfCpR4n7bOi8x86mOu/EAboxCJbi.k07dA3JkixZugKhjzOi', (SELECT role_id FROM role WHERE role_name='staff'), 'active'),
  ('کارمند ۲',   '09122222222', 'staff2@mobyar.local', '$2b$12$0Nv4LMfCpR4n7bOi8x86mOu/EAboxCJbi.k07dA3JkixZugKhjzOi', (SELECT role_id FROM role WHERE role_name='staff'), 'active'),
  ('مشتری ۱',    '09123333333', 'cust1@mobyar.local',  '$2b$12$R8oZvhmmrIQuRSzmaZD.BuXWqd3Z1zItSv0ZXeNp5y/0FCiInMoBK', (SELECT role_id FROM role WHERE role_name='customer'), 'active'),
  ('مشتری ۲',    '09124444444', 'cust2@mobyar.local',  '$2b$12$R8oZvhmmrIQuRSzmaZD.BuXWqd3Z1zItSv0ZXeNp5y/0FCiInMoBK', (SELECT role_id FROM role WHERE role_name='customer'), 'active');

-- Brands (public data)
INSERT INTO brand (brand_name) VALUES
  ('Apple'),
  ('Samsung'),
  ('Xiaomi');

-- Phone models (public data)
INSERT INTO phone_model (model_name, brand_id)
VALUES
  ('iPhone 13', (SELECT brand_id FROM brand WHERE brand_name='Apple')),
  ('Galaxy S21', (SELECT brand_id FROM brand WHERE brand_name='Samsung')),
  ('Redmi Note 10', (SELECT brand_id FROM brand WHERE brand_name='Xiaomi'));

-- Customer phones (IMEI is unique)
INSERT INTO customer_phone (model_id, color, imei, customer_id)
VALUES
  ((SELECT model_id FROM phone_model WHERE model_name='iPhone 13'), 'Midnight', '356789012345678',
    (SELECT user_id FROM users WHERE phone='09123333333')),
  ((SELECT model_id FROM phone_model WHERE model_name='Galaxy S21'), 'Black', '351234567890123',
    (SELECT user_id FROM users WHERE phone='09124444444'));

-- Categories
INSERT INTO category (category_name, type) VALUES
  ('لوازم جانبی', 'public'),
  ('قطعات', 'private'),
  ('گوشی', 'public');

-- Products
INSERT INTO product (name, description, image, current_price, stock, category_id, is_active)
VALUES
  ('گلس محافظ آیفون', 'گلس محافظ شیشه‌ای مناسب آیفون', NULL, 200000, 20,
    (SELECT category_id FROM category WHERE category_name='لوازم جانبی'), TRUE),
  ('شارژر سامسونگ 25W', 'شارژر سریع ۲۵ وات سامسونگ', NULL, 450000, 10,
    (SELECT category_id FROM category WHERE category_name='لوازم جانبی'), TRUE),
  ('کابل USB-C', 'کابل USB-C یک متری', NULL, 150000, 30,
    (SELECT category_id FROM category WHERE category_name='لوازم جانبی'), TRUE),
  ('باتری آیفون 13 (اورجینال)', 'باتری اصلی آیفون ۱۳', NULL, 1500000, 5,
    (SELECT category_id FROM category WHERE category_name='قطعات'), TRUE),
  ('LCD Galaxy S21', 'صفحه نمایش اصلی Galaxy S21', NULL, 3500000, 3,
    (SELECT category_id FROM category WHERE category_name='قطعات'), TRUE);

-- Services
INSERT INTO service (service_name, description, current_price, is_active)
VALUES
  ('تعویض گلس', 'تعویض گلس و چسب‌کاری', 500000, TRUE),
  ('تعویض باتری', 'تعویض باتری با تست سلامت', 1200000, TRUE),
  ('تعویض LCD', 'تعویض کامل LCD و فریم', 2000000, TRUE);

-- Create a repair order (price_at_time is set by trigger)
INSERT INTO repair_order (customer_id, phone_id, service_id, status, created_by_user_id, notes)
VALUES (
  (SELECT user_id FROM users WHERE phone='09123333333'),
  (SELECT phone_id FROM customer_phone WHERE imei='356789012345678'),
  (SELECT service_id FROM service WHERE service_name='تعویض باتری'),
  'pending',
  (SELECT user_id FROM users WHERE phone='09121111111'),
  'مشتری اعلام کرد شارژدهی کم شده است.'
);

-- ------------------------------------------------------------
-- Sales demo
-- ------------------------------------------------------------

-- Sale #1 (with customer)
WITH s AS (
  INSERT INTO sale (customer_id, created_by_user_id, status)
  VALUES (
    (SELECT user_id FROM users WHERE phone='09123333333'),
    (SELECT user_id FROM users WHERE phone='09121111111'),
    'draft'
  )
  RETURNING sale_id
)
INSERT INTO sale_item (sale_id, product_id, quantity)
SELECT
  s.sale_id,
  p.product_id,
  2
FROM s
JOIN product p ON p.name = 'گلس محافظ آیفون';

-- Add another item
INSERT INTO sale_item (sale_id, product_id, quantity)
VALUES (
  (SELECT MAX(sale_id) FROM sale),
  (SELECT product_id FROM product WHERE name='کابل USB-C'),
  1
);

-- Finalize sale #1 (this deducts stock, updates inventory_history, etc.)
UPDATE sale
SET status = 'finalized'
WHERE sale_id = (SELECT MAX(sale_id) FROM sale);

-- Sale #2 (walk-in, no customer_id)
WITH s AS (
  INSERT INTO sale (customer_id, created_by_user_id, status)
  VALUES (
    NULL,
    (SELECT user_id FROM users WHERE phone='09122222222'),
    'draft'
  )
  RETURNING sale_id
)
INSERT INTO sale_item (sale_id, product_id, quantity)
SELECT
  s.sale_id,
  p.product_id,
  1
FROM s
JOIN product p ON p.name = 'شارژر سامسونگ 25W';

UPDATE sale
SET status = 'finalized'
WHERE sale_id = (SELECT MAX(sale_id) FROM sale);

-- ------------------------------------------------------------
-- Create some history rows (price change + manual stock adjustment)
-- ------------------------------------------------------------

-- Staff #1 updates product price (logs product_price_history)
UPDATE product
SET current_price = 470000,
    updated_by_user_id = (SELECT user_id FROM users WHERE phone='09121111111')
WHERE name = 'شارژر سامسونگ 25W';

-- Staff #1 adjusts stock (logs inventory_history)
UPDATE product
SET stock = stock + 5,
    updated_by_user_id = (SELECT user_id FROM users WHERE phone='09121111111')
WHERE name = 'LCD Galaxy S21';

-- Staff #2 updates service price (logs service_price_history)
UPDATE service
SET current_price = 550000,
    updated_by_user_id = (SELECT user_id FROM users WHERE phone='09122222222')
WHERE service_name = 'تعویض گلس';
