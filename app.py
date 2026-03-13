import streamlit as st
import time
import hashlib
import json
import re
import requests
from urllib.parse import urlencode

# --- 配置项 ---
APP_KEY = "12574478"
API = "mtop.idle.wx.user.profile.update"
BASE_URL = "https://acs.m.goofish.com/h5/mtop.idle.wx.user.profile.update/1.0/"

# --- 核心逻辑 ---
def extract_auth(request_text: str) -> dict:
    """提取凭证"""
    info = {"cookies": {}, "utdid": None}
    text = str(request_text)
    
    # 提取 cookie2
    stc_match = re.search(r'x-smallstc: (\{.*?\})', text)
    if stc_match:
        try:
            stc_json = json.loads(stc_match.group(1))
            cookie2 = stc_json.get('cookie2')
            if cookie2:
                info["cookies"]['cookie2'] = str(cookie2)
                info["cookies"]['_m_h5_tk'] = str(cookie2).split('_')[0]
        except: pass
    
    # 提取 utdid
    data_match = re.search(r'data=%7B%22utdid%22%3A%22(.*?)%22', text)
    if data_match:
        info["utdid"] = data_match.group(1)
        
    return info

# --- 界面 ---
st.set_page_config(page_title="闲鱼头像助手", layout="wide")
st.title("🐟 闲鱼头像更新助手")

image_url = st.text_input("1. 输入新图片链接:")
request_text = st.text_area("2. 粘贴原始 HTTP 请求 (Raw):", height=200)

if st.button("🚀 执行更新"):
    if not image_url or not request_text:
        st.error("请填写完整信息")
    else:
        auth = extract_auth(request_text)
        if not auth['cookies'].get('cookie2'):
            st.error("解析失败：未找到 cookie2。")
        elif not auth['utdid']:
            st.error("解析失败：未找到 utdid。")
        else:
            try:
                # 签名与发送
                token = auth['cookies']['cookie2'].split('_')[0]
                t = str(int(time.time() * 1000))
                data_str = json.dumps({"utdid": auth['utdid'], "profileImageUrl": image_url}, separators=(",", ":"))
                sign = hashlib.md5(f"{token}&{t}&{APP_KEY}&{data_str}".encode()).hexdigest()
                
                params = {"appKey": APP_KEY, "t": t, "sign": sign, "api": API, "dataType": "json"}
                
                res = requests.post(
                    f"{BASE_URL}?{urlencode(params)}", 
                    data={"data": data_str},
                    cookies=auth['cookies'], 
                    verify=False
                )
                st.json(res.json())
                st.success("请求已发送，请查看返回结果。")
            except Exception as e:
                st.error(f"执行出错: {e}")
