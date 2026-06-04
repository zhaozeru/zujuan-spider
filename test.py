# import requests
# import json
#
# url = "https://api.yygu.cn/v6/edu/exam/review"
#
# payload = json.dumps({
#     "timeout_set": 600,
#     "request": {
#         "question_images": [
#             {
#                 "db_image_id": 1767,
#                 "image_url": "https://s3.i.yygu.cn:58081/test-dataset/catapi-client-resources/试卷原图.jpg",
#                 "page_num": 1
#             }
#         ],
#         "conf": {
#             "expand_question_region": False,
#             "reserved_answer_area": False
#         }
#     }
# })
# headers = {
#   'Authorization': 'yg-1e3056c966a423260c14f60b0f9f94a5',
#   'Content-Type': 'application/json'
# }
#
# response = requests.request("POST", url, headers=headers, data=payload)
#


import urllib.request
import json

API_URL = "http://localhost:8088/api/console/chat"
AGENT_ID = "default"
AUTH_TOKEN = ""  # 如果启用了认证，在这里设置你的 token

def chat_with_agent(message, session_id="1779521432129"):
    # 准备请求
    headers = {
        "Content-Type": "application/json",
        "X-Agent-Id": AGENT_ID
    }

    # 如果有 auth token，添加到请求头
    if AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"

    data = {
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": message
                    }
                ]
            }
        ],
        "session_id": session_id,
        "user_id": "python-user",
        "channel": "console"
    }

    # 发送请求
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='POST'
    )

    # 处理流式响应
    try:
        with urllib.request.urlopen(request) as response:
            for line in response:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    event_data = json.loads(line[6:])  # 去掉 'data: ' 前缀

                    # 打印状态
                    # status = event_data.get('status')
                    # print(f"状态: {status}")

                    # 提取回复内容
                    if event_data.get('output'):
                        for item in event_data['output']:
                            if item.get('role') == 'assistant':
                                for content in item.get('content', []):
                                    if content.get('type') == 'text':
                                        print(f"回复: {content.get('text')}")

                    # 检查错误
                    if event_data.get('error'):
                        error = event_data['error']
                        print(f"错误: {error.get('message')}")

    except urllib.error.HTTPError as e:
        print(f"HTTP 错误: {e.code} - {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"错误: {e}")

# 使用示例
if __name__ == "__main__":
    # chat_with_agent("你好，请介绍一下自己")
    chat_with_agent("如果我通过RESTfulAPI来调用你，你具备调用绑定的skill和插件的能力吗？")
