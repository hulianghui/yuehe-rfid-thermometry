#!/usr/bin/env python3
"""
rfid_query.py — 悦和 RFID 测温系统命令行查询工具

功能:
  temp <sensor-id>        读取指定传感器温度
  list                    列出所有在线传感器
  history <id> <hours>    查询最近N小时温度历史
  rssi <id>               查询信号强度

用法:
  python3 rfid_query.py temp D001
  python3 rfid_query.py list
  python3 rfid_query.py history D001 24
  python3 rfid_query.py rssi D001
"""

import sys
import os
import json
import argparse

# 加载本地知识库（模拟数据，生产环境替换为真实API调用）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(SKILL_DIR, "data")

def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None

def crc16(data: bytes) -> bytes:
    """计算 Modbus CRC16，低字节在前"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc >>= 1
    return bytes([crc & 0xFF, (crc >> 8) & 0xFF])

def calc_temperature(d2: int, delta1: int = 0) -> float:
    """温度解析公式"""
    return round(11109.6 / (24 + (d2 + delta1) / 375.3) - 290, 1)

def cmd_temp(sensor_id: str):
    """读取单个传感器温度"""
    sensors = load_json("products_sensors.json")
    protocols = load_json("protocols.json")

    # 模拟数据（生产环境：实际发送 Modbus 指令）
    mock_data = {
        "D001": {"temp": 45.3, "rssi": -62, "status": "normal"},
        "D002": {"temp": 72.1, "rssi": -58, "status": "warning"},
        "D003": {"temp": 85.6, "rssi": -70, "status": "critical"},
        "D004": {"temp": 38.0, "rssi": -55, "status": "normal"},
    }

    if sensor_id not in mock_data:
        print(json.dumps({"error": f"未找到传感器 {sensor_id}，请检查ID是否正确"}, ensure_ascii=False, indent=2))
        sys.exit(1)

    data = mock_data[sensor_id]
    status = data["status"]
    status_text = {"normal": "✅ 正常", "warning": "⚠️ 关注", "critical": "🔴 告警"}[status]

    print(json.dumps({
        "status": "success",
        "command": "temp",
        "sensor_id": sensor_id,
        "temperature": data["temp"],
        "unit": "℃",
        "rssi": data["rssi"],
        "threshold": {"normal": "<60℃", "warning": "60-70℃", "critical": ">70℃"},
        "device_status": status_text,
        "reference": protocols
    }, ensure_ascii=False, indent=2))

def cmd_list():
    """列出所有传感器"""
    sensors = load_json("products_sensors.json")
    if not sensors:
        print(json.dumps({"error": "未找到传感器数据文件"}, ensure_ascii=False, indent=2))
        sys.exit(1)

    results = []
    for s in sensors:
        results.append({
            "model": s["model"],
            "name": s["name"],
            "chip": s["chip"],
            "temp_range": s["temp_range"],
            "accuracy": s["accuracy"],
            "reading_distance": s["reading_distance"],
            "mounting": s["mounting"],
            "ip_rating": s["ip"],
            "status": s["status"],
            "scenarios": s["scenarios"]
        })

    print(json.dumps({
        "status": "success",
        "command": "list",
        "total": len(results),
        "sensors": results
    }, ensure_ascii=False, indent=2))

def cmd_history(sensor_id: str, hours: int = 24):
    """查询温度历史"""
    # 模拟历史数据（生产环境：查询云平台或本地数据库）
    import random
    from datetime import datetime, timedelta

    points = []
    base_temp = random.uniform(35.0, 50.0)
    now = datetime.now()

    for i in range(min(hours * 4, 96)):  # 最多96个数据点
        t = now - timedelta(minutes=i * 15)
        temp = base_temp + random.uniform(-3, 3)
        points.append({
            "timestamp": t.isoformat(),
            "temperature": round(temp, 1),
            "rssi": random.randint(-72, -55)
        })

    print(json.dumps({
        "status": "success",
        "command": "history",
        "sensor_id": sensor_id,
        "period": f"{hours}小时",
        "data_points": len(points),
        "data": points[::-1]
    }, ensure_ascii=False, indent=2))

def cmd_rssi(sensor_id: str):
    """查询信号强度"""
    mock_rssi = {
        "D001": -62, "D002": -58, "D003": -70, "D004": -55
    }
    rssi = mock_rssi.get(sensor_id, -75)

    if rssi > -65:
        level = "极强"
    elif rssi > -75:
        level = "良好"
    else:
        level = "临界，建议检查天线或调整位置"

    print(json.dumps({
        "status": "success",
        "command": "rssi",
        "sensor_id": sensor_id,
        "rssi": rssi,
        "level": level,
        "threshold": {
            "极强": ">-65dBm",
            "良好": "-65~-75dBm",
            "临界": "<-75dBm"
        }
    }, ensure_ascii=False, indent=2))

def main():
    cmds = ["temp", "list", "history", "rssi"]

    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(json.dumps({
            "error": f"用法: rfid_query.py <{','.join(cmds)}> [args]",
            "examples": {
                "temp": "rfid_query.py temp D001      # 读取传感器温度",
                "list": "rfid_query.py list           # 列出所有传感器",
                "history": "rfid_query.py history D001 24  # 查询24小时历史",
                "rssi": "rfid_query.py rssi D001     # 查询信号强度"
            }
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "temp":
        if not args:
            print("错误: temp 需要传感器ID参数")
            sys.exit(1)
        cmd_temp(args[0])
    elif cmd == "list":
        cmd_list()
    elif cmd == "history":
        sensor_id = args[0] if args else "D001"
        hours = int(args[1]) if len(args) > 1 else 24
        cmd_history(sensor_id, hours)
    elif cmd == "rssi":
        if not args:
            print("错误: rssi 需要传感器ID参数")
            sys.exit(1)
        cmd_rssi(args[0])

if __name__ == "__main__":
    main()
