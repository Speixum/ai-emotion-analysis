import os
from dashscope import Generation
import dashscope
import time
import threading


class QwenAPIManager:
    def __init__(self):
        self.api_key = os.environ.get("DASHSCOPE_API_KEY", "")
        self.last_call_time = 0
        self.MIN_CALL_INTERVAL = 3
        self.lock = threading.Lock()

        # 初始化时检查API_KEY
        if not self.api_key:
            print("⚠️ 警告：未设置DASHSCOPE_API_KEY环境变量，AI分析功能将不可用")
            print("   请在系统环境变量中添加DASHSCOPE_API_KEY，或直接修改本文件中的api_key")

        dashscope.api_key = self.api_key

    def analyze_emotion(self, emotion):
        if not self.api_key:
            return "AI分析已禁用（未配置API_KEY）"

        with self.lock:
            current_time = time.time()
            if current_time - self.last_call_time < self.MIN_CALL_INTERVAL:
                return None

            self.last_call_time = current_time

        try:
            response = Generation.call(
                model='qwen-turbo',
                messages=[
                    {
                        "role": "user",
                        "content": f"用户当前的情绪是：{emotion}\n\n请生成一句简短、温暖、有同理心的情绪分析和建议，不超过30个字。不要使用过于正式的语言，语气要亲切自然。"
                    }
                ],
                temperature=0.7,
                max_tokens=50
            )

            if response.status_code == 200:
                return response.output.choices[0].message.content.strip()
            else:
                print(f"API调用失败: 状态码 {response.status_code}")
                return "AI分析暂时不可用"

        except Exception as e:
            print(f"大模型调用出错: {e}")
            return "AI分析暂时不可用，请检查网络"


# 全局单例
qwen_manager = QwenAPIManager()


def analyze_emotion(emotion):
    return qwen_manager.analyze_emotion(emotion)