#!/bin/bash
# ============================================
# 工业设备台账管理系统 - 服务器一键部署脚本
# 在 openGauss 所在服务器上执行 (192.168.31.160)
# ============================================

set -e

echo "===== 1. 克隆项目 ====="
cd /home/omm
if [ -d "equip-mgmt-system" ]; then
    echo "项目目录已存在，更新代码..."
    cd equip-mgmt-system && git pull
else
    git clone https://github.com/ynd6/equip-mgmt-system.git
    cd equip-mgmt-system
fi

echo ""
echo "===== 2. 安装 Python 依赖 ====="
pip3 install flask psycopg2-binary faker -i https://mirrors.aliyun.com/pypi/simple/ 2>/dev/null || \
pip3 install flask psycopg2-binary faker

echo ""
echo "===== 3. 修改数据库连接为本地 ====="
sed -i 's/host="192.168.31.160"/host="127.0.0.1"/' app.py
echo "已改为 host=127.0.0.1"

echo ""
echo "===== 4. 初始化数据库（跳过已有数据）====="
python3 rebuild_data.py 2>/dev/null && echo "数据初始化完成" || echo "数据已存在，跳过"

echo ""
echo "===== 5. 停止旧进程 ====="
pkill -f "python3 app.py" 2>/dev/null || echo "无旧进程"

echo ""
echo "===== 6. 后台启动 Flask ====="
nohup python3 app.py > flask.log 2>&1 &
sleep 2

if pgrep -f "python3 app.py" > /dev/null; then
    echo "Flask 启动成功！PID: $(pgrep -f 'python3 app.py')"
else
    echo "启动失败，查看日志: tail -f /home/omm/equip-mgmt-system/flask.log"
    exit 1
fi

echo ""
echo "===== 7. 放行防火墙端口 ====="
sudo firewall-cmd --add-port=5000/tcp --permanent 2>/dev/null && sudo firewall-cmd --reload 2>/dev/null && echo "防火墙已放行 5000" || echo "防火墙未运行或无需配置"

echo ""
echo "============================================"
echo "  部署完成！"
echo "  访问地址: http://192.168.31.160:5000"
echo "  查看日志: tail -f /home/omm/equip-mgmt-system/flask.log"
echo "============================================"
