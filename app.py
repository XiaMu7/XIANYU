#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import json
import time
import requests
import urllib.parse
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 配置项 ---
API = "mtop.idle.wx.user.profile.update"
APP_KEY = "12574478"
BASE_URL = "https://acs.m.goofish.com/h5/mtop.idle.wx.user.profile.update/1.0/"
UPLOAD_URL = "https://stream-upload.goofish.com/api/upload.api"

def get_sign(token, t, app_key, data):
    """生成 Mtop 签名"""
    raw = f"{token}&{t}&{app_key}&{data}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()

def run_task():
    # 1. 引导用户粘贴抓取的完整 Headers
    print("请粘贴从微信开发者工具/抓包软件获取的完整请求头（按两下回车结束）：")
    raw_headers = ""
    while True:
        line = input()
        if not line: break
        raw_headers += line + "\n"
    
    img_url = input("请输入你想设置的头像图片URL: ").strip()

    # 2. 解析 Header
    headers = {}
    cookies = {}
    for line in raw_headers.strip().split('\n'):
        if ': ' in line:
            k, v = line.split(': ', 1)
            headers[k.strip()] = v.strip()
            if k.strip().lower() == 'cookie':
                for pair in v.split('; '):
                    if '=' in pair:
                        ck, cv = pair.split('=', 1)
                        cookies[ck] = cv

    # 提取 utdid 和 token
    token = cookies.get("_m_h5_tk", "").split('_')[0]
    
    # 3. 核心：下载图片 (模拟小程序内下载)
    session = requests.Session()
    session.headers.update(headers)
    session.cookies.update(cookies)
    
    print("正在下载图片并上传至闲鱼服务器...")
    img_resp = session.get(img_url, verify=False)
    
    upload_resp = session.post(UPLOAD_URL, files={"file": ("avatar.jpg", img_resp.content, "image/jpeg")}, 
                               data={"appkey": "fleamarket", "bizCode": "fleamarket"})
    
    upload_data = upload_resp.json()
    if not upload_data.get("success"):
        print(f"上传失败，响应内容: {upload_data}")
        return
    
    final_img_url = upload_data["object"]["url"]
    print(f"上传成功! 最终图片地址: {final_img_url}")

    # 4. 更新头像 (MTOP 接口)
    t = str(int(time.time() * 1000))
    data_obj = {"utdid": json.loads(urllib.parse.unquote(headers.get("data", "{}"))).get("utdid", ""), 
                "platform": "windows", "profileCode": "avatar", "profileImageUrl": final_img_url}
    data_str = json.dumps(data_obj, separators=(",", ":"), ensure_ascii=False)
    
    params = {
        "jsv": "2.4.12", "appKey": APP_KEY, "t": t, "api": API, "v": "1.0",
        "sign": get_sign(token, t, APP_KEY, data_str),
        "type": "originaljson"
    }

    res = session.post(f"{BASE_URL}?{urllib.parse.urlencode(params)}", data={"data": data_str})
    print(f"更新头像最终结果: {res.text}")

if __name__ == "__main__":
    run_task()
