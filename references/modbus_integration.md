# Modbus RTU 协议对接指南

## 1. 通信参数

| 参数 | 值 |
|------|-----|
| 波特率（默认） | 9600 bps |
| 数据位 | 8 |
| 停止位 | 1 |
| 校验 | 无校验（None） |
| 流控 | 无 |

## 2. 帧结构

```
Len + Adr + Cmd + Data[] + CRC16
```

- **Len**: 数据长度（字节数）
- **Adr**: 从机地址（0x01~0xFF）
- **Cmd**: 功能码/命令
- **Data[]**: 数据域
- **CRC16**: CRC校验，低字节在前

### CRC16 计算参数

| 参数 | 值 |
|------|-----|
| 多项式 | 0x8408 |
| 预置值 | 0xFFFF |
| 结果字节序 | 低字节在前（Little Endian） |

## 3. SELSENSE 读温指令

命令字：`0x17`

### LTU3K 芯片参数

| 参数 | 值 |
|------|-----|
| SelTarget | 0x07 |
| SelAction | 0x04 |

### LAU1 芯片参数

| 参数 | 值 |
|------|-----|
| SelTarget | 0x06 |
| SelAction | 0x00 |

## 4. 温度解析公式

```
温度(℃) = 11109.6 / (24 + (D2 + Δ1) / 375.3) - 290
```

- **D2**: 传感器原始数据第2字节
- **Δ1**: 校准参数，从 USER 0x08 地址读取
- **验证条件**: HEADER=0xF, SEN_DATA[23:19]=00100b

## 5. CRC16 Python 实现

```python
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
```

## 6. 完整读温示例

```python
import struct

# 组帧
adr = 0x01
cmd = 0x17
data = bytes([0x07, 0x04])  # SelTarget, SelAction (LTU3K)
frame_body = bytes([adr, cmd]) + data
crc = crc16(frame_body)
frame = frame_body + crc

# 发送（示例）
# serial_port.write(frame)
# response = serial_port.read(64)

# 解析温度
def parse_temperature(raw_bytes: bytes) -> float:
    # 提取 D2 和 Δ1
    d2 = raw_bytes[10]  # 示例偏移，需按实际协议调整
    delta1 = raw_bytes[20]  # 校准参数偏移
    temp = 11109.6 / (24 + (d2 + delta1) / 375.3) - 290
    return round(temp, 1)
```

## 7. 常见问题

- **读到 EPC 但温度不刷新**：芯片未进入测温模式，检查 SelTarget/SelAction 参数是否正确
- **CRC 校验失败**：确认多项式为 0x8408，预置值为 0xFFFF，低字节在前
- **读不到传感器**：检查天线功率是否 ≤33dBm，尝试上调 2dBm
