from flask import Flask, request, render_template
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def calculate_hours():
    if request.method == 'POST':
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')

        # 解析时间
        start = datetime.strptime(start_time, '%H:%M')
        end = datetime.strptime(end_time, '%H:%M')

        # 计算工作时长
        work_duration = end - start

        # 减去午休和晚饭时间
        if start < datetime.strptime('12:00', '%H:%M') < end:
            work_duration -= timedelta(hours=1.5)
        if start < datetime.strptime('17:30', '%H:%M') < end:
            work_duration -= timedelta(hours=0.5)

        # 计算工时
        work_hours = work_duration.total_seconds() / 3600

        # 提示信息
        if work_hours < 8:
            message = f"旷工 {8 - work_hours:.2f} 小时"
        elif work_hours > 8:
            message = f"加班 {work_hours - 8:.2f} 小时"
        else:
            message = "正常工作"

        return render_template('index.html', work_hours=work_hours, message=message)

    return render_template('index.html', work_hours=None, message=None)

if __name__ == '__main__':
    app.run(debug=True) 