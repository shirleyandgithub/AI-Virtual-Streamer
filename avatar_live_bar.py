# encoding=utf-8

import time
import random
import asyncio

# 配置片段
BEATS = [
    {"text": "大家好，欢迎来到直播间！今天介绍一款酱香型白酒。", "dur": 8, "allow_insert": False},
    {"text": "这款酒入口绵柔、回味悠长，适合宴席与送礼。", "dur": 10, "allow_insert": True},
    {"text": "它是53度，来自贵州产区，工艺传统且稳定。", "dur": 10, "allow_insert": True},
    {"text": "现在下单有优惠，详情点击购买链接查看。", "dur": 8, "allow_insert": False},
]
FAQ = {
    "价格": "价格见下方购买链接，活动价更实惠哦。",
    "度数": "这款是53度的酱香型白酒。",
    "产地": "来自贵州酱香产区，工艺稳定。",
}

MAX_ANSWERS_PER_30S = 2
USER_COOLDOWN = 60  # s

# 状态
answer_times = []
user_last_time = {}

qa_queue = asyncio.Queue()  # 待回答队列（已判定需要回答的弹幕塞进来）

# 分类与决策
def decide_action(user_id: str, text: str):
    # 安全拦截
    for bad in ["辱骂", "违法"]:
        if bad in text:
            return ("IGNORE", None, "safety")
    # 相关性（看是否出现酒/度数/价格等词）
    related_keys = ["酒", "度数", "价格", "产地", "口感", "优惠"]
    if not any(k in text for k in related_keys):
        return ("IGNORE", None, "irrelevant")
    # 判断是否命中FAQ
    for k, ans in FAQ.items():
        if k in text:
            return ("ANSWER", ans, f"faq:{k}")
    # 开放问答（这里用固定模板代替LLM）
    short = f"关于“{text}”，您可以查看商品详情页的参数说明哦。"
    return ("ANSWER", short, "openqa")

def rate_limited(user_id: str):
    # 用户冷却
    now = time.time()
    last = user_last_time.get(user_id, 0)
    if now - last < USER_COOLDOWN:
        return True
    # 30s限速
    global answer_times
    answer_times = [t for t in answer_times if now - t < 30]
    return len(answer_times) >= MAX_ANSWERS_PER_30S

# 合成器（代替TTS + 驱动命令）
async def synth_and_render(text: str, clip_name: str):
    # 用sleep代替真实生成
    print(f"[TTS] {text}")
    await asyncio.sleep(min(3, max(1, len(text)//10)))  # 模拟合成时长
    print(f"[VIDEO] render {clip_name}.mp4 (Wav2Lip/LivePortrait)")
    await asyncio.sleep(1)
    return f"{clip_name}.mp4"

# 主讲轨
async def main_script_player():
    for i, beat in enumerate(BEATS):
        print(f"\n[MAIN] ▶ {beat['text']}")
        start = time.time()
        while time.time() - start < beat["dur"]:
            # 允许插播：给答疑轨机会抢占
            if beat["allow_insert"] and not qa_queue.empty():
                item = await qa_queue.get()
                print(f"[MAIN] ⏸ 暂停主讲，插播答疑：{item}")
                vid = await synth_and_render(item["answer"], f"ans_{item['id']}")
                print(f"[MAIN] ⏺ 插播结束，继续主讲")
            await asyncio.sleep(0.2)
        print(f"[MAIN] ⏭ 结束本段（{beat['dur']}s）")

# 弹幕消费者 -> 决策 -> 入队
async def chat_consumer():
    # 模拟弹幕流
    demo_msgs = [
        {"uid": "u1", "text": "多少钱啊？能便宜点吗"},
        {"uid": "u2", "text": "度数是多少？"},
        {"uid": "u3", "text": "唱个歌呗"},
        {"uid": "u1", "text": "产地在哪里？"},
        {"uid": "u4", "text": "这酒适合女生喝吗"},
    ]
    for m in demo_msgs:
        await asyncio.sleep(random.uniform(2, 6))  # 模拟随机到达
        action, ans, reason = decide_action(m["uid"], m["text"])
        print(f"[CHAT] 收到：{m} → {action} ({reason})")
        if action == "ANSWER" and ans and not rate_limited(m["uid"]):
            user_last_time[m["uid"]] = time.time()
            answer_times.append(time.time())
            await qa_queue.put({"id": f"{m['uid']}_{int(time.time())}", "answer": ans})
        else:
            print("[CHAT] 忽略或被限流")

# 入口
async def main():
    await asyncio.gather(
        main_script_player(),
        chat_consumer(),
    )

if __name__ == "__main__":
    asyncio.run(main())



