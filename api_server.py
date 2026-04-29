from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Dhanu%77",
        database="energy_management_sys"
    )

#http://localhost:5000/energy?machine_id=1&voltage=12&current=1.3&energy=10&relay_status=1&power=10&anomaly=1
@app.route('/energy', methods=['GET'])
def receive_energy():
    try:
        data = request.args
        print(data)

        machine_id = data.get("machine_id")
        voltage = data.get("voltage")
        current = data.get("current")
        power = data.get("power")
        energy = data.get("energy")
        relay_status = data.get("relay_status")
        anomaly_input = data.get("anomaly", "0").lower()
        anomaly_input = data.get("anomaly", "0").lower()
        if anomaly_input in ["normal", "0"]:
            anomaly = 0
        elif anomaly_input in ["abnormal", "1", "high_voltage", "low_voltage"]:
            anomaly = 1
        else:
            anomaly = 0

        if not machine_id:
            return jsonify({"error": "machine_id is required"}), 400

        db = get_db_connection()
        cursor = db.cursor()

        query = """
        INSERT INTO energy_data
        (machine_id, voltage, current, power, energy, relay_status, anomaly)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """
        values = (
    int(machine_id),
    float(voltage),
    float(current),
    float(power),
    float(energy),
    int(relay_status),
    int(anomaly)
)

        cursor.execute(query, values)
        db.commit()

        cursor.close()
        db.close()

        return jsonify({"message": "Data stored successfully"})

    except Exception as e:
        print("ERROR IN /energy:", e)   # 👈 MUST ADD
    return jsonify({"error": str(e)}), 500


@app.route('/energy/all', methods=['GET'])
def get_all_data():
    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("SELECT * FROM energy_data")
        rows = cursor.fetchall()

        data = []
        for r in rows:
            data.append({
                "id": r[0],
                "machine_id": r[1],
                "voltage": r[2],
                "current": r[3],
                "power": r[4],
                "energy": r[5],
                "relay_status": r[6],
                "anomaly": r[7],
                "timestamp": r[8]
            })

        cursor.close()
        db.close()

        return jsonify(data)

    except Exception as e:
      print("ERROR IN /energy:", e)   # 👈 ADD THIS
      return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)