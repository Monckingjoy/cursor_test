import pymysql
from flask import Flask, request, render_template, redirect, url_for, session
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

# 创建 Flask 应用实例
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# 数据库连接配置
db_config = {
    'user': 'root',
    'password': '123456',
    'host': 'localhost',
    'database': 'cursor_test_project'
}

# 获取数据库连接
def get_db_connection():
    # 使用 PyMySQL 连接 MySQL 数据库
    return pymysql.connect(
        user=db_config['user'],
        password=db_config['password'],
        host=db_config['host'],
        database=db_config['database'],
        cursorclass=pymysql.cursors.DictCursor  # 返回字典格式的游标
    )

# 定义路由和视图函数
@app.route('/', methods=['GET', 'POST'])
def calculate_hours():
    if request.method == 'POST':
        # 获取表单数据
        start_time = request.form.get('start_time') + ":00"  # 添加秒
        end_time = request.form.get('end_time') + ":00"  # 添加秒

        # 解析时间字符串为 datetime 对象
        start = datetime.strptime(start_time, '%H:%M:%S')
        end = datetime.strptime(end_time, '%H:%M:%S')

        # 计算工作时长
        work_duration = end - start

        # 减去午休和晚饭时间
        if start < datetime.strptime('12:00:00', '%H:%M:%S') < end:
            work_duration -= timedelta(hours=1.5)  # 午休时间
        if start < datetime.strptime('17:30:00', '%H:%M:%S') < end:
            work_duration -= timedelta(hours=0.5)  # 晚饭时间

        # 计算工时（以小时为单位）
        work_hours = work_duration.total_seconds() / 3600

        # 根据工时判断工作状态
        if work_hours < 8:
            message = f"旷工 {8 - work_hours:.2f} 小时"
            work_status = "旷工"
        elif work_hours > 8:
            message = f"加班 {work_hours - 8:.2f} 小时"
            work_status = "加班"
        else:
            message = "正常工作"
            work_status = "正常"

        # 保存记录到数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO work_time (start_time, end_time, dur_time, work_status) VALUES (%s, %s, %s, %s)",
            (start.strftime('%H:%M:%S'), end.strftime('%H:%M:%S'), work_hours, work_status)
        )
        conn.commit()
        cursor.close()
        conn.close()

        # 重定向到 GET 请求，防止表单重复提交
        return redirect(url_for('calculate_hours'))

    # GET 请求时渲染模板
    return render_template('index.html', work_hours=None, message=None, history=get_history(), average_hours=calculate_average_hours())

# 获取历史记录
def get_history():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM work_time")  # 查询所有记录
    history = cursor.fetchall()  # 获取所有结果
    cursor.close()
    conn.close()
    return history

# 删除记录
@app.route('/delete/<int:history_id>', methods=['POST'])
def delete_record(history_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM work_time WHERE history_id = %s", (history_id,))  # 删除指定记录
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('calculate_hours'))  # 重定向到主页

def calculate_average_hours():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT AVG(dur_time) as average_hours FROM work_time")  # 计算平均工时
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result['average_hours'] if result['average_hours'] is not None else 0

def format_duration(duration):
    # 假设duration是一个timedelta对象
    total_seconds = int(duration.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02}:{seconds:02}"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_name = request.form['user_name']
        user_count = request.form['user_count']
        password = request.form['password']

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_info WHERE user_name = %s AND user_count = %s", (user_name, user_count))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['user_id']
            return redirect(url_for('home'))
        else:
            return "用户名或密码错误"

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_name = request.form['user_name']
        user_count = request.form['user_count']
        password = generate_password_hash(request.form['password'])

        cursor = db.cursor()
        cursor.execute("INSERT INTO user_info (user_name, user_count, password) VALUES (%s, %s, %s)", (user_name, user_count, password))
        db.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/home')
def home():
    if 'user_id' in session:
        return "欢迎回来，用户！"
    return redirect(url_for('login'))

# 启动 Flask 应用
if __name__ == '__main__':
    app.run(debug=True)  # 开启调试模式 