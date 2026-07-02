# 工业设备台账管理系统

基于 **Flask + openGauss** 的工业设备全生命周期管理平台，支持设备台账管理、维修记录追踪、多条件筛选、车间统计可视化及 DB4AI 时序预测。


## 系统截图

### 设备管理
支持模糊搜索、新增、批量编辑、条件删除，4 种状态（未使用/在用/维修中/报废）

### 维修记录
多条件筛选（设备 + 时间范围 + 故障类型），列存储优化查询

### 车间统计
车间设备汇总表 + 设备月度维修趋势柱状图 + DB4AI 时序预测（橙红虚线柱为预测值）

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python Flask, psycopg2 |
| 数据库 | openGauss 6.0（列存储 + 行存储混合） |
| 前端 | Bootstrap 5, Chart.js, 原生 JavaScript Fetch API |
| AI 预测 | openGauss DB4AI.PREDICT_TIME_SERIES / 加权移动平均回退 |

## 功能概览

### 设备管理
- 模糊搜索（编号 / 名称 / 型号）
- 新增、单个编辑、**批量编辑**（多选后统一修改状态和负责人）
- 条件删除（仅"未使用"且无维修记录可删）
- 4 种状态：未使用、在用、维修中、报废

### 维修记录
- **多条件筛选**：设备编号 + 起止月份 + 故障类型关键词（可任意组合）
- 列存储优化查询，仅读取所需列，效率高于行存储
- 新增维修记录（应用层校验设备存在性 + 费用非负）

### 车间统计与预测
- 5 个车间的设备总数、在用数、维修总次数一览表
- **设备月度维修趋势柱状图**（Chart.js 渐变渲染，含动画）
- **DB4AI 时序预测**：基于近 6 个月数据预测下月故障频次，自动叠加到趋势图中（橙红虚线柱），含置信区间

## 老师如何使用

1. 浏览器打开 `http://192.168.31.160:5000`
2. 无需安装任何软件，三个标签页切换即可使用全部功能

详细操作说明见 **[使用说明.md](使用说明.md)**

## 快速部署

### 服务器部署（推荐）

在 openGauss 所在服务器上执行：

```bash
cd /home/omm
wget https://raw.githubusercontent.com/ydn6/equip-mgmt-system/master/deploy.sh
bash deploy.sh
```

### 本地开发

```bash
git clone https://github.com/ydn6/equip-mgmt-system.git
cd equip-mgmt-system
pip install -r requirements.txt

# 修改 app.py 中 get_db() 的数据库连接参数
python rebuild_data.py    # 初始化数据
python app.py             # 启动 → http://127.0.0.1:5000
```

## 项目结构

```
equip-mgmt-system/
├── app.py                 # Flask 主程序（14 个 API 端点）
├── templates/
│   └── index.html         # Bootstrap 5 单页面应用
├── deploy.sh              # 服务器一键部署脚本
├── rebuild_data.py        # 数据库初始化（100 台设备 + 维修记录）
├── seed_maintenance.py    # 维修记录批量追加
├── requirements.txt       # Python 依赖
├── 使用说明.md             # 详细安装与使用文档
└── README.md
```

## API 文档

### 车间
| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/api/workshops` | 车间列表 |

### 设备
| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/api/equipment?q=` | 模糊搜索设备 |
| POST | `/api/equipment` | 新增设备 |
| PUT | `/api/equipment/<id>` | 更新设备 |
| DELETE | `/api/equipment/<id>` | 条件删除 |
| PUT | `/api/equipment/batch` | 批量更新 |

### 维修记录
| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/api/maintenance/<id>` | 某设备维修记录 |
| GET | `/api/maintenance/search` | 多条件筛选 |
| POST | `/api/maintenance` | 新增维修 |

### 统计与预测
| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/api/stats/workshop` | 车间统计 |
| GET | `/api/stats/trend?equip_id=` | 月度趋势 |
| GET | `/api/stats/predict?equip_id=` | DB4AI 预测 |

## 数据库表结构

```sql
workshop    (workshop_id, workshop_name, location)
equipment   (equip_id, equip_name, model, manufacture_date,
             purchase_price, workshop_id, responsible_person, status)
maintenance (maintenance_id, equip_id, maintenance_time, fault_desc, repair_cost)
-- maintenance 为列存储表，无外键约束，应用层负责校验
```
