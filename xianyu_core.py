import hashlib
import json
import re
import urllib.parse
import requests
import time

# 禁用 SSL 警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API = "mtop.idle.wx.user.profile.update"
APP_KEY = "12574478"
BASE_URL = "https://acs.m.goofish.com/h5/mtop.idle.wx.user.profile.update/1.0/"

def extract_from_request(request_text: str) -> dict:
    """带类型防护的解析器"""
    # 强制将输入转换为字符串
    text = str(request_text)
    info = {"cookies": {}, "headers": {}, "utdid": None, "m_h5_tk": None}
    
    # 1. 解析 x-smallstc
    stc_match = re.search(r'x-smallstc: (\{.*?\})', text)
    if stc_match:
        try:
            stc_json = json.loads(stc_match.group(1))
            info["cookies"] = {k: str(v) for k, v in stc_json.items() if k in ['cookie2', 'sid', 'sgcookie']}
            info["m_h5_tk"] = stc_json.get('cookie2', '') # 闲鱼小程序通常把 Token 存在 cookie2
        except: pass

    # 2. 解析 data
    data_match = re.search(r'data=(.*)', text)
    if data_match:
        decoded_data = urllib.parse.unquote(str(data_match.group(1)))
        try:
            data_dict = json.loads(decoded_data)
            info["utdid"] = data_dict.get("utdid")
        except: pass

    # 3. 提取 Header
    for h in ["bx-umidtoken", "x-ticid", "mini-janus", "bx-ua"]:
        match = re.search(rf'{h}: (.*?)\n', text, re.IGNORECASE)
        if match: info["headers"][h] = match.group(1).strip()
            
    return info

def update_avatar(image_url: str, auth_info: dict):
    data_str = json.dumps({
        "utdid": auth_info.get("utdid"),
        "platform": "windows",
        "profileCode": "avatar",
        "profileImageUrl": image_url
    }, separators=(",", ":"), ensure_ascii=False)
    
    t = str(int(time.time() * 1000))
    # 签名计算
    token = auth_info.get("m_h5_tk", "").split('_')[0]
    sign = hashlib.md5(f"{token}&{t}&{APP_KEY}&{data_str}".encode()).hexdigest()
    
    params = {"appKey": APP_KEY, "t": t, "sign": sign, "api": API, "dataType": "json"}
    headers = {**auth_info.get("headers", {}), "Content-Type": "application/x-www-form-urlencoded"}
    
    response = requests.post(
        f"{BASE_URL}?{urllib.parse.urlencode(params)}",
        data={"data": data_str},
        headers=headers,
        cookies=auth_info.get("cookies", {}),
        verify=False
    )
    return response.json()
