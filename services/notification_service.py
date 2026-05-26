from datetime import datetime


def _format_time(dt):
    if not dt:
        return ""
    return dt.strftime("%b %d, %Y %I:%M %p")


def get_low_stock_alerts(db, threshold=15, limit=10):
    cur = db.connection.cursor()
    cur.execute(
        """SELECT i.id,
                          i.name,
                          i.quantity,
                          COALESCE(i.date_updated, i.date_created) AS event_time
                   FROM inventory_items i
                   JOIN categories c ON i.category_id = c.id
                   JOIN subcategories s ON i.subcategory_id = s.id
                   WHERE i.quantity <= %s
                   ORDER BY i.quantity ASC, event_time DESC
                   LIMIT %s""",
        (threshold, limit),
    )
    rows = cur.fetchall()
    notifications = []
    for row in rows:
        created = row.get("event_time")
        notifications.append(
            {
                "id": f"low-{row['id']}",
                "type": "low_stock",
                "title": "Low Stock",
                "message": f"{row['quantity']} {row['name']} remaining",
                "time": _format_time(created),
                "timestamp": created.timestamp() if isinstance(created, datetime) else 0,
            }
        )
    return notifications


def get_pending_approval_notifications(db, limit=10):
    cur = db.connection.cursor()
    cur.execute(
        """SELECT r.id,
                          r.action_type,
                          r.created_at,
                          COALESCE(i.name, '(new item)') AS item_name,
                          COALESCE(u.full_name, u.email) AS requester_name
                   FROM inventory_change_requests r
                   JOIN users u ON r.requested_by = u.id
                   LEFT JOIN inventory_items i ON r.item_id = i.id
                   WHERE r.status = 'pending'
                   ORDER BY r.created_at DESC
                   LIMIT %s""",
        (limit,),
    )
    rows = cur.fetchall()
    notifications = []
    for row in rows:
        action = row["action_type"].title()
        item_name = row["item_name"] or "(new item)"
        created = row.get("created_at")
        notifications.append(
            {
                "id": f"approval-{row['id']}",
                "type": "approval",
                "title": "Approval Request",
                "message": f"{action} request for {item_name} by {row['requester_name']}",
                "time": _format_time(created),
                "timestamp": created.timestamp() if isinstance(created, datetime) else 0,
            }
        )
    return notifications


def get_notifications(db, role):
    notifications = get_low_stock_alerts(db)
    if role == "admin":
        notifications.extend(get_pending_approval_notifications(db))
    notifications.sort(key=lambda item: item.get("timestamp", 0), reverse=True)
    for item in notifications:
        item.pop("timestamp", None)
    return notifications
