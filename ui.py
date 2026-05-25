import sys
import cv2
import time
import csv
from collections import defaultdict, deque
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGroupBox, QMessageBox
)
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtCore import QTimer, Qt, QObject, pyqtSignal

from emotion_detector import detect_emotion
from qwen_api import analyze_emotion
from emotion_chart import EmotionChart
from voice import speak_async
from warning import check_warning, reset_warning_history


class EmotionDetectionWorker(QObject):
    """封装异步检测，通过信号传递结果"""
    result_ready = pyqtSignal(str)

    def __init__(self, executor):
        super().__init__()
        self.executor = executor
        self._is_running = False

    def submit(self, frame):
        if self._is_running:
            return False
        self._is_running = True
        future = self.executor.submit(detect_emotion, frame)
        future.add_done_callback(self._on_done)
        return True

    def _on_done(self, future):
        try:
            emotion = future.result()
        except Exception as e:
            print(f"检测异常: {e}")
            emotion = "neutral"
        self._is_running = False
        self.result_ready.emit(emotion)


class EmotionSystem(QWidget):
    MAX_RECORDS = 5000

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_variables()
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.worker = EmotionDetectionWorker(self.executor)
        self.worker.result_ready.connect(self.on_emotion_detected)

    def init_ui(self):
        """与之前你的 init_ui 完全一致，此处省略以节省篇幅，请直接使用你原有的"""
        pass   # 在这里粘贴你原来的 init_ui 代码

    def init_variables(self):
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.emotion_counts = defaultdict(int)
        self.detection_records = deque(maxlen=self.MAX_RECORDS)
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.is_detecting = False
        self.consecutive_failures = 0
        self.MAX_CONSEC_FAILURES = 10

    def start_detection(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            QMessageBox.critical(self, "错误", "无法打开摄像头！请检查摄像头是否被其他程序占用。")
            return

        self.timer.start(30)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.video_label.setText("正在加载...")

    def stop_detection(self):
        self.timer.stop()
        if self.cap is not None:
            self.cap.release()
            self.cap = None

        self.is_detecting = False
        self.consecutive_failures = 0
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.video_label.setText("摄像头已关闭")

    def reset_stats(self):
        self.emotion_counts.clear()
        self.detection_records.clear()
        reset_warning_history()
        self.chart.update_chart(self.emotion_counts, force=True)  # 强制刷新清空图表
        self.warning_label.setText("情绪状态：正常")
        self.warning_label.setStyleSheet("color: green;")
        QMessageBox.information(self, "提示", "所有统计数据已重置！")

    def save_records(self):
        if not self.detection_records:
            QMessageBox.warning(self, "提示", "没有检测记录可保存！")
            return

        filename = f"情绪检测记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['检测时间', '当前情绪', 'AI分析建议'])
                writer.writerows(self.detection_records)
            QMessageBox.information(self, "保存成功", f"检测记录已保存到：\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"错误信息：{str(e)}")

    def update_frame(self):
        start_time = time.time()

        ret, frame = self.cap.read()
        if not ret:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.MAX_CONSEC_FAILURES:
                QMessageBox.critical(self, "错误", "摄像头连接丢失，即将停止检测。")
                self.stop_detection()
            return
        else:
            self.consecutive_failures = 0

        frame = cv2.flip(frame, 1)

        # 提交检测任务（不阻塞UI）
        self.worker.submit(frame)

        # 实时更新视频画面
        self._update_video_display(frame)
        self.update_status_bar(start_time)

    def on_emotion_detected(self, emotion):
        """该函数在主线程执行，安全更新UI"""
        self.emotion_counts[emotion] += 1
        analysis = analyze_emotion(emotion)
        warning_text = check_warning(emotion)

        if warning_text:
            self.warning_label.setText(f"⚠️ 预警：{warning_text}")
            self.warning_label.setStyleSheet("color: red; font-weight: bold;")
            speak_async(warning_text)
        else:
            self.warning_label.setText("情绪状态：正常")
            self.warning_label.setStyleSheet("color: green;")

        self.emotion_label.setText(f"当前情绪：{emotion}")
        if analysis:
            self.analysis_label.setText(f"AI分析：{analysis}")
            self.detection_records.append([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                emotion,
                analysis
            ])

        self.chart.update_chart(self.emotion_counts)

    def _update_video_display(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        scaled = QPixmap.fromImage(qt_image).scaled(
            self.video_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.video_label.setPixmap(scaled)

    def update_status_bar(self, start_time):
        detect_time = (time.time() - start_time) * 1000
        self.detect_time_label.setText(f"检测耗时: {detect_time:.1f} ms")

        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_fps_time >= 1:
            fps = self.frame_count / (current_time - self.last_fps_time)
            self.fps_label.setText(f"帧率: {fps:.1f} FPS")
            self.frame_count = 0
            self.last_fps_time = current_time

    def closeEvent(self, event):
        self.stop_detection()
        self.executor.shutdown(wait=False)
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = EmotionSystem()
    window.show()
    sys.exit(app.exec_())