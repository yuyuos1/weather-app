import logging
import os
import sys
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_cors import CORS
import pymysql
from lxml import etree
import base64
from io import BytesIO
import matplotlib

matplotlib.use('Agg')  # 使用非交互式后端，避免GUI报错
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from datetime import datetime
from werkzeug.utils import secure_filename


# ====================== 修复 weather_service 依赖（避免导入报错） ======================
# 如果没有单独的 weather_service.py，先定义一个基础版的 weather_service 类
class WeatherService:
    def get_current_weather(self):
        """模拟获取当前天气数据"""
        return {
            "temperature": 25.5,
            "feels_like": 26.8,
            "humidity": 65,
            "pressure": 1012,
            "description": "晴",
            "icon": "01d",
            "wind_speed": 3.2,
            "wind_direction": 180,
            "visibility": 10.0,
            "rain_probability": 0
        }

    def get_daily_forecast(self, days=7):
        """模拟获取未来N天天气预报"""
        forecast = []
        base_date = datetime.now()
        for i in range(days):
            date = (base_date + pd.Timedelta(days=i)).strftime("%Y-%m-%d")
            forecast.append({
                "date": date,
                "max_temp": 25 + i % 5,
                "min_temp": 15 + i % 4,
                "avg_humidity": 60 + i % 10,
                "max_rain_prob": i % 20,
                "description": "晴" if i % 3 == 0 else "多云"
            })
        return forecast

    def get_forecast(self):
        """模拟获取小时级预报"""
        hourly = []
        base_time = datetime.now()
        for i in range(24):
            time_str = (base_time + pd.Timedelta(hours=i)).strftime("%H:%M")
            hourly.append({
                "time": time_str,
                "temperature": 20 + i % 8,
                "humidity": 65 + i % 5,
                "rain_probability": i % 30
            })
        return hourly


# 实例化天气服务（替代外部导入）
weather_service = WeatherService()

# ====================== 基础配置 ======================
# 设置matplotlib字体，解决中文乱码
try:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False
except Exception as e:
    logging.warning(f"字体配置警告: {e}")
    plt.rcParams['font.family'] = 'sans-serif'

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# ====================== Flask 应用初始化 ======================
app = Flask(__name__, static_folder='static', template_folder='templates')

# 1. 数据库配置（优先使用SQLite，适配部署场景；本地开发可注释后改用MySQL）
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///air_quality.db'  # 无需额外安装数据库
# 本地MySQL配置（开发时使用，部署时注释）
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/air_quality_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭不必要的警告
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key_123456')  # 适配环境变量

# 2. 头像上传配置（修复路径问题，适配打包/部署）
BASE_DIR = os.path.dirname(os.path.abspath(sys.executable)) if hasattr(sys, '_MEIPASS') else os.path.dirname(
    os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static/avatars')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}  # 允许的头像格式
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 3. 跨域配置（增强，适配部署后的前后端分离）
CORS(
    app,
    supports_credentials=True,
    origins=['*']  # 生产环境可改为具体域名，如 'https://your-username.github.io'
)


@app.after_request
def after_request(response):
    """全局响应头，解决跨域"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response


# 初始化数据库和登录管理器
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录后访问'


# ====================== 数据库模型 ======================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    user_type = db.Column(db.String(20), nullable=False, default='user')
    avatar = db.Column(db.String(200), default='default-avatar.png')


class WeatherData(db.Model):
    """天气数据模型"""
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    temperature = db.Column(db.Float, nullable=False)  # 温度
    feels_like = db.Column(db.Float)  # 体感温度
    humidity = db.Column(db.Integer)  # 湿度
    pressure = db.Column(db.Integer)  # 气压
    description = db.Column(db.String(100))  # 天气描述
    icon = db.Column(db.String(10))  # 天气图标代码
    wind_speed = db.Column(db.Float)  # 风速
    wind_direction = db.Column(db.Integer)  # 风向
    visibility = db.Column(db.Float)  # 能见度
    rain_probability = db.Column(db.Float, default=0)  # 降雨概率
    data_type = db.Column(db.String(20), default='current')  # 数据类型：current, forecast

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'temperature': self.temperature,
            'feels_like': self.feels_like,
            'humidity': self.humidity,
            'pressure': self.pressure,
            'description': self.description,
            'icon': self.icon,
            'wind_speed': self.wind_speed,
            'wind_direction': self.wind_direction,
            'visibility': self.visibility,
            'rain_probability': self.rain_probability,
            'data_type': self.data_type
        }


# ====================== 登录管理器回调 ======================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ====================== 数据预处理类 ======================
class DataPreprocessor:
    @staticmethod
    def preprocess(df):
        df_clean = df.copy()
        df_clean = DataPreprocessor._handle_missing(df_clean)
        df_clean = DataPreprocessor._remove_duplicates(df_clean)
        df_clean = DataPreprocessor._validate_dtypes(df_clean)
        df_clean = DataPreprocessor._handle_outliers(df_clean)
        df_clean = DataPreprocessor._standardize_date(df_clean)
        logging.info(f"预处理完成，原始数据{len(df)}条，处理后{len(df_clean)}条")
        return df_clean

    @staticmethod
    def _handle_missing(df):
        missing = df.isnull().sum()
        if missing.sum() > 0:
            logging.info(f"发现缺失值:\n{missing[missing > 0]}")
            num_cols = ['AQI', 'PM2.5', 'PM10', 'O3', 'CO', 'SO2', 'NO2']
            for col in num_cols:
                if col in df.columns:
                    df[col].fillna(df[col].median(), inplace=True)
            str_cols = ['月份', 'AQI范围', '质量等级']
            for col in str_cols:
                if col in df.columns:
                    df[col].fillna(df[col].mode()[0], inplace=True)
        return df

    @staticmethod
    def _remove_duplicates(df):
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            logging.info(f"发现{dup_count}条重复记录，已删除")
            df = df.drop_duplicates()
        return df

    @staticmethod
    def _validate_dtypes(df):
        num_cols = ['AQI', 'PM2.5', 'PM10', 'O3', 'CO', 'SO2', 'NO2']
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df

    @staticmethod
    def _handle_outliers(df):
        ranges = {
            'AQI': (0, 500),
            'PM2.5': (0, 500),
            'PM10': (0, 600),
            'O3': (0, 800)
        }
        for col, (min_val, max_val) in ranges.items():
            if col in df.columns:
                mask = (df[col] < min_val) | (df[col] > max_val)
                if mask.any():
                    logging.info(f"在 {col} 列发现 {mask.sum()} 个异常值，已用中位数替换")
                    median = df[col].median()
                    df.loc[mask, col] = median
        return df

    @staticmethod
    def _standardize_date(df):
        if '月份' in df.columns:
            df['月份'] = pd.to_datetime(df['月份'], format='%Y-%m', errors='coerce')
        return df

    @staticmethod
    def save_to_csv(df, output_path):
        try:
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            logging.info(f"清洗数据已保存至 {output_path}")
        except Exception as e:
            logging.error(f"CSV保存失败: {str(e)}")

    @staticmethod
    def insert_to_mysql(df, host, database, user, password):
        try:
            admin_conn = pymysql.connect(host=host, user=user, password=password)
            with admin_conn.cursor() as admin_cursor:
                admin_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database} CHARACTER SET utf8mb4")
                admin_conn.commit()
            admin_conn.close()
            connection = pymysql.connect(
                host=host,
                database=database,
                user=user,
                password=password
            )
            with connection.cursor() as cursor:
                create_table_sql = """
                    CREATE TABLE IF NOT EXISTS air_quality_data (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        month VARCHAR(20) NOT NULL,
                        aqi INT,
                        aqi_range VARCHAR(20),
                        qua_grade VARCHAR(20),
                        pm2_5 INT,
                        pm10 INT,
                        co FLOAT,
                        so2 FLOAT,
                        no2 FLOAT,
                        o3 INT
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
                cursor.execute(create_table_sql)
                cursor.execute("TRUNCATE TABLE air_quality_data")
                values = [tuple(row[['月份', 'AQI', 'AQI范围', '质量等级', 'PM2.5', 'PM10', 'CO', 'SO2', 'NO2', 'O3']])
                          for _, row in df.iterrows()]
                query = """
                    INSERT INTO air_quality_data 
                    (month, aqi, aqi_range, qua_grade, pm2_5, pm10, co, so2, no2, o3)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.executemany(query, values)
                connection.commit()
                logging.info(f"成功插入{len(df)}条数据到数据库")
        except pymysql.Error as e:
            logging.error(f"数据库操作失败: {e}")
        finally:
            if 'connection' in locals() and connection.open:
                connection.close()


# ====================== 数据解析类 ======================
class DetailParse:
    def parse(self, filePath):
        parser = etree.HTMLParser(encoding='utf-8')
        tree = etree.parse(filePath, parser=parser)
        month = tree.xpath("//td/a[@href]/text()")
        aqi = list(map(int, tree.xpath("//tr/td[not(@class)][2]/text()")))
        aqi_range = tree.xpath('//tr/td[@class="hidden-xs"][1]/text()')
        qua_grade = tree.xpath('//td/span/text()')
        pm2_5 = list(map(int, tree.xpath('//tr/td[not(@class)][4]/text()')))
        pm10 = list(map(int, tree.xpath('//tr/td[not(@class)][5]/text()')))
        o3 = list(map(int, tree.xpath('//tr/td[@class="hidden-xs"][5]/text()')))
        field_keys = tree.xpath('//tr/th[@style="background:#d9edf7;" and @class="hidden-xs"]/text()')
        field_values = [
            list(map(float, tree.xpath('//tr/td[@class="hidden-xs"][2]/text()'))),
            list(map(float, tree.xpath('//tr/td[@class="hidden-xs"][3]/text()'))),
            list(map(float, tree.xpath('//tr/td[@class="hidden-xs"][4]/text()')))
        ]
        field_dict = dict(zip(field_keys, field_values))
        data = {
            "月份": month,
            "AQI": aqi,
            "AQI范围": aqi_range,
            "质量等级": qua_grade,
            "PM2.5": pm2_5,
            "PM10": pm10,
            "O3": o3
        }
        for key in ["CO", "SO2", "NO2"]:
            if key in field_dict:
                data[key] = field_dict[key]
        df = pd.DataFrame(data)
        return df

    def export_to_csv(self, df, output_path):
        try:
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            logging.info(f"原始数据成功导出至 {output_path}")
        except Exception as e:
            logging.error(f"CSV导出失败: {str(e)}")


# ====================== 数据可视化类 ======================
class DataVisualizer:
    @staticmethod
    def _fig_to_base64(fig):
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        return base64.b64encode(buf.getvalue()).decode('utf-8')

    @classmethod
    def generate_aqi_trend(cls, df):
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.lineplot(data=df, x='月份', y='AQI', ax=ax, marker='o')
        ax.set_title('AQI月度趋势')
        return cls._fig_to_base64(fig)

    @classmethod
    def generate_pollutant_comparison(cls, df):
        fig, ax = plt.subplots(figsize=(12, 6))
        df.plot(x='月份', y=['PM2.5', 'PM10', 'O3'], kind='bar', ax=ax)
        ax.set_title('污染物浓度对比')
        return cls._fig_to_base64(fig)

    @classmethod
    def generate_quality_distribution(cls, df):
        fig, ax = plt.subplots(figsize=(8, 8))
        df['质量等级'].value_counts().plot.pie(autopct='%1.1f%%', ax=ax)
        ax.set_title('质量等级分布')
        return cls._fig_to_base64(fig)

    @classmethod
    def generate_correlation_heatmap(cls, df):
        df = df[['AQI', 'PM2.5', 'PM10', 'O3']].apply(pd.to_numeric, errors='coerce')
        df = df.dropna()
        if len(df) < 2:
            raise ValueError("数据不足，无法计算相关系数")
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(df.corr(), annot=True, ax=ax, cmap='coolwarm')
        ax.set_title('污染物相关性分析')
        return cls._fig_to_base64(fig)


# ====================== 工具函数 ======================
def load_data():
    """加载清洗后的空气质量数据"""
    try:
        # 适配路径，确保打包/部署后能找到clean_data.csv
        csv_path = os.path.join(BASE_DIR, 'clean_data.csv')
        df = pd.read_csv(csv_path)
        df['月份'] = pd.to_datetime(df['月份'])
        return df
    except FileNotFoundError:
        logging.error("clean_data.csv文件未找到，生成模拟数据")
        # 生成模拟数据避免报错
        dates = pd.date_range(start='2024-01-01', end='2024-12-01', freq='MS')
        df = pd.DataFrame({
            '月份': dates,
            'AQI': [50 + i * 5 for i in range(len(dates))],
            'PM2.5': [20 + i * 3 for i in range(len(dates))],
            'PM10': [40 + i * 4 for i in range(len(dates))],
            'O3': [60 + i * 2 for i in range(len(dates))],
            'CO': [0.8 + i * 0.1 for i in range(len(dates))],
            'SO2': [10 + i * 1 for i in range(len(dates))],
            'NO2': [20 + i * 2 for i in range(len(dates))],
            'AQI范围': ['0-50' for _ in dates],
            '质量等级': ['优' for _ in dates]
        })
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        return df


def allowed_file(filename):
    """检查头像文件格式是否合法"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# ====================== 核心路由 ======================
@app.route('/')
@login_required
def dashboard():
    return render_template('air_data_visualization.html', current_user=current_user)


@app.route('/data')
@login_required
def get_data():
    try:
        df = load_data()
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            df = df[(df['月份'] >= start_date) & (df['月份'] <= end_date)]
        data_types = request.args.getlist('data_type')
        result = {}
        for dt in data_types:
            if dt in df.columns:
                result[dt] = df[['月份', dt]].to_dict(orient='records')
        return jsonify(result)
    except Exception as e:
        logging.error(f"获取数据失败: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/visualize/<chart_type>')
@login_required
def visualize(chart_type):
    try:
        df = load_data()
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            df = df[(df['月份'] >= start_date) & (df['月份'] <= end_date)]
            if len(df) < 2:
                return jsonify({"error": "时间段内数据不足，无法生成图表"}), 400

        # 检查必要列
        required_cols = {
            'aqi_trend': ['AQI', '月份'],
            'pollutant_comparison': ['PM2.5', 'PM10', 'O3', '月份'],
            'quality_distribution': ['质量等级'],
            'correlation_heatmap': ['AQI', 'PM2.5', 'PM10', 'O3']
        }.get(chart_type, [])

        if not required_cols:
            return jsonify({"error": "不支持的图表类型"}), 400

        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            return jsonify({"error": f"缺失必要列：{', '.join(missing)}"}), 400

        # 生成图表和分析文本
        chart_data = get_chart_data(chart_type, df)
        analysis_text = generate_analysis_text(chart_type, df)
        return jsonify({
            "chart_data": chart_data,
            "analysis_text": analysis_text
        })
    except Exception as e:
        logging.error(f"可视化错误: {e}")
        return jsonify({"error": str(e)}), 500


def get_chart_data(chart_type, df):
    """生成指定类型的图表Base64数据"""
    if chart_type == 'aqi_trend':
        return DataVisualizer.generate_aqi_trend(df)
    elif chart_type == 'pollutant_comparison':
        return DataVisualizer.generate_pollutant_comparison(df)
    elif chart_type == 'quality_distribution':
        return DataVisualizer.generate_quality_distribution(df)
    elif chart_type == 'correlation_heatmap':
        return DataVisualizer.generate_correlation_heatmap(df)


def generate_analysis_text(chart_type, df):
    """生成图表对应的分析文本"""
    if chart_type == 'aqi_trend':
        avg_aqi = df['AQI'].mean()
        max_aqi = df['AQI'].max()
        trend = df['AQI'].pct_change().mean() * 100
        advice = (
            f"\n\n健康建议："
            f"- 当AQI低于50时，适合开窗通风和户外运动\n"
            f"- AQI在101-150时，敏感人群应减少长时间户外活动\n"
            f"- 当前最高AQI值{max_aqi}出现时，建议佩戴口罩出行"
        )
        return (
            f"平均AQI：{avg_aqi:.1f}\n"
            f"最高AQI：{max_aqi}\n"
            f"整体趋势：{'上升' if trend > 0 else '下降'} {abs(trend):.1f}%{advice}"
        )
    elif chart_type == 'pollutant_comparison':
        pollutants = ['PM2.5', 'PM10', 'O3']
        max_pollutant = df[pollutants].max().idxmax()
        max_value = df[max_pollutant].max()
        over_threshold = (df[max_pollutant] > 75).sum()
        advice = (
            f"\n\n防护建议："
            f"- 当{max_pollutant}超过75μg/m³时，建议："
            f"  ▪️ 戴N95口罩进行户外活动\n"
            f"  ▪️ 减少长时间户外运动\n"
            f"  ▪️ 早晚高峰时段尽量避免外出"
        )
        return (
            f"最高污染物：{max_pollutant}\n"
            f"峰值浓度：{max_value}μg/m³\n"
            f"超标比例：{over_threshold / len(df) * 100:.0f}%{advice}"
        )
    elif chart_type == 'quality_distribution':
        grade_counts = df['质量等级'].value_counts()
        total_days = len(df)
        advice = (
            f"\n\n生活建议："
            f"- '优'等级日：适合所有户外活动\n"
            f"- '良'等级日：可正常安排户外运动\n"
            f"- '轻度污染'日：建议减少高强度运动\n"
            f"- 当前污染日占比：{grade_counts.get('轻度污染', 0) / total_days * 100:.0f}%"
        )
        return (
            f"优：{grade_counts.get('优', 0)}天 ({grade_counts.get('优', 0) / total_days * 100:.0f}%)\n"
            f"良：{grade_counts.get('良', 0)}天 ({grade_counts.get('良', 0) / total_days * 100:.0f}%)\n"
            f"轻度污染：{grade_counts.get('轻度污染', 0)}天{advice}"
        )
    elif chart_type == 'correlation_heatmap':
        corr_matrix = df[['AQI', 'PM2.5', 'PM10', 'O3']].corr()
        correlations = corr_matrix.unstack()
        strongest = correlations.abs().idxmax()
        max_corr = correlations[strongest]
        pair = strongest if isinstance(strongest, tuple) else (strongest, strongest)
        advice = (
            f"\n\n环境建议："
            f"- 需重点关注{pair[0]}与{pair[1]}的协同治理\n"
            f"- 正相关表明两者可能存在共同污染源\n"
            f"- 建议环保部门联合监测{pair[0]}排放源"
        )
        return (
            f"最强相关：{pair[0]}与{pair[1]}\n"
            f"相关系数：{max_corr:.2f}\n"
            f"正相关：{'是' if max_corr > 0 else '否'}{advice}"
        )
    return ""


# ====================== 用户认证路由 ======================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            if not username or not password:
                return jsonify({"message": "用户名和密码不能为空"}), 400

            user = User.query.filter_by(username=username).first()
            if user:
                return jsonify({"message": "用户名已存在"}), 400

            new_user = User(
                username=username,
                password=password,  # 生产环境建议加密存储，如使用werkzeug.security
                user_type='user',
                avatar='default-avatar.png'
            )
            db.session.add(new_user)
            db.session.commit()
            return jsonify({"message": "账户创建成功"}), 200
        except Exception as e:
            db.session.rollback()
            logging.error(f"注册失败: {e}")
            return jsonify({"message": "注册失败：" + str(e)}), 500
    return render_template('air_data_visualization.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_type = request.form.get('user_type', 'user')  # 默认普通用户

        if not username or not password:
            return jsonify({"message": "用户名和密码不能为空"}), 400

        user = User.query.filter_by(username=username, user_type=user_type).first()
        if user and user.password == password:
            login_user(user)
            return jsonify({"message": "登录成功"}), 200
        else:
            return jsonify({"message": "用户名、密码或用户类型错误"}), 401
    return render_template('air_data_visualization.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ====================== 管理员路由 ======================
@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    if current_user.user_type != 'admin':
        return jsonify({"error": "无管理员权限"}), 403
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'user_type': user.user_type,
        'avatar': user.avatar
    } for user in users])


@app.route('/api/user/<int:user_id>', methods=['PUT'])
@login_required
def update_user_type(user_id):
    if current_user.user_type != 'admin':
        return jsonify({"error": "无管理员权限"}), 403
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "用户不存在"}), 404

        data = request.get_json()
        new_type = data.get('userType')
        if new_type not in ['admin', 'user']:
            return jsonify({"error": "无效的用户类型（仅支持admin/user）"}), 400

        user.user_type = new_type
        db.session.commit()
        return jsonify({"message": "用户类型更新成功"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"更新用户类型失败: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/user/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    if current_user.user_type != 'admin':
        return jsonify({"error": "无管理员权限"}), 403
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "用户不存在"}), 404

        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "用户删除成功"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"删除用户失败: {e}")
        return jsonify({"error": str(e)}), 500


# ====================== 用户个人中心路由 ======================
@app.route('/api/clean-data', methods=['GET'])
@login_required
def get_clean_data():
    df = load_data()
    return jsonify(df.to_dict(orient='records'))


@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    try:
        data = request.get_json()
        current_password = data.get('currentPassword')
        new_password = data.get('newPassword')

        if not current_password or not new_password:
            return jsonify({"success": False, "message": "当前密码和新密码不能为空"}), 400

        if len(new_password) < 3 or len(new_password) > 16:  # 放宽密码长度限制，更合理
            return jsonify({"success": False, "message": "密码长度需在3-16位之间"}), 400

        if current_user.password != current_password:
            return jsonify({"success": False, "message": "当前密码错误"}), 401

        current_user.password = new_password
        db.session.commit()
        return jsonify({"success": True, "message": "密码修改成功"}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"修改密码失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/update_profile', methods=['POST'])
@login_required
def update_profile():
    try:
        new_username = request.form.get('username')
        avatar_file = request.files.get('avatar')

        # 验证用户名
        if not new_username:
            return jsonify({'error': '用户名不能为空'}), 400

        # 检查用户名唯一性（排除当前用户）
        existing_user = User.query.filter(
            User.username == new_username,
            User.id != current_user.id
        ).first()
        if existing_user:
            return jsonify({'error': '用户名已存在'}), 400

        # 更新用户名
        current_user.username = new_username

        # 处理头像上传
        if avatar_file and allowed_file(avatar_file.filename):
            filename = secure_filename(avatar_file.filename)
            # 生成唯一文件名，避免覆盖
            filename = f"{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            avatar_file.save(upload_path)
            # 保存相对路径，便于前端访问
            current_user.avatar = f'avatars/{filename}'

        db.session.commit()
        return jsonify({'success': True, 'message': '个人信息更新成功'}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"更新个人信息失败: {e}")
        return jsonify({'error': str(e)}), 500


# ====================== 天气相关路由 ======================
@app.route('/api/weather/current')
def get_current_weather():
    """获取当前天气"""
    try:
        weather_data = weather_service.get_current_weather()
        return jsonify({
            'success': True,
            'data': weather_data
        })
    except Exception as e:
        logging.error(f"获取当前天气失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/weather/forecast')
def get_weather_forecast():
    """获取天气预报（默认15天，最多15天）"""
    try:
        days = request.args.get('days', 15, type=int)
        days = min(days, 15)  # 限制最多15天
        forecast_data = weather_service.get_daily_forecast(days)
        return jsonify({
            'success': True,
            'data': forecast_data
        })
    except Exception as e:
        logging.error(f"获取天气预报失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/weather/hourly')
def get_hourly_forecast():
    """获取小时级天气预报（默认24小时，最多120小时）"""
    try:
        hours = request.args.get('hours', 24, type=int)
        hours = min(hours, 120)  # 限制最多120小时（5天）
        forecast_data = weather_service.get_forecast()
        hourly_data = forecast_data[:hours // 3]  # 每3小时一个数据点
        return jsonify({
            'success': True,
            'data': hourly_data
        })
    except Exception as e:
        logging.error(f"获取小时级预报失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/weather/charts/<chart_type>')
def get_weather_chart(chart_type):
    """获取天气图表数据（温度/湿度/降雨概率）"""
    try:
        if chart_type == 'temperature':
            forecast_data = weather_service.get_daily_forecast(7)
            chart_data = {
                'labels': [item['date'] for item in forecast_data],
                'max_temp': [item['max_temp'] for item in forecast_data],
                'min_temp': [item['min_temp'] for item in forecast_data]  # 补充最低温度
            }
        elif chart_type == 'humidity':
            forecast_data = weather_service.get_daily_forecast(7)
            chart_data = {
                'labels': [item['date'] for item in forecast_data],
                'values': [item['avg_humidity'] for item in forecast_data]
            }
        elif chart_type == 'rain':
            forecast_data = weather_service.get_daily_forecast(7)
            chart_data = {
                'labels': [item['date'] for item in forecast_data],
                'values': [item['max_rain_prob'] for item in forecast_data]
            }
        else:
            return jsonify({
                'success': False,
                'error': '不支持的图表类型（仅支持temperature/humidity/rain）'
            }), 400

        return jsonify({
            'success': True,
            'data': chart_data
        })
    except Exception as e:
        logging.error(f"获取天气图表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ====================== 启动配置 ======================
if __name__ == '__main__':
    # 创建数据库表
    with app.app_context():
        db.create_all()
        # 初始化管理员账户（首次运行自动创建，密码123456）
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                password='123456',
                user_type='admin',
                avatar='default-avatar.png'
            )
            db.session.add(admin_user)
            db.session.commit()
            logging.info("默认管理员账户创建成功：用户名admin，密码123456")

    # 启动应用（适配生产/开发环境）
    debug_mode = os.environ.get('FLASK_DEBUG', 'True') == 'True'
    port = int(os.environ.get('PORT', 5001))  # 适配部署平台的端口
    app.run(
        debug=debug_mode,
        port=port,
        host='0.0.0.0'  # 允许外部访问，适配部署
    )
