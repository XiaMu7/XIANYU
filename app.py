#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import json
import mimetypes
import time
import sys
import re
import urllib.parse
from urllib.parse import urlparse, urlencode, parse_qs
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3

# 禁用SSL警告与验证
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 全局配置
API = "mtop.idle.wx.user.profile.update"
APP_KEY = "12574478"
BASE_URL = "https://acs.m.goofish.com/h5/mtop.idle.wx.user.profile.update/1.0/"
UPLOAD_URL = "https://stream-upload.goofish.com/api/upload.api"
CURRENT_M_H5_TK = "717336018584e9c7c54f266f5db96fca_1772912434028"

session = requests.Session()
session.verify = False

def calc_sign(token: str, t: str, app_key: str, data_str: str) -> str:
    """计算 Mtop 签名"""
    raw = f"{token}&{t}&{app_key}&{data_str}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()

def extract_from_request(request_text: str) -> dict:
    """从原始请求文本中提取完整的上下文信息"""
    info = {"cookies": {}, "headers": {}, "data": {}, "utdid": None}
    lines = request_text.strip().split('\n')
    for line in lines:
        if ': ' in line:
            key, value = line.split(': ', 1)
            info["headers"][key.strip()] = value.strip()
            if key.lower() == 'cookie':
                for pair in value.split('; '):
                    if '=' in pair:
                        k, v = pair.split('=', 1)
                        info["cookies"][k] = v
        elif line.startswith('data='):
            data_str = urllib.parse.unquote(line[5:])
            try:
                info["data"] = json.loads(data_str)
                info["utdid"] = info["data"].get("utdid")
            except: pass
    return info

def update_avatar(image_url: str, auth_info: dict) -> dict:
    """调用头像更新接口"""
    global CURRENT_M_H5_TK
    
    # 动态获取 Token
    token = CURRENT_M_H5_TK.split('_')[0]
    t = str(int(time.time() * 1000))
    
    data_obj = {
        "utdid": auth_info.get("utdid"),
        "platform": "mac",
        "profileCode": "avatar",
        "profileImageUrl": image_url
    }
    data_str = json.dumps(data_obj, separators=(",", ":"), ensure_ascii=False)
    sign = calc_sign(token, t, APP_KEY, data_str)
    
    params = {"jsv": "2.4.12", "appKey": APP_KEY, "t": t, "sign": sign, "v": "1.0", "api": API}
    cookies = {**auth_info.get("cookies", {}), "_m_h5_tk": CURRENT_M_H5_TK}
    
    response = session.post(f"{BASE_URL}?{urlencode(params)}", cookies=cookies, data={"data": data_str})
    
    # 自动更新 Token
    if '_m_h5_tk' in response.cookies:
        CURRENT_M_H5_TK = response.cookies['_m_h5_tk']
        
    return response.json()

def upload_to_xianyu(file_url: str, auth_info: dict) -> str:
    """上传图片至闲鱼图床"""
    img_resp = session.get(file_url, stream=True)
    files = {"file": ("avatar.jpg", img_resp.content, "image/jpeg")}
    data = {"appkey": "fleamarket", "bizCode": "fleamarket"}
    
    resp = session.post(UPLOAD_URL, files=files, data=data, cookies=auth_info["cookies"])
    body = resp.json()
    return body.get("object", {}).get("url")

# 

def main():
    print("🐟 闲鱼头像助手已启动...")
    img_url = input("输入图片URL: ").strip()
    req_text = input("粘贴完整请求信息 (输入END结束):\n") # 这里简化了交互逻辑
    
    auth = extract_from_request(req_text)
    
    try:
        print("🚀 正在同步头像...")
        final_url = upload_to_xianyu(img_url, auth)
        res = update_avatar(final_url, auth)
        
        if "SUCCESS" in str(res.get("ret", "")):
            print("✅ 更新成功！")
        else:
            print(f"❌ 更新失败: {res}")
            
    except Exception as e:
        print(f"💥 发生错误: {e}")

if __name__ == "__main__":
    main()
