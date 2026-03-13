#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import json
import re
import urllib.parse
import requests
import time
import sys

# 禁用 SSL 警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API = "mtop.idle.wx.user.profile.update"
APP_KEY = "12574478"
BASE_URL = "https://acs.m.goofish.com/h5/mtop.idle.wx.user.profile.update/1.0/"

def extract_from_request(request_text: str) -> dict:
    """完美解析小程序格式的 HTTP 请求文本"""
    info = {"cookies": {}, "headers": {}, "utdid": None, "token": None}
    
    # 1. 提取 x-smallstc 中的关键 Session 信息
    stc_match = re.search(r'x-smallstc: (\{.*?\})', request_text)
    if stc_match:
        try:
            stc_json = json.loads(stc_match.group(1))
            # 将核心凭证存入 cookies
            info["cookies"] = {k: v for k, v in stc_json.items() if k in ['cookie2', 'sid', 'unb', 'sgcookie']}
            # 提取 token
            if 'cookie2' in stc_json:
                info["token"] = stc_json['cookie2'].split('_')[0]
        except: pass

    # 2. 解码 URL 编码的 data 字段
    data_match = re.search(r'data=(.*)', request_text)
    if data_match:
        decoded_data = urllib.parse.unquote(data_match.group(1))
        try:
            data_dict = json.loads(decoded_data)
            info["utdid"] = data_dict.get("utdid")
        except: pass

    # 3. 抓取必要 Header
    for h in ["bx-umidtoken", "x-ticid", "mini-janus", "bx-ua", "sgcookie"]:
        match = re.search(rf'{h}: (.*?)\n', request_text, re.IGNORECASE)
        if match: info["headers"][h] = match.group(1).strip()
            
    return info

def update_avatar(image_url: str, auth_info: dict):
    """执行更新"""
    data_str = json.dumps({
        "utdid": auth_info["utdid"],
        "platform": "windows",
        "miniAppVersion": "9.9.9",
        "profileCode": "avatar",
        "profileImageUrl": image_url
    }, separators=(",", ":"), ensure_ascii=False)
    
    t = str(int(time.time() * 1000))
    # 签名计算（注意：这里的 token 通常对应 cookie2 的一部分）
    sign = hashlib.md5(f"{auth_info.get('token', '')}&{t}&{APP_KEY}&{data_str}".encode()).hexdigest()
    
    params = {"appKey": APP_KEY, "t": t, "sign": sign, "api": API, "dataType": "json"}
    headers = {**auth_info["headers"], "Content-Type": "application/x-www-form-urlencoded"}
    
    response = requests.post(
        f"{BASE_URL}?{urllib.parse.urlencode(params)}",
        data={"data": data_str},
        headers=headers,
        cookies=auth_info["cookies"],
        verify=False
    )
    return response.json()

# --- 执行入口 ---
if __name__ == "__main__":
    print("请粘贴完整的请求文本（输入 END 结束）：")
    lines = []
    while True:
        line = sys.stdin.readline()
        if line.strip() == "END": break
        lines.append(line)
    
    request_text = "\n".join(lines)
    auth = extract_from_request(request_text)
    
    if auth["utdid"]:
        print(f"✅ 解析成功，UTDID: {auth['utdid']}")
        new_url = input("输入新图片 URL: ")
        res = update_avatar(new_url, auth)
        print("响应结果:", res)
    else:
        print("❌ 解析失败，请检查粘贴的内容是否包含 data= 和 x-smallstc")
