import hashlib
import json
import re
import urllib.parse
import requests
from urllib.parse import urlencode

# 全局配置
API = "mtop.idle.wx.user.profile.update"
APP_KEY = "12574478"
BASE_URL = "https://acs.m.goofish.com/h5/mtop.idle.wx.user.profile.update/1.0/"

def extract_from_request(request_text: str) -> dict:
    """自动解析完整的 HTTP 请求文本，提取关键 Token 和 UTDID"""
    info = {"cookies": {}, "headers": {}, "utdid": None, "m_h5_tk": None}
    
    # 1. 提取 Cookies
    cookie_match = re.search(r'cookie: (.*?)\n', request_text, re.IGNORECASE)
    if cookie_match:
        for item in cookie_match.group(1).split(';'):
            if '=' in item:
                k, v = item.strip().split('=', 1)
                info["cookies"][k] = v
                if k == '_m_h5_tk': info["m_h5_tk"] = v

    # 2. 提取并解码 Data 字段
    data_match = re.search(r'data=(.*)', request_text)
    if data_match:
        decoded_data = urllib.parse.unquote(data_match.group(1))
        try:
            data_json = json.loads(decoded_data)
            info["utdid"] = data_json.get("utdid")
        except: pass

    # 3. 提取所有特殊请求头 (防止验证失败)
    for h in ["bx-umidtoken", "x-ticid", "mini-janus", "sgcookie", "bx-ua"]:
        match = re.search(rf'{h}: (.*?)\n', request_text, re.IGNORECASE)
        if match: info["headers"][h] = match.group(1).strip()
            
    return info

def update_avatar(image_url: str, auth_info: dict) -> dict:
    """执行最终的头像更新请求"""
    token = auth_info["m_h5_tk"].split('_')[0]
    t = str(int(time.time() * 1000))
    data_str = json.dumps({
        "utdid": auth_info["utdid"],
        "platform": "windows",
        "profileCode": "avatar",
        "profileImageUrl": image_url
    }, separators=(",", ":"), ensure_ascii=False)
    
    sign = hashlib.md5(f"{token}&{t}&{APP_KEY}&{data_str}".encode()).hexdigest()
    params = {"appKey": APP_KEY, "t": t, "sign": sign, "api": API, "dataType": "json"}
    
    # 构建请求
    session = requests.Session()
    session.headers.update(auth_info["headers"])
    response = session.post(
        f"{BASE_URL}?{urlencode(params)}",
        data={"data": data_str},
        cookies=auth_info["cookies"]
    )
    return response.json()
