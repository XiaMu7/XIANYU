# -*- coding: utf-8 -*-
import hashlib
import json
import mimetypes
import time
import re
import urllib.parse
from urllib.parse import urlencode, parse_qs
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API = "mtop.idle.wx.user.profile.update"
APP_KEY = "12574478"
BASE_URL = "https://acs.m.goofish.com/h5/mtop.idle.wx.user.profile.update/1.0/"
UPLOAD_URL = "https://stream-upload.goofish.com/api/upload.api"

def get_session():
    s = requests.Session()
    s.verify = False
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s

def extract_from_request(request_text: str) -> dict:
    """仅负责解析请求字符串，返回 auth_info 字典"""
    info = {"cookies": {}, "headers": {}, "params": {}, "data": {}, "utdid": None}
    lines = request_text.strip().split('\n')
    
    # 简单的正则提取
    for line in lines:
        if ': ' in line:
            key, value = line.split(': ', 1)
            info["headers"][key] = value
            if key.lower() == 'cookie':
                # 简单解析cookie
                for cookie in value.split(';'):
                    if '=' in cookie:
                        k, v = cookie.strip().split('=', 1)
                        info["cookies"][k] = v
    
    data_match = re.search(r'data=(.*)', request_text)
    if data_match:
        try:
            data_json = json.loads(urllib.parse.unquote(data_match.group(1)))
            info["data"] = data_json
            info["utdid"] = data_json.get("utdid")
        except: pass
    return info

def upload_from_url(file_url: str, auth_info: dict) -> str:
    """下载并上传图片，返回图片URL"""
    s = get_session()
    resp = s.get(file_url, timeout=15)
    resp.raise_for_status()
    
    files = {"file": ("avatar.jpg", resp.content, "image/jpeg")}
    data = {"bizCode": "fleamarket", "appkey": "fleamarket", "name": "fileFromAlbum"}
    cookies = auth_info.get("cookies", {}).copy()
    cookies["_m_h5_tk"] = auth_info.get("m_h5_tk", "")
    
    up_resp = s.post(UPLOAD_URL, data=data, files=files, cookies=cookies)
    up_resp.raise_for_status()
    return up_resp.json()["object"]["url"]

def update_avatar(image_url: str, auth_info: dict, token: str) -> dict:
    """执行头像更新"""
    s = get_session()
    t = str(int(time.time() * 1000))
    data_str = json.dumps({
        "utdid": auth_info.get("utdid"),
        "platform": "mac",
        "profileCode": "avatar",
        "profileImageUrl": image_url
    }, separators=(",", ":"), ensure_ascii=False)
    
    # 签名计算
    sign = hashlib.md5(f"{token.split('_')[0]}&{t}&{APP_KEY}&{data_str}".encode()).hexdigest()
    
    params = {"appKey": APP_KEY, "t": t, "sign": sign, "api": API, "dataType": "json"}
    cookies = auth_info.get("cookies", {}).copy()
    cookies["_m_h5_tk"] = token
    
    res = s.post(f"{BASE_URL}?{urlencode(params)}", data={"data": data_str}, cookies=cookies)
    return res.json()
