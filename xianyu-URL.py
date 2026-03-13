import hashlib
import json
import mimetypes
import time
import re
import urllib.parse
import base64
from typing import Optional, Tuple, Dict, Any
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

# 全局session
session = requests.Session()
session.verify = False 

def create_session_with_retries() -> requests.Session:
    s = requests.Session()
    s.verify = False
    retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    s.mount('https://', adapter)
    return s

def calc_sign(token: str, t: str, app_key: str, data_str: str) -> str:
    raw = f"{token}&{t}&{app_key}&{data_str}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()

def extract_from_request(request_text: str, current_token: str) -> dict:
    """从请求文本中提取关键信息，不再使用input()"""
    info = {
        "cookies": {}, "headers": {}, "params": {}, "data": {},
        "utdid": None, "token": current_token.split('_')[0], "m_h5_tk": current_token
    }
    lines = request_text.strip().split('\n')
    # ... (解析逻辑保持不变) ...
    return info

def download_image_from_url(url: str, timeout: int = 30) -> Tuple[bytes, str, str]:
    """核心下载逻辑，移除所有input和print"""
    s = create_session_with_retries()
    try:
        response = s.get(url, timeout=timeout, verify=False, stream=True)
        response.raise_for_status()
        content = response.content
        mime = response.headers.get('Content-Type', 'image/jpeg').split(';')[0]
        return content, f"img_{int(time.time())}.jpg", mime
    except Exception as e:
        raise RuntimeError(f"下载图片失败: {str(e)}")

def upload_bytes(file_name: str, file_bytes: bytes, mime: str, auth_info: dict) -> str:
    """上传逻辑"""
    cookies = auth_info.get("cookies", {}).copy()
    cookies["_m_h5_tk"] = auth_info["m_h5_tk"]
    
    files = {"file": (file_name, file_bytes, mime)}
    data = {"bizCode": "fleamarket", "appkey": "fleamarket", "floderId": "0", "name": "fileFromAlbum"}
    
    response = session.post(UPLOAD_URL, files=files, data=data, cookies=cookies, verify=False)
    response.raise_for_status()
    body = response.json()
    if not body.get("success"):
        raise RuntimeError(f"上传失败: {body}")
    return body["object"]["url"]

def update_avatar(image_url: str, auth_info: dict) -> dict:
    """更新头像接口逻辑"""
    token = auth_info["token"]
    t = str(int(time.time() * 1000))
    data_str = json.dumps({
        "utdid": auth_info["utdid"],
        "platform": "mac",
        "profileCode": "avatar",
        "profileImageUrl": image_url
    }, separators=(",", ":"), ensure_ascii=False)
    
    params = {
        "appKey": APP_KEY, "t": t, "sign": calc_sign(token, t, APP_KEY, data_str),
        "api": API, "type": "originaljson", "dataType": "json"
    }
    
    response = session.post(
        f"{BASE_URL}?{urllib.parse.urlencode(params)}",
        data={"data": data_str},
        cookies={"_m_h5_tk": auth_info["m_h5_tk"]},
        verify=False
    )
    return response.json()
