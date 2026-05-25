import pyttsx3
import threading
import queue


class VoiceManager:
    def __init__(self):
        self.speech_queue = queue.Queue(maxsize=10)
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.running = True
        self.worker_thread.start()

    def _worker(self):
        # 在播放线程内初始化引擎，保证线程安全
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.setProperty('volume', 0.8)
        except Exception as e:
            print(f"语音引擎初始化失败: {e}")
            engine = None

        while self.running:
            try:
                text = self.speech_queue.get(timeout=1)
                if engine:
                    try:
                        engine.say(text)
                        engine.runAndWait()
                    except Exception as e:
                        print(f"语音播报出错: {e}")
                self.speech_queue.task_done()
            except queue.Empty:
                continue

    def speak_async(self, text):
        try:
            self.speech_queue.put_nowait(text)
        except queue.Full:
            print("语音队列已满，跳过本次播报")

    def shutdown(self):
        self.running = False
        # 等待线程自然退出
        if self.worker_thread:
            self.worker_thread.join(timeout=2)


# 全局单例
voice_manager = VoiceManager()

def speak_async(text):
    voice_manager.speak_async(text)