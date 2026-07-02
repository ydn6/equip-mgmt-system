"""工业设备台账管理系统"""
from flask import Flask, request, jsonify, render_template
import psycopg2
import psycopg2.extras

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


def get_db():
    """返回 openGauss 数据库连接"""
    return psycopg2.connect(
        database="postgres",
        user="ryan",
        password="ryan@123",
        host="192.168.31.160",
        port=5432
    )


# ==================== 车间 API ====================

@app.route('/api/workshops')
def api_workshops():
    """返回所有车间列表（用于下拉框）"""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT workshop_id, workshop_name, location FROM workshop ORDER BY workshop_id")
        rows = cur.fetchall()
        workshops = [
            {"id": r[0], "name": r[1], "location": r[2]}
            for r in rows
        ]
        return jsonify(workshops)
    finally:
        conn.close()


# ==================== 设备 API ====================

@app.route('/api/equipment')
def api_equipment():
    """模糊查询设备（按编号、名称、型号），返回列表含车间名称"""
    q = request.args.get('q', '').strip()
    conn = get_db()
    try:
        cur = conn.cursor()
        if q:
            cur.execute("""
                SELECT e.equip_id, e.equip_name, e.model, e.manufacture_date,
                       e.purchase_price, e.workshop_id, e.responsible_person, e.status,
                       w.workshop_name
                FROM equipment e
                LEFT JOIN workshop w ON e.workshop_id = w.workshop_id
                WHERE e.equip_id ILIKE %(q)s
                   OR e.equip_name ILIKE %(q)s
                   OR e.model ILIKE %(q)s
                ORDER BY e.equip_id
            """, {'q': f'%{q}%'})
        else:
            cur.execute("""
                SELECT e.equip_id, e.equip_name, e.model, e.manufacture_date,
                       e.purchase_price, e.workshop_id, e.responsible_person, e.status,
                       w.workshop_name
                FROM equipment e
                LEFT JOIN workshop w ON e.workshop_id = w.workshop_id
                ORDER BY e.equip_id
            """)
        rows = cur.fetchall()
        result = [{
            "equip_id": r[0],
            "equip_name": r[1],
            "model": r[2],
            "manufacture_date": r[3].isoformat() if r[3] else None,
            "purchase_price": float(r[4]) if r[4] else None,
            "workshop_id": r[5],
            "responsible_person": r[6],
            "status": r[7],
            "workshop_name": r[8]
        } for r in rows]
        return jsonify(result)
    finally:
        conn.close()


@app.route('/api/equipment', methods=['POST'])
def api_equipment_create():
    """新增设备"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "请求体为空"}), 400

    required = ['equip_id', 'equip_name', 'model', 'manufacture_date',
                'purchase_price', 'workshop_id', 'responsible_person', 'status']
    for field in required:
        if field not in data:
            return jsonify({"error": f"缺少字段: {field}"}), 400

    # 应用层校验：价格非负
    if data['purchase_price'] < 0:
        return jsonify({"error": "采购价格不能为负数"}), 400

    # 应用层校验：车间存在性
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM workshop WHERE workshop_id = %s", (data['workshop_id'],))
        if not cur.fetchone():
            return jsonify({"error": f"车间 {data['workshop_id']} 不存在"}), 400

        cur.execute("""
            INSERT INTO equipment (equip_id, equip_name, model, manufacture_date,
                                   purchase_price, workshop_id, responsible_person, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['equip_id'], data['equip_name'], data['model'],
            data['manufacture_date'], data['purchase_price'],
            data['workshop_id'], data['responsible_person'], data['status']
        ))
        conn.commit()
        return jsonify({"message": "设备添加成功"}), 201
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return jsonify({"error": f"设备编号 {data['equip_id']} 已存在"}), 409
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route('/api/equipment/<equip_id>', methods=['PUT'])
def api_equipment_update(equip_id):
    """更新设备负责人和状态"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "请求体为空"}), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM equipment WHERE equip_id = %s", (equip_id,))
        if not cur.fetchone():
            return jsonify({"error": f"设备 {equip_id} 不存在"}), 404

        cur.execute("""
            UPDATE equipment
            SET responsible_person = %s, status = %s
            WHERE equip_id = %s
        """, (data.get('responsible_person', ''),
              data.get('status', '在用'), equip_id))
        conn.commit()
        return jsonify({"message": "设备更新成功"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route('/api/equipment/<equip_id>', methods=['DELETE'])
def api_equipment_delete(equip_id):
    """删除设备：仅当状态为'未使用'且无维修记录时允许"""
    conn = get_db()
    try:
        cur = conn.cursor()

        # 检查设备是否存在
        cur.execute("SELECT status FROM equipment WHERE equip_id = %s", (equip_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": f"设备 {equip_id} 不存在"}), 404

        status = row[0]
        if status != '未使用':
            return jsonify({"error": f"只能删除'未使用'状态的设备，当前状态: {status}"}), 400

        # 检查是否有维修记录
        cur.execute("SELECT COUNT(*) FROM maintenance WHERE equip_id = %s", (equip_id,))
        count = cur.fetchone()[0]
        if count > 0:
            return jsonify({"error": f"该设备有 {count} 条维修记录，不允许删除"}), 400

        cur.execute("DELETE FROM equipment WHERE equip_id = %s", (equip_id,))
        conn.commit()
        return jsonify({"message": f"设备 {equip_id} 已删除"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# ==================== 维修记录 API ====================

@app.route('/api/maintenance/<equip_id>')
def api_maintenance_get(equip_id):
    """返回某设备的所有维修记录，按时间倒序"""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT maintenance_id, equip_id, maintenance_time, fault_desc, repair_cost
            FROM maintenance
            WHERE equip_id = %s
            ORDER BY maintenance_time DESC
        """, (equip_id,))
        rows = cur.fetchall()
        result = [{
            "maintenance_id": r[0],
            "equip_id": r[1],
            "maintenance_time": r[2].isoformat() if r[2] else None,
            "fault_desc": r[3],
            "repair_cost": float(r[4]) if r[4] else None
        } for r in rows]
        return jsonify(result)
    finally:
        conn.close()


@app.route('/api/maintenance', methods=['POST'])
def api_maintenance_create():
    """新增维修记录：应用层校验设备存在性和费用非负"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "请求体为空"}), 400

    required = ['equip_id', 'maintenance_time', 'fault_desc', 'repair_cost']
    for field in required:
        if field not in data:
            return jsonify({"error": f"缺少字段: {field}"}), 400

    # 应用层校验：费用非负
    if data['repair_cost'] < 0:
        return jsonify({"error": "维修费用不能为负数"}), 400

    conn = get_db()
    try:
        cur = conn.cursor()

        # 应用层校验：设备存在
        cur.execute("SELECT 1 FROM equipment WHERE equip_id = %s", (data['equip_id'],))
        if not cur.fetchone():
            return jsonify({"error": f"设备 {data['equip_id']} 不存在"}), 400

        cur.execute("""
            INSERT INTO maintenance (equip_id, maintenance_time, fault_desc, repair_cost)
            VALUES (%s, %s, %s, %s)
        """, (data['equip_id'], data['maintenance_time'],
              data['fault_desc'], data['repair_cost']))
        conn.commit()
        return jsonify({"message": "维修记录添加成功"}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# ==================== 维修多条件筛选 API ====================

@app.route('/api/maintenance/search')
def api_maintenance_search():
    """多条件筛选维修记录（列存储仅读取所需列，效率高于行存储）
      可选参数: equip_id, date_from(YYYY-MM), date_to(YYYY-MM), fault_desc"""
    equip_id = request.args.get('equip_id', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    fault_desc = request.args.get('fault_desc', '').strip()

    conn = get_db()
    try:
        cur = conn.cursor()
        # 列存储：仅 SELECT 所需列 maintenance_time, fault_desc, repair_cost, equip_id
        sql = """SELECT equip_id, maintenance_time, fault_desc, repair_cost
                 FROM maintenance WHERE 1=1"""
        params = []

        if equip_id:
            sql += " AND equip_id = %s"
            params.append(equip_id)
        if date_from:
            sql += " AND maintenance_time >= %s"
            params.append(date_from + '-01 00:00:00')
        if date_to:
            sql += " AND maintenance_time < %s"
            # date_to 需要取该月最后一天之后
            import calendar
            y, m = map(int, date_to.split('-'))
            last_day = calendar.monthrange(y, m)[1]
            params.append(f'{date_to}-{last_day:02d} 23:59:59')
        if fault_desc:
            sql += " AND fault_desc ILIKE %s"
            params.append(f'%{fault_desc}%')

        sql += " ORDER BY maintenance_time DESC LIMIT 500"
        cur.execute(sql, params)
        rows = cur.fetchall()
        result = [{
            "equip_id": r[0],
            "maintenance_time": r[1].isoformat() if r[1] else None,
            "fault_desc": r[2],
            "repair_cost": float(r[3]) if r[3] else None
        } for r in rows]
        return jsonify(result)
    finally:
        conn.close()


# ==================== 设备批量更新 API ====================

@app.route('/api/equipment/batch', methods=['PUT'])
def api_equipment_batch_update():
    """批量更新设备负责人和状态"""
    data = request.get_json()
    if not data or 'ids' not in data or 'updates' not in data:
        return jsonify({"error": "请提供 ids 和 updates 字段"}), 400

    ids = data['ids']
    updates = data['updates']
    if not ids:
        return jsonify({"error": "ids 不能为空"}), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        set_clauses = []
        params = []
        if 'responsible_person' in updates:
            set_clauses.append("responsible_person = %s")
            params.append(updates['responsible_person'])
        if 'status' in updates:
            set_clauses.append("status = %s")
            params.append(updates['status'])
        if not set_clauses:
            return jsonify({"error": "没有要更新的字段"}), 400

        placeholders = ','.join(['%s'] * len(ids))
        sql = f"UPDATE equipment SET {', '.join(set_clauses)} WHERE equip_id IN ({placeholders})"
        cur.execute(sql, params + ids)
        conn.commit()
        return jsonify({"message": f"已批量更新 {cur.rowcount} 台设备"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# ==================== DB4AI 时序预测 API ====================

@app.route('/api/stats/predict')
def api_stats_predict():
    """基于近6个月维修记录，预测下月故障频次
       优先使用 openGauss DB4AI.PREDICT_TIME_SERIES，
       若未安装则使用 Python 加权移动平均作为回退。"""
    equip_id = request.args.get('equip_id', '').strip()
    if not equip_id:
        return jsonify({"error": "请提供 equip_id 参数"}), 400

    conn = get_db()
    try:
        cur = conn.cursor()

        # 近 6 个月按月汇总
        cur.execute("""
            SELECT TO_CHAR(maintenance_time, 'YYYY-MM') AS month,
                   COUNT(*) AS cnt
            FROM maintenance
            WHERE equip_id = %s
              AND maintenance_time >= NOW() - INTERVAL '6 months'
            GROUP BY TO_CHAR(maintenance_time, 'YYYY-MM')
            ORDER BY month
        """, (equip_id,))
        rows = cur.fetchall()

        history = [{"month": r[0], "count": r[1]} for r in rows]
        values = [r[1] for r in rows]

        if len(values) < 2:
            return jsonify({
                "equip_id": equip_id,
                "history": history,
                "prediction": None,
                "method": "insufficient_data",
                "message": f"历史数据不足（需要≥2个月），当前仅 {len(values)} 个月"
            })

        # 尝试 DB4AI 时序预测
        try:
            cur.execute("""
                SELECT db4ai.predict_time_series(
                    %s,           -- equip_id
                    %s,           -- last N months
                    'maintenance',
                    'maintenance_time',
                    'fault_desc'
                )
            """, (equip_id, 6))
            pred_result = cur.fetchone()
            if pred_result and pred_result[0] is not None:
                predicted = round(float(pred_result[0]), 1)
                return jsonify({
                    "equip_id": equip_id,
                    "history": history,
                    "prediction": [{"month": "下月预测", "count": predicted}],
                    "method": "DB4AI.PREDICT_TIME_SERIES"
                })
        except Exception:
            conn.rollback()
            # DB4AI 不可用，回退到 Python 计算

        # === Python 加权移动平均回退 ===
        n = len(values)
        # 权重：越近的月份权重越大
        weights = [0.05, 0.10, 0.15, 0.20, 0.22, 0.28][-n:]
        # 归一化
        w_sum = sum(weights)
        weights = [w / w_sum for w in weights]

        # 趋势因子（最近两期变化率）
        if n >= 2 and values[-2] > 0:
            trend = (values[-1] - values[-2]) / values[-2]
        else:
            trend = 0

        # 加权移动平均 × 趋势调整
        wma = sum(v * w for v, w in zip(values, weights))
        predicted = round(max(0, wma * (1 + 0.3 * trend)), 1)

        # 计算置信区间 (±1 sigma)
        mean_v = sum(values) / n
        variance = sum((v - mean_v) ** 2 for v in values) / max(1, n - 1)
        std_dev = variance ** 0.5

        return jsonify({
            "equip_id": equip_id,
            "history": history,
            "prediction": [{
                "month": "下月预测",
                "count": predicted,
                "range_low": round(max(0, predicted - std_dev), 1),
                "range_high": round(predicted + std_dev, 1)
            }],
            "method": "weighted_moving_average(回退)",
            "weights_used": [round(w, 3) for w in weights],
            "trend_factor": round(trend, 3)
        })
    finally:
        conn.close()


# ==================== 统计 API ====================

@app.route('/api/stats/workshop')
def api_stats_workshop():
    """车间设备统计：设备总数、在用数、维修次数"""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                w.workshop_name,
                COUNT(DISTINCT e.equip_id) AS total_devices,
                COUNT(DISTINCT CASE WHEN e.status = '在用' THEN e.equip_id END) AS active_devices,
                COUNT(DISTINCT m.maintenance_id) AS total_repairs
            FROM workshop w
            LEFT JOIN equipment e ON w.workshop_id = e.workshop_id
            LEFT JOIN maintenance m ON e.equip_id = m.equip_id
            GROUP BY w.workshop_id, w.workshop_name
            ORDER BY w.workshop_id
        """)
        rows = cur.fetchall()
        result = [{
            "workshop_name": r[0],
            "total_devices": r[1],
            "active_devices": r[2],
            "total_repairs": r[3]
        } for r in rows]
        return jsonify(result)
    finally:
        conn.close()


@app.route('/api/stats/trend')
def api_stats_trend():
    """某设备按月统计维修次数，格式: [{month, count}]"""
    equip_id = request.args.get('equip_id', '').strip()
    if not equip_id:
        return jsonify({"error": "请提供 equip_id 参数"}), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT TO_CHAR(maintenance_time, 'YYYY-MM') AS month,
                   COUNT(*) AS cnt
            FROM maintenance
            WHERE equip_id = %s
            GROUP BY TO_CHAR(maintenance_time, 'YYYY-MM')
            ORDER BY month
        """, (equip_id,))
        rows = cur.fetchall()
        result = [{"month": r[0], "count": r[1]} for r in rows]
        return jsonify(result)
    finally:
        conn.close()


# ==================== 页面路由 ====================

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
