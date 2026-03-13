#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import json
import time
import requests
import urllib.parse
import urllib3
from urllib.parse import urlencode

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
session = requests.Session()
session.verify = False

API = "mtop.idle.wx.user.profile.update"
APP_KEY = "12574478"
BASE_URL = "https://acs.m.goofish.com/h5/mtop.idle.wx.user.profile.update/1.0/"
UPLOAD_URL = "https://stream-upload.goofish.com/api/upload.api"

def calc_sign(token: str, t: str, app_key: str, data_str: str) -> str:
    """计算 Mtop 签名，没有它，接口会拒绝访问"""
    raw = f"{token}&{t}&{app_key}&{data_str}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()

def extract_from_request(request_text: str) -> dict:
    info = {"cookies": {}, "headers": {}, "data": {}, "utdid": None, "token": ""}
    lines = request_text.strip().split('\n')
    for line in lines:
        if ': ' in line:
            key, value = line.split(': ', 1)
            info["headers"][key.strip()] = value.strip()
            if key.strip().lower() == 'cookie':
                for pair in value.split('; '):
                    if '=' in pair:
                        k, v = pair.split('=', 1)
                        info["cookies"][k] = v
                        if k == '_m_h5_tk': info["token"] = v.split('_')[0]
        if 'data=' in line:
            info["data"] = json.loads(urllib.parse.unquote(line.split('data=')[1]))
            info["utdid"] = info["data"].get("utdid")
    return info

def upload_to_xianyu(image_url: str, auth_info: dict) -> str:
    img_resp = session.get(image_url, verify=False)
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
    result = resp.json()
    if not result.get("success"):
        raise Exception(f"上传失败: {result}")
    return result["object"]["url"]

def update_avatar(final_url: str, auth_info: dict):
    t = str(int(time.time() * 1000))
    data_obj = {"utdid": auth_info["utdid"], "platform": "windows", "profileCode": "avatar", "profileImageUrl": final_url}
    data_str = json.dumps(data_obj, separators=(",", ":"), ensure_ascii=False)
    
    # 【修复核心点】：必须生成正确的 sign
    sign = calc_sign(auth_info["token"], t, APP_KEY, data_str)
    
    params = {"jsv": "2.4.12", "appKey": APP_KEY, "t": t, "sign": sign, "api": API, "v": "1.0", "type": "originaljson"}
    
    resp = session.post(f"{BASE_URL}?{urlencode(params)}", 
                        headers={"User-Agent": auth_info["headers"].get("user-agent")},
                        cookies=auth_info["cookies"], 
                        data={"data": data_str})
    return resp.json()

if __name__ == "__main__":
    req_raw = input("请粘贴完整请求信息:\n")
    img_url = input("请输入图片URL:\n")
    auth = extract_from_request(req_raw)
    try:
        final_url = upload_to_xianyu(img_url, auth)
        print(f"✅ 上传成功: {final_url}")
        res = update_avatar(final_url, auth)
        print(f"🔄 更新结果: {res}")
    except Exception as e:
        print(f"❌ 错误: {e}")
