from psycopg2.extras import execute_batch

from drinkit_stock_transfers.logger import get_logger

logger = get_logger(__name__)


class TransferRepository:
    def __init__(self, conn):
        self.conn = conn

    def save_transfers(self, transfers):
        if not transfers:
            logger.info("No transfers received")
            return

        def to_row(item):
            return (
                item["transferOrderId"],
                item["transferOrderNumber"],
                item["originUnitId"],
                item["destinationUnitId"],
                item["stockItemId"],
                item["stockItemName"],
                item["orderedQuantity"],
                item["shippedQuantity"],
                item["receivedQuantity"],
                item["measurementUnit"],
                item["pricePerUnitWithVat"],
                item["sumPriceWithVat"],
                item.get("expectedAtLocal"),
                item.get("shippedAtLocal"),
                item.get("receivedAtLocal"),
                item["status"],
            )

        seen = set()
        rows = []
        for item in transfers:
            if item.get("shippedQuantity") != 0:
                continue
            key = (item.get("transferOrderId"), item.get("stockItemId"))
            if key in seen:
                continue
            seen.add(key)
            try:
                rows.append(to_row(item))
            except KeyError as error:
                logger.warning(f"Skipping invalid item: missing {error}")
                continue
        if not rows:
            logger.info("No rows to insert")
            return
        sql = """
        INSERT INTO transfer_items (
            transfer_order_id,
            transfer_order_number,
            origin_unit_id,
            destination_unit_id,
            stock_item_id,
            stock_item_name,
            ordered_quantity,
            shipped_quantity,
            received_quantity,
            measurement_unit,
            price_per_unit_with_vat,
            sum_price_with_vat,
            expected_at_local,
            shipped_at_local,
            received_at_local,
            status
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (transfer_order_id, stock_item_id)
        DO UPDATE SET
            ordered_quantity = EXCLUDED.ordered_quantity,
            shipped_quantity = EXCLUDED.shipped_quantity,
            received_quantity = EXCLUDED.received_quantity,
            status = EXCLUDED.status,
            shipped_at_local = EXCLUDED.shipped_at_local,
            received_at_local = EXCLUDED.received_at_local,
            updated_at = NOW()
        """

        BATCH_SIZE = 1000
        try:
            with self.conn:
                with self.conn.cursor() as cur:
                    for i in range(0, len(rows), BATCH_SIZE):
                        batch = rows[i : i + BATCH_SIZE]
                        execute_batch(cur, sql, batch)
            logger.info(
                "transfers_saved",
                extra={
                    "count": len(rows),
                    "batches": (len(rows) // BATCH_SIZE) + 1,
                },
            )
        except Exception as error:
            logger.error(f"DB error: {error}")
            raise

    def fetch_zero_shipped(self, date):
        """Fetch positions where shipped quantity equals 0."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    u.unit_name AS точка,
                    u_dest.unit_name AS получатель,
                    ti.transfer_order_number AS накладная,
                    ti.stock_item_name AS товар,
                    ti.ordered_quantity AS заказано,
                    ti.shipped_quantity AS отгружено,
                    ti.expected_at_local AS ожидаемая_дата
                FROM transfer_items ti
                JOIN units u ON u.unit_uuid = ti.origin_unit_id
                JOIN units u_dest ON u_dest.unit_uuid = ti.destination_unit_id
                WHERE ti.shipped_quantity = 0
                  AND ti.ordered_quantity > 0
                  AND DATE(ti.expected_at_local) = %s
                ORDER BY u_dest.unit_name, ti.expected_at_local DESC
            """,
                (date,),
            )
            return cur.fetchall()

    def has_zero_shipped_for_date(self, date):
        """Check if  in DB  shipped_quantity=0 today."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT EXISTS(
                    SELECT 1 FROM transfer_items
                    WHERE shipped_quantity = 0
                      AND ordered_quantity > 0
                      AND DATE(expected_at_local) = %s
                )
            """,
                (date,),
            )
            return cur.fetchone()[0]
