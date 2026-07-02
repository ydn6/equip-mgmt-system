# 工业设备台账管理系统

基于 **Flask + openGauss** 的工业设备全生命周期管理系统，支持设备台账管理、维修记录追踪、多条件筛选、车间统计可视化及 DB4AI 时序预测。


## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python Flask, psycopg2 |
| 数据库 | openGauss 6.0（列存储 + 行存储混合） |
| 前端 | Bootstrap 5, Chart.js, 原生 JavaScript Fetch API |
| AI 预测 | openGauss DB4AI.PREDICT_TIME_SERIES / 加权移动平均回退 |

## 功能概览

### 设备管理
- 模糊搜索（编号/名称/型号）
- 新增、单个编辑、批量编辑（多选后统一修改状态和负责人）
- 条件删除（仅"未使用"且无维修记录可删）
- 4 种状态：未使用、在用、维修中、报废

### 维修记录
- 多条件筛选：设备编号 + 起止月份 + 故障类型关键词
- 列存储优化查询，仅读取所需列
- 新增维修记录（应用层校验设备存在性 + 费用非负）

### 车间统计
- 5 个车间的设备总数、在用数、维修总次数一览表
- 设备月度维修趋势柱状图（Chart.js 美化渲染）
- **DB4AI 时序预测**：基于近 6 个月数据预测下月故障频次，自动叠加到趋势图中

## 项目结构

```
opengauss-python/
├── app.py                 # Flask 主程序（14 个 API 端点）
├── templates/
│   └── index.html         # Bootstrap 5 单页面应用
├── deploy.sh              # 服务器一键部署脚本
├── rebuild_data.py        # 数据库重建脚本（100 台设备 + 维修记录）
├── seed_maintenance.py    # 维修记录批量插入脚本
├── test_db.py             # 数据库连接测试
├── check_data.py          # 数据验证工具
├── check_schema.py        # 表结构查看工具
├── requirements.txt       # Python 依赖
└── README.md
```

## 部署方式

### 服务器部署（推荐，无需操作）

在 openGauss 所在服务器上执行一键脚本：

```bash
cd /home/omm
wget https://raw.githubusercontent.com/ynd6/equip-mgmt-system/main/deploy.sh
bash deploy.sh
```

部署完成后直接浏览器访问 `http://192.168.31.160:5000`。

### 本地开发部署

#### 1. 环境要求

- Python 3.10+
- openGauss 数据库（已包含 workshop / equipment / maintenance 三张表）

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 修改数据库连接

编辑 `app.py` 第 12-18 行的 `get_db()` 函数：

```python
def get_db():
    return psycopg2.connect(
        database="postgres",
        user="你的用户名",
        password="你的密码",
        host="你的数据库IP",
        port=5432
    )
```

#### 4. 初始化数据

```bash
python rebuild_data.py
```

#### 5. 启动应用

```bash
python app.py
```

浏览器访问 `http://127.0.0.1:5000`

## API 文档

### 车间
| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/api/workshops` | 车间列表（下拉框数据源） |

### 设备
| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/api/equipment?q=` | 模糊搜索设备 |
| POST | `/api/equipment` | 新增设备 |
| PUT | `/api/equipment/<id>` | 更新负责人和状态 |
| DELETE | `/api/equipment/<id>` | 条件删除（仅未使用+无记录） |
| PUT | `/api/equipment/batch` | 批量更新 |

### 维修记录
| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/api/maintenance/<id>` | 某设备维修记录（时间倒序） |
| GET | `/api/maintenance/search` | 多条件筛选（设备/月份/故障类型） |
| POST | `/api/maintenance` | 新增维修记录 |

### 统计与预测
| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/api/stats/workshop` | 车间设备统计 |
| GET | `/api/stats/trend?equip_id=` | 设备月度维修趋势 |
| GET | `/api/stats/predict?equip_id=` | DB4AI 下月故障预测 |

## 数据库表结构

```sql
workshop (workshop_id, workshop_name, location)
equipment (equip_id, equip_name, model, manufacture_date, purchase_price,
           workshop_id, responsible_person, status)
maintenance (maintenance_id, equip_id, maintenance_time, fault_desc, repair_cost)
-- maintenance 为列存储表，无外键约束，应用层负责校验
```
