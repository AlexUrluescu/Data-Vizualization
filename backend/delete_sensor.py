import sys
from db import get_conn


def hard_delete_sensor(sensor_id: str):
    sensor_id = sensor_id.strip().upper()
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM sensors WHERE id=?", (sensor_id,)).fetchone()
        if not row:
            print(f"❌ Sensor '{sensor_id}' not found.")
            return
        print(f"Found: {dict(row)}")
        confirm = input(f"Permanently delete sensor '{sensor_id}'? (yes/no): ")
        if confirm.strip().lower() != "yes":
            print("Aborted.")
            return
        conn.execute("DELETE FROM sensors WHERE id=?", (sensor_id,))
        print(f"✓ Sensor '{sensor_id}' deleted.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sensor_id = input("Enter Sensor ID to delete: ")
    else:
        sensor_id = sys.argv[1]

    hard_delete_sensor(sensor_id)
