from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import time

# 尝试设置中文字体
try:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
    plt.rcParams['axes.unicode_minus'] = False
except:
    pass


class EmotionChart(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(5, 4), dpi=100)
        super().__init__(self.fig)

        self.ax = self.fig.add_subplot(111)
        self.fig.tight_layout()

        self.emotion_colors = {
            'happy': '#FFD700',
            'sad': '#4169E1',
            'angry': '#FF4500',
            'surprise': '#9932CC',
            'fear': '#808080',
            'disgust': '#228B22',
            'neutral': '#87CEEB'
        }

        self.last_update_time = 0
        self.update_interval = 1.0  # 每秒最多更新一次

    def update_chart(self, emotion_counts, force=False):
        """更新饼图，force=True 时不检查更新间隔"""
        current_time = time.time()
        if not force and (current_time - self.last_update_time < self.update_interval):
            return

        self.last_update_time = current_time
        self.ax.clear()

        filtered_counts = {k: v for k, v in emotion_counts.items() if v > 0}

        if not filtered_counts:
            self.ax.text(0.5, 0.5, '暂无检测数据', ha='center', va='center', fontsize=16)
            self.draw()
            return

        labels = list(filtered_counts.keys())
        sizes = list(filtered_counts.values())
        colors = [self.emotion_colors.get(label, '#808080') for label in labels]

        self.ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 12}
        )

        self.ax.axis('equal')
        self.ax.set_title('情绪占比统计', fontsize=14, pad=20)
        self.draw()