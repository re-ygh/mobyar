-- 03_views.sql
-- ------------------------------------------------------------
-- Mobyar (موبیار) - Views for managerial reports
-- ------------------------------------------------------------

-- 1) Daily sales summary (only finalized sales)
CREATE OR REPLACE VIEW v_daily_sales AS
SELECT
  (sale_date AT TIME ZONE 'UTC')::date AS sale_day,
  COUNT(*) AS sales_count,
  COALESCE(SUM(total_price), 0) AS revenue
FROM sale
WHERE status = 'finalized'
GROUP BY (sale_date AT TIME ZONE 'UTC')::date
ORDER BY sale_day DESC;

-- 2) Low stock products (threshold = 5 for this view)
CREATE OR REPLACE VIEW v_low_stock AS
SELECT
  p.product_id,
  p.name,
  p.stock,
  p.current_price,
  c.category_name
FROM product p
JOIN category c ON c.category_id = p.category_id
WHERE p.is_active = TRUE
  AND p.stock <= 5
ORDER BY p.stock ASC, p.product_id ASC;

-- 3) Open repair orders (not delivered/cancelled)
CREATE OR REPLACE VIEW v_open_repairs AS
SELECT
  r.repair_id,
  r.created_at,
  r.updated_at,
  r.status,
  r.price_at_time,
  u.name AS customer_name,
  u.phone AS customer_phone,
  s.service_name,
  cp.imei
FROM repair_order r
JOIN users u ON u.user_id = r.customer_id
JOIN service s ON s.service_id = r.service_id
JOIN customer_phone cp ON cp.phone_id = r.phone_id
WHERE r.status IN ('pending', 'in_progress', 'ready')
ORDER BY r.created_at DESC;

-- 4) Top selling products in last 30 days (by quantity)
CREATE OR REPLACE VIEW v_top_products_30d AS
SELECT
  p.product_id,
  p.name,
  SUM(si.quantity) AS total_qty,
  SUM(si.quantity * si.price_at_time) AS total_amount
FROM sale_item si
JOIN sale s ON s.sale_id = si.sale_id
JOIN product p ON p.product_id = si.product_id
WHERE s.status = 'finalized'
  AND s.sale_date >= now() - interval '30 days'
GROUP BY p.product_id, p.name
ORDER BY total_qty DESC
LIMIT 10;

-- 5) Service revenue in last 30 days (delivered repairs)
CREATE OR REPLACE VIEW v_service_revenue_30d AS
SELECT
  srv.service_id,
  srv.service_name,
  COUNT(*) AS orders_count,
  SUM(r.price_at_time) AS revenue
FROM repair_order r
JOIN service srv ON srv.service_id = r.service_id
WHERE r.status = 'delivered'
  AND r.created_at >= now() - interval '30 days'
GROUP BY srv.service_id, srv.service_name
ORDER BY revenue DESC;
