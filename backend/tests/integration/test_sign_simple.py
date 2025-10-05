"""
简单测试签名SDK
"""
import json
from app.services.sign_meitu import Signer

# 测试参数
key = "your_key_here"
secret = "your_secret_here"

url = "https://openapi.meitu.com/api/v1/sdk/sync/push"
method = "POST"

headers = {
    "Content-Type": "application/json",
    "Host": "openapi.meitu.com",
    "X-Sdk-Content-Sha256": "UNSIGNED-PAYLOAD"
}

body_data = {
    "params": json.dumps({
        "parameter": {
            "sr_num": 2,
            "area_size": 1920
        }
    }),
    "init_images": [
        {
            "url": "https://wheeai.meitudata.com/static/666162c4139073547bhMUcLeee3093.jpeg",
            "profile": {
                "media_profiles": {
                    "media_data_type": "url"
                }
            }
        }
    ],
    "task": "/v1/Ultra_High_Definition_V2/478332",
    "task_type": "formula",
    "sync_timeout": 30,
    "rsp_media_type": "url"
}

body = json.dumps(body_data, separators=(',', ':'))

print("=" * 60)
print("测试签名SDK")
print("=" * 60)

print("\n原始Headers:")
print(json.dumps(headers, indent=2))

# 创建签名器
signer = Signer(key, secret)

# 签名
print("\n正在签名...")
result = signer.sign(url, method, headers, body)

print("\n签名后的Headers:")
print(json.dumps(headers, indent=2))

print("\n返回的对象类型:", type(result))
print("返回对象的属性:", dir(result))

print("\n" + "=" * 60)
print("签名完成")
print("=" * 60)
