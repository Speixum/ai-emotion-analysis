from collections import deque
import time
import threading


class WarningManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init()
            return cls._instance

    def _init(self):
        self.emotion_history = deque(maxlen=30)
        self.last_warning_time = 0
        self.WARNING_COOLDOWN = 10
        self.lock = threading.Lock()

    def check_warning(self, emotion):
        with self.lock:
            self.emotion_history.append(emotion)

            sad_count = self.emotion_history.count("sad")
            angry_count = self.emotion_history.count("angry")

            current_time = time.time()
            if current_time - self.last_warning_time < self.WARNING_COOLDOWN:
                return None

            if sad_count >= 15:
                self.last_warning_time = current_time
                return "检测到您长时间情绪低落，建议起身活动一下"

            if angry_count >= 15:
                self.last_warning_time = current_time
                return "检测到您情绪比较激动，请深呼吸保持冷静"

            return None

    def reset_history(self):
        with self.lock:
            self.emotion_history.clear()
            self.last_warning_time = 0


# 全局单例
warning_manager = WarningManager()


def check_warning(emotion):
    return warning_manager.check_warning(emotion)


def reset_warning_history():
    warning_manager.reset_history()