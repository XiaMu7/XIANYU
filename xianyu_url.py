# -*- coding: utf-8 -*-
import hashlib
import json
import time
import re
import urllib.parse
from urllib.parse import urlencode
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
    """从请求文本中提取 cookies 和 utdid"""
    info = {"cookies": {}, "utdid": None}
    # 提取 Cookie
    cookie_match = re.search(r'cookie: (.*)', request_text, re.IGNORECASE)
    if cookie_match:
        cookie_str = cookie_match.group(1)
        for part in cookie_str.split(';'):
            if '=' in part:
                k, v = part.strip().split('=', 1)
                info["cookies"][k] = v
    
    # 提取 utdid (从请求的 data 部分)
    data_match = re.search(r'data=(.*)', request_text)
    if data_match:
        try:
            data_json = json.loads(urllib.parse.unquote(data_match.group(1)))
            info["utdid"] = data_json.get("utdid")
        except:
            pass
    return info

def upload_from_url(file_url: str, auth_info: dict) -> str:
    """下载图片并上传到闲鱼服务器"""
    s = get_session()
    # 1. 下载图片
    resp = s.get(file_url, timeout=15)
    resp.raise_for_status()
    
    # 2. 上传图片
    files = {"file": ("avatar.jpg", resp.content, "image/jpeg")}
    data = {"bizCode": "fleamarket", "appkey": "fleamarket", "name": "fileFromAlbum"}
    
    # 使用 extract_from_request 得到的 cookies
    cookies = auth_info.get("cookies", {}).copy()
    cookies["_m_h5_tk"] = auth_info.get("m_h5_tk", "")
    
    up_resp = s.post(UPLOAD_URL, data=data, files=files, cookies=cookies)
    up_resp.raise_for_status()
    
    res_json = up_resp.json()
    if not res_json.get("success"):
        raise RuntimeError(f"上传服务器拒绝: {res_json}")
    return res_json["object"]["url"]

def update_avatar(image_url: str, auth_info: dict, token: str) -> dict:
    """调用闲鱼更新头像接口"""
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
