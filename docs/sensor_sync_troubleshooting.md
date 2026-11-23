# 双副屏温度参数对齐与传感器排坑指南（SAMA ZW360 Ultra + TURZX）

在同时运行先马 `SAMA.exe`（6.8" 曲面屏）与图灵 `TURZX.exe`（8.8" 副屏）时，如果两块屏显示的 CPU 或 GPU 温度读数不一致，通常由以下两类底层原因导致：

## 1. `AppConfig.data` 绑定了不同的 CPU 温度子传感器（最常见）

在 AMD Ryzen 9000（如 `Ryzen 7 9800X3D`）等平台上，系统会同时暴露多个 CPU 相关温度节点：
- `CPU (Tctl/Tdie)` — 核心封装主温度（推荐）
- `CPU VDDCR_SOC VRM (SVI3 TFN)` — 主板/SOC 供电 VRM 温度（偏低且变化慢，并非 CPU 核心温度）
- `CCD1 (Tdie)` / `Core Average`

`SAMA.exe` 默认首次扫描时，可能会将 `CpuTempSensorSubName` 误绑定到 `CPU VDDCR_SOC VRM (SVI3 TFN)`，从而导致与另一块读取 `CPU (Tctl/Tdie)` 的副屏出现明显温差。

**解决方法**：
1. 打开 `SAMA.exe` → **设置 / 硬件监控设置**；
2. 将 **CPU 温度传感器** 手动统一选为 **`CPU (Tctl/Tdie)`**（Intel 平台统一选 `CPU Package`）；
3. 将 **GPU** 手动锁定为独显（例如 `GPU [#0]: NVIDIA GeForce RTX 5080`），避免多 GPU 平台（带核显 `AMD Radeon Graphics`）自动漂移到核显。

## 2. 主题内 `M_Data.queueLen` 平滑缓冲队列长度不一致

先马官方部分内置主题（如 `fish.turtheme`）为温度项设置了 `queueLen = 10`（10 次采样滑动平均），而多数实时主题采用 `queueLen = 0`（实时瞬时值），在负载骤升或回落时会产生 1–3°C 的滞后差。

本仓库 `release/WastelandDaydream_A.turtheme` 与 `scripts/build_sama_theme_A.ps1` 已将全部 10 项传感器统一显式设为 **`queueLen = 0`**，确保与桌面监控软件及其他副屏保持零延迟实时同步。
