-- 02_triggers.sql
-- ------------------------------------------------------------
-- Mobyar (موبیار) - Triggers & Functions (PostgreSQL)
--
-- What we enforce in DB:
-- 1) Price history for product/service (automatic)
-- 2) Inventory history for product stock changes (automatic)
-- 3) Prevent negative stock (DB-level guarantee)
-- 4) Sale workflow:
--      - Items can be modified only when sale is draft
--      - SaleItem.price_at_time is copied from product.current_price at insert
--      - Sale.total_price is auto-synced from SaleItems
--      - Finalizing a sale deducts stock atomically & prevents negative stock
-- 5) Repair workflow:
--      - RepairOrder.price_at_time is copied from service.current_price at insert
--      - Validate that selected phone belongs to the customer
--      - Restrict status transitions after delivered/cancelled
-- ------------------------------------------------------------

-- Updated-at helper (generic)
CREATE OR REPLACE FUNCTION tg_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ------------------------------------------------------------
-- Product: price history + stock history
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION tg_log_product_price_change()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.current_price IS DISTINCT FROM OLD.current_price THEN
    INSERT INTO product_price_history(product_id, old_price, new_price, changed_by, change_date)
    VALUES (OLD.product_id, OLD.current_price, NEW.current_price, NEW.updated_by_user_id, now());
  END IF;

  -- Always refresh updated_at
  NEW.updated_at := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_product_price_history
BEFORE UPDATE OF current_price ON product
FOR EACH ROW
EXECUTE FUNCTION tg_log_product_price_change();

CREATE OR REPLACE FUNCTION tg_log_product_stock_change()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.stock < 0 THEN
    RAISE EXCEPTION 'Stock cannot be negative (product_id=%)', OLD.product_id;
  END IF;

  IF NEW.stock IS DISTINCT FROM OLD.stock THEN
    INSERT INTO inventory_history(product_id, old_stock, new_stock, changed_by, update_date)
    VALUES (OLD.product_id, OLD.stock, NEW.stock, NEW.updated_by_user_id, now());
  END IF;

  NEW.updated_at := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_product_inventory_history
BEFORE UPDATE OF stock ON product
FOR EACH ROW
EXECUTE FUNCTION tg_log_product_stock_change();

-- ------------------------------------------------------------
-- Service: price history
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION tg_log_service_price_change()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.current_price IS DISTINCT FROM OLD.current_price THEN
    INSERT INTO service_price_history(service_id, old_price, new_price, changed_by, change_date)
    VALUES (OLD.service_id, OLD.current_price, NEW.current_price, NEW.updated_by_user_id, now());
  END IF;

  NEW.updated_at := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_service_price_history
BEFORE UPDATE OF current_price ON service
FOR EACH ROW
EXECUTE FUNCTION tg_log_service_price_change();

-- Keep updated_at on "any update" for key tables
CREATE TRIGGER tr_users_set_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION tg_set_updated_at();

CREATE TRIGGER tr_sale_set_updated_at
BEFORE UPDATE ON sale
FOR EACH ROW
EXECUTE FUNCTION tg_set_updated_at();

-- ------------------------------------------------------------
-- Sales: total sync + price_at_time + finalize workflow
-- ------------------------------------------------------------

-- Recalculate sale.total_price from sale_item rows.
CREATE OR REPLACE FUNCTION recalc_sale_total(p_sale_id BIGINT)
RETURNS VOID AS $$
DECLARE
  v_total NUMERIC(12,2);
BEGIN
  SELECT COALESCE(SUM(quantity * price_at_time), 0)
    INTO v_total
  FROM sale_item
  WHERE sale_id = p_sale_id;

  UPDATE sale
     SET total_price = v_total,
         updated_at  = now()
   WHERE sale_id = p_sale_id;
END;
$$ LANGUAGE plpgsql;

-- Validate draft-only modifications and set price_at_time on insert.
CREATE OR REPLACE FUNCTION tg_sale_item_before_write()
RETURNS TRIGGER AS $$
DECLARE
  v_sale_status  TEXT;
  v_stock        INT;
  v_price        NUMERIC(12,2);
  v_sale_id      BIGINT;
BEGIN
  v_sale_id := COALESCE(NEW.sale_id, OLD.sale_id);

  -- Lock the sale row so concurrent writes are consistent.
  SELECT status INTO v_sale_status
  FROM sale
  WHERE sale_id = v_sale_id
  FOR UPDATE;

  IF v_sale_status IS NULL THEN
    RAISE EXCEPTION 'Sale not found (sale_id=%)', v_sale_id;
  END IF;

  IF v_sale_status <> 'draft' THEN
    RAISE EXCEPTION 'Cannot modify items when sale is % (sale_id=%)', v_sale_status, v_sale_id;
  END IF;

  IF TG_OP = 'INSERT' THEN
    SELECT stock, current_price INTO v_stock, v_price
    FROM product
    WHERE product_id = NEW.product_id
    FOR UPDATE;

    IF v_stock IS NULL THEN
      RAISE EXCEPTION 'Product not found (product_id=%)', NEW.product_id;
    END IF;

    IF NEW.quantity <= 0 THEN
      RAISE EXCEPTION 'Quantity must be > 0';
    END IF;

    IF NEW.quantity > v_stock THEN
      RAISE EXCEPTION 'Insufficient stock. Available=%, requested=% (product_id=%)', v_stock, NEW.quantity, NEW.product_id;
    END IF;

    -- Copy snapshot of product price
    NEW.price_at_time := v_price;

    RETURN NEW;
  ELSIF TG_OP = 'UPDATE' THEN
    -- By default, keep old snapshot price (do not allow manual price edits)
    NEW.price_at_time := OLD.price_at_time;

    IF NEW.quantity <= 0 THEN
      RAISE EXCEPTION 'Quantity must be > 0';
    END IF;

    IF NEW.product_id IS DISTINCT FROM OLD.product_id THEN
      -- If product changes, set price snapshot from the new product
      SELECT stock, current_price INTO v_stock, v_price
      FROM product
      WHERE product_id = NEW.product_id
      FOR UPDATE;

      IF v_stock IS NULL THEN
        RAISE EXCEPTION 'Product not found (product_id=%)', NEW.product_id;
      END IF;

      IF NEW.quantity > v_stock THEN
        RAISE EXCEPTION 'Insufficient stock. Available=%, requested=% (product_id=%)', v_stock, NEW.quantity, NEW.product_id;
      END IF;

      NEW.price_at_time := v_price;
    ELSE
      -- Same product, just validate stock
      SELECT stock INTO v_stock
      FROM product
      WHERE product_id = NEW.product_id
      FOR UPDATE;

      IF NEW.quantity > v_stock THEN
        RAISE EXCEPTION 'Insufficient stock. Available=%, requested=% (product_id=%)', v_stock, NEW.quantity, NEW.product_id;
      END IF;
    END IF;

    RETURN NEW;
  ELSIF TG_OP = 'DELETE' THEN
    RETURN OLD;
  END IF;

  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_sale_item_before_insert
BEFORE INSERT ON sale_item
FOR EACH ROW
EXECUTE FUNCTION tg_sale_item_before_write();

CREATE TRIGGER tr_sale_item_before_update
BEFORE UPDATE ON sale_item
FOR EACH ROW
EXECUTE FUNCTION tg_sale_item_before_write();

CREATE OR REPLACE FUNCTION tg_sale_item_before_delete()
RETURNS TRIGGER AS $$
DECLARE
  v_sale_status TEXT;
BEGIN
  SELECT status INTO v_sale_status
  FROM sale
  WHERE sale_id = OLD.sale_id
  FOR UPDATE;

  IF v_sale_status <> 'draft' THEN
    RAISE EXCEPTION 'Cannot delete items when sale is % (sale_id=%)', v_sale_status, OLD.sale_id;
  END IF;

  RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_sale_item_before_delete
BEFORE DELETE ON sale_item
FOR EACH ROW
EXECUTE FUNCTION tg_sale_item_before_delete();

-- After any item change, resync total
CREATE OR REPLACE FUNCTION tg_sale_item_after_change()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM recalc_sale_total(COALESCE(NEW.sale_id, OLD.sale_id));
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_sale_item_after_insert
AFTER INSERT ON sale_item
FOR EACH ROW
EXECUTE FUNCTION tg_sale_item_after_change();

CREATE TRIGGER tr_sale_item_after_update
AFTER UPDATE ON sale_item
FOR EACH ROW
EXECUTE FUNCTION tg_sale_item_after_change();

CREATE TRIGGER tr_sale_item_after_delete
AFTER DELETE ON sale_item
FOR EACH ROW
EXECUTE FUNCTION tg_sale_item_after_change();

-- Finalizing a sale deducts stock atomically.
CREATE OR REPLACE FUNCTION tg_sale_before_status_update()
RETURNS TRIGGER AS $$
DECLARE
  rec RECORD;
  v_total NUMERIC(12,2);
BEGIN
  -- Only react when status changes
  IF NEW.status IS DISTINCT FROM OLD.status THEN

    -- Prevent changing finalized sales
    IF OLD.status = 'finalized' THEN
      RAISE EXCEPTION 'Finalized sale cannot change (sale_id=%)', OLD.sale_id;
    END IF;

    -- Finalize path
    IF OLD.status = 'draft' AND NEW.status = 'finalized' THEN

      -- Must have at least one item
      IF NOT EXISTS (SELECT 1 FROM sale_item WHERE sale_id = OLD.sale_id) THEN
        RAISE EXCEPTION 'Cannot finalize an empty sale (sale_id=%)', OLD.sale_id;
      END IF;

      -- Lock & validate stock for each item
      FOR rec IN
        SELECT product_id, quantity
        FROM sale_item
        WHERE sale_id = OLD.sale_id
      LOOP
        -- Lock product row
        PERFORM 1 FROM product WHERE product_id = rec.product_id FOR UPDATE;

        IF (SELECT stock FROM product WHERE product_id = rec.product_id) < rec.quantity THEN
          RAISE EXCEPTION 'Insufficient stock for product_id=% (sale_id=%)', rec.product_id, OLD.sale_id;
        END IF;
      END LOOP;

      -- Recalculate total as a final safety (in case of manual edits)
      SELECT COALESCE(SUM(quantity * price_at_time), 0) INTO v_total
      FROM sale_item
      WHERE sale_id = OLD.sale_id;

      NEW.total_price := v_total;

      -- Deduct stock in one statement
      UPDATE product p
         SET stock = p.stock - si.quantity,
             updated_by_user_id = OLD.created_by_user_id,
             updated_at = now()
        FROM sale_item si
       WHERE si.sale_id = OLD.sale_id
         AND p.product_id = si.product_id;

      NEW.finalized_at := now();
      NEW.updated_at := now();
      NEW.sale_date := COALESCE(NEW.sale_date, now());

      RETURN NEW;
    END IF;

    -- Allow void only from draft
    IF OLD.status = 'draft' AND NEW.status = 'void' THEN
      NEW.updated_at := now();
      RETURN NEW;
    END IF;

  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_sale_before_status_update
BEFORE UPDATE OF status ON sale
FOR EACH ROW
EXECUTE FUNCTION tg_sale_before_status_update();

-- ------------------------------------------------------------
-- Repairs: price_at_time snapshot + validation + status rules
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION tg_repair_before_insert()
RETURNS TRIGGER AS $$
DECLARE
  v_price NUMERIC(12,2);
BEGIN
  -- Validate the phone belongs to the same customer
  IF NOT EXISTS (
    SELECT 1
    FROM customer_phone cp
    WHERE cp.phone_id = NEW.phone_id
      AND cp.customer_id = NEW.customer_id
  ) THEN
    RAISE EXCEPTION 'Selected phone does not belong to the customer (phone_id=% customer_id=%)', NEW.phone_id, NEW.customer_id;
  END IF;

  -- Copy service price snapshot
  SELECT current_price INTO v_price
  FROM service
  WHERE service_id = NEW.service_id;

  IF v_price IS NULL THEN
    RAISE EXCEPTION 'Service not found (service_id=%)', NEW.service_id;
  END IF;

  NEW.price_at_time := v_price;

  IF NEW.status IS NULL THEN
    NEW.status := 'pending';
  END IF;

  NEW.created_at := COALESCE(NEW.created_at, now());
  NEW.updated_at := now();

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_repair_before_insert
BEFORE INSERT ON repair_order
FOR EACH ROW
EXECUTE FUNCTION tg_repair_before_insert();

CREATE OR REPLACE FUNCTION tg_repair_before_update()
RETURNS TRIGGER AS $$
BEGIN
  -- Immutable fields after creation
  IF NEW.customer_id IS DISTINCT FROM OLD.customer_id
     OR NEW.phone_id IS DISTINCT FROM OLD.phone_id
     OR NEW.service_id IS DISTINCT FROM OLD.service_id THEN
    RAISE EXCEPTION 'Cannot change customer/phone/service of an existing repair_order (repair_id=%)', OLD.repair_id;
  END IF;

  -- price_at_time must not change
  NEW.price_at_time := OLD.price_at_time;

  -- After delivered/cancelled, status cannot change
  IF OLD.status IN ('delivered', 'cancelled')
     AND NEW.status IS DISTINCT FROM OLD.status THEN
    RAISE EXCEPTION 'Cannot change status after it is % (repair_id=%)', OLD.status, OLD.repair_id;
  END IF;

  NEW.updated_at := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_repair_before_update
BEFORE UPDATE ON repair_order
FOR EACH ROW
EXECUTE FUNCTION tg_repair_before_update();
