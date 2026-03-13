#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import json
import time
import requests
import urllib3
import re
from urllib.parse import urlencode, parse_qs

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 全局配置
API = "mtop.idle.wx.user.profile.update"
APP_KEY = "12574478"
BASE_URL = "https://acs.m.goofish.com/h5/mtop.idle.wx.user.profile.update/1.0/"
UPLOAD_URL = "https://stream-upload.goofish.com/api/upload.api"

# 初始 Token (运行时会自动覆盖)
CURRENT_M_H5_TK = "717336018584e9c7c54f266f5db96fca_1772912434028"

def sync_token(response):
    """从服务器响应中同步最新的 Token"""
    global CURRENT_M_H5_TK
    new_tk = response.cookies.get('_m_h5_tk')
    if new_tk and new_tk != CURRENT_M_H5_TK:
        print(f"🔄 [自动同步] 更新 Token: {new_tk[:15]}...")
        CURRENT_M_H5_TK = new_tk

def upload_bytes(file_name, file_bytes, mime, auth_info):
    """上传图片并同步状态"""
    cookies = auth_info.get("cookies", {}).copy()
    cookies["_m_h5_tk"] = CURRENT_M_H5_TK
    
    files = {"file": (file_name, file_bytes, mime)}
    data = {"bizCode": "fleamarket", "appkey": "fleamarket"}
    
    response = requests.post(UPLOAD_URL, files=files, data=data, cookies=cookies, verify=False)
    sync_token(response) # 必须在上传后同步
    
    body = response.json()
    if not body.get("success"):
        raise RuntimeError(f"上传失败: {body}")
    return body["object"]["url"]

def update_avatar(image_url, auth_info):
    """更新头像并同步状态"""
    global CURRENT_M_H5_TK
    token = CURRENT_M_H5_TK.split('_')[0]
    t = str(int(time.time() * 1000))
    
    data_str = json.dumps({"utdid": auth_info["utdid"], "profileImageUrl": image_url}, separators=(",", ":"))
    sign = hashlib.md5(f"{token}&{t}&{APP_KEY}&{data_str}".encode()).hexdigest()
    
    params = {"appKey": APP_KEY, "t": t, "sign": sign, "api": API, "type": "originaljson"}
    cookies = auth_info.get("cookies", {}).copy()
    cookies["_m_h5_tk"] = CURRENT_M_H5_TK
    
    response = requests.post(f"{BASE_URL}?{urlencode(params)}", data={"data": data_str}, cookies=cookies, verify=False)
    sync_token(response) # 必须在更新后同步
    return response.json()

# 

def main():
    print("=== 闲鱼头像自动更新 (自动保鲜版) ===")
    image_url = input("输入图片链接: ").strip()
    
    print("\n请粘贴完整请求文本 (最后一行输入 END):")
    lines = []
    while True:
        line = input()
        if line == "END": break
        lines.append(line)
    
    # 这里嵌入你之前的解析逻辑，确保 auth_info 结构包含 cookies 和 utdid
    # ... (调用你的 extract_from_request)
    
    try:
        final_url = upload_bytes("avatar.jpg", b"...", "image/jpeg", auth_info)
        result = update_avatar(final_url, auth_info)
        print("执行结果:", result)
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    main()
