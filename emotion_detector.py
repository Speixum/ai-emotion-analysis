from deepface import DeepFace
import tensorflow as tf
import os
import threading

# 屏蔽TensorFlow日志
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
tf.get_logger().setLevel('ERROR')

# 模型懒加载
_model = None
_model_lock = threading.Lock()
_model_loaded = False


def _load_model():
    global _model, _model_loaded
    with _model_lock:
        if not _model_loaded:
            print("=" * 50)
            print("正在加载DeepFace表情识别模型...")
            try:
                _model = DeepFace.build_model("Emotion")
                print("模型加载完成！系统准备就绪。")
            except Exception as e:
                print(f"模型加载失败: {e}")
                print("请检查网络连接，DeepFace需要下载预训练模型")
                _model = None
            print("=" * 50)
            _model_loaded = True


def detect_emotion(frame):
    # 第一次调用时才加载模型
    if not _model_loaded:
        _load_model()

    if _model is None:
        return "neutral"

    try:
        results = DeepFace.analyze(
            frame,
            actions=['emotion'],
            enforce_detection=False,
            detector_backend='opencv',
            silent=True
        )

        if isinstance(results, list) and len(results) > 0:
            return results[0].get('dominant_emotion', 'neutral')
        elif isinstance(results, dict):
            return results.get('dominant_emotion', 'neutral')
        else:
            return 'neutral'

    except ValueError as e:
        print(f"DeepFace参数错误: {e}")
        return "neutral"
    except RuntimeError as e:
        print(f"模型运行错误: {e}")
        return "neutral"
    except Exception as e:
        print(f"未知识别错误: {e}")
        return "neutral"