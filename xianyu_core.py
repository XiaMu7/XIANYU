import hashlib
import json
import time
import requests
import urllib3
import re
from urllib.parse import urlencode

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API = "mtop.idle.wx.user.profile.update"
APP_KEY = "12574478"
BASE_URL = "https://acs.m.goofish.com/h5/mtop.idle.wx.user.profile.update/1.0/"
UPLOAD_URL = "https://stream-upload.goofish.com/api/upload.api"

def extract_from_request(request_text: str) -> dict:
    """从请求文本中解析关键信息"""
    info = {"cookies": {}, "headers": {}, "utdid": None}
    text = str(request_text)
    
    # 提取 UTDID
    data_match = re.search(r'data=(.*?)(?:\n|$)', text)
    if data_match:
        try:
            data_json = json.loads(data_match.group(1))
            info["utdid"] = data_json.get("utdid")
        except: pass
    
    # 提取关键凭证
    stc_match = re.search(r'x-smallstc: (\{.*?\})', text)
    if stc_match:
        try:
            stc_json = json.loads(stc_match.group(1))
            info["cookies"] = {k: str(v) for k, v in stc_json.items() if k in ['cookie2', 'sgcookie', 'sid']}
        except: pass
        
    return info

def call_api(url, data, cookies, files=None):
    """通用请求封装，自动处理认证"""
    return requests.post(url, data=data, cookies=cookies, files=files, verify=False)
