# -*- coding: utf-8 -*-
import hashlib
import json
import time
import re
import urllib.parse
from urllib.parse import urlencode, parse_qs
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3

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
    """自动从请求文本中解析 Token, UTID 和 Cookies"""
    info = {"cookies": {}, "headers": {}, "utdid": None, "m_h5_tk": None}
    lines = request_text.strip().split('\n')
    
    # 1. 提取 Cookies
    for line in lines:
        if line.lower().startswith('cookie:'):
            cookie_str = line.split(': ', 1)[1]
            for part in cookie_str.split(';'):
                if '=' in part:
                    k, v = part.strip().split('=', 1)
                    info["cookies"][k] = v
                    if k == '_m_h5_tk':
                        info["m_h5_tk"] = v
    
    # 2. 提取 UTDID
    data_match = re.search(r'data=(.*)', request_text)
    if data_match:
        try:
            data_str = urllib.parse.unquote(data_match.group(1))
            data_json = json.loads(data_str)
            info["utdid"] = data_json.get("utdid")
        except: pass
    return info

def upload_from_url(file_url: str, auth_info: dict) -> str:
    """下载并上传图片"""
    s = get_session()
    resp = s.get(file_url, timeout=15)
    resp.raise_for_status()
    
    cookies = auth_info.get("cookies", {}).copy()
    cookies["_m_h5_tk"] = auth_info.get("m_h5_tk", "")
    
    files = {"file": ("avatar.jpg", resp.content, "image/jpeg")}
    data = {"bizCode": "fleamarket", "appkey": "fleamarket", "name": "fileFromAlbum"}
    
    up_resp = s.post(UPLOAD_URL, data=data, files=files, cookies=cookies)
    up_resp.raise_for_status()
    res = up_resp.json()
    if not res.get("success"):
        raise RuntimeError(f"服务器返回上传失败: {res.get('message')}")
    return res["object"]["url"]

def update_avatar(image_url: str, auth_info: dict) -> dict:
    """执行最终头像更新"""
    s = get_session()
    token = auth_info.get("m_h5_tk", "").split('_')[0]
    t = str(int(time.time() * 1000))
    data_str = json.dumps({
        "utdid": auth_info.get("utdid"),
        "platform": "mac",
        "profileCode": "avatar",
        "profileImageUrl": image_url
    }, separators=(",", ":"), ensure_ascii=False)
    
    sign = hashlib.md5(f"{token}&{t}&{APP_KEY}&{data_str}".encode()).hexdigest()
    params = {"appKey": APP_KEY, "t": t, "sign": sign, "api": API, "dataType": "json"}
    
    cookies = auth_info.get("cookies", {}).copy()
    cookies["_m_h5_tk"] = auth_info.get("m_h5_tk", "")
    
    res = s.post(f"{BASE_URL}?{urlencode(params)}", data={"data": data_str}, cookies=cookies)
    return res.json()
