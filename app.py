#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import json
import time
import requests
import urllib.parse
import urllib3
from urllib.parse import urlencode

# 禁用SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

session = requests.Session()
session.verify = False

API = "mtop.idle.wx.user.profile.update"
APP_KEY = "12574478"
BASE_URL = "https://acs.m.goofish.com/h5/mtop.idle.wx.user.profile.update/1.0/"
UPLOAD_URL = "https://stream-upload.goofish.com/api/upload.api"

def extract_from_request(request_text: str) -> dict:
    """从你的原始请求文本中提取所有关键Header和Cookie"""
    info = {"cookies": {}, "headers": {}, "data": {}, "utdid": None}
    lines = request_text.strip().split('\n')
    
    for line in lines:
        if ': ' in line:
            key, value = line.split(': ', 1)
            k, v = key.strip(), value.strip()
            info["headers"][k] = v
            # 解析x-smallstc中的重要凭证
            if k.lower() == 'x-smallstc':
                try:
                    stc = json.loads(v)
                    info["cookies"].update({k: str(v) for k, v in stc.items() if k in ['sid', 'cookie2', 'sgcookie', 'csg']})
                except: pass
        if 'data=' in line:
            data_str = urllib.parse.unquote(line.split('data=')[1])
            info["data"] = json.loads(data_str)
            info["utdid"] = info["data"].get("utdid")
            
    return info

def upload_to_xianyu(image_url: str, auth_info: dict) -> str:
    """复用微信小程序环境进行上传"""
    img_resp = session.get(image_url, verify=False)
    
    # 构建与你成功请求一致的Headers
    headers = {
        "User-Agent": auth_info["headers"].get("user-agent"),
        "bx-umidtoken": auth_info["headers"].get("bx-umidtoken"),
        "x-ticid": auth_info["headers"].get("x-ticid"),
        "mini-janus": auth_info["headers"].get("mini-janus"),
        "x-tap": auth_info["headers"].get("x-tap"),
        "sgcookie": auth_info["headers"].get("sgcookie"),
        "xweb_xhr": "1",
        "Referer": "https://servicewechat.com/wx9882f2a891880616/74/page-frame.html"
    }
    
    files = {"file": ("avatar.jpg", img_resp.content, "image/jpeg")}
    data = {"appkey": "fleamarket", "bizCode": "fleamarket"}
    
    resp = session.post(UPLOAD_URL, files=files, data=data, headers=headers, cookies=auth_info["cookies"])
    return resp.json().get("object", {}).get("url")

def update_avatar(final_url: str, auth_info: dict):
    """更新头像接口"""
    t = str(int(time.time() * 1000))
    data_obj = {"utdid": auth_info["utdid"], "platform": "windows", "profileCode": "avatar", "profileImageUrl": final_url}
    data_str = json.dumps(data_obj, separators=(",", ":"), ensure_ascii=False)
    
    # 这里sign需要你根据 token 生成，保持原有逻辑即可
    params = {"jsv": "2.4.12", "appKey": APP_KEY, "t": t, "api": API, "v": "1.0"}
    
    resp = session.post(f"{BASE_URL}?{urlencode(params)}", 
                        headers={"User-Agent": auth_info["headers"].get("user-agent")},
                        cookies=auth_info["cookies"], 
                        data={"data": data_str})
    return resp.json()

# --- 执行主程序 ---
if __name__ == "__main__":
    req_raw = input("请粘贴你刚才发出的完整请求信息:\n")
    img_url = input("请输入图片URL:\n")
    
    auth = extract_from_request(req_raw)
    final_url = upload_to_xianyu(img_url, auth)
    print(f"上传成功，链接: {final_url}")
    res = update_avatar(final_url, auth)
    print(res)
