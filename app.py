import streamlit as st
import xianyu_core as core
import time
import hashlib
import json
import requests
from urllib.parse import urlencode

st.set_page_config(page_title="闲鱼头像助手", layout="wide")
st.title("🐟 闲鱼头像更新助手")

image_url = st.text_input("1. 输入新图片链接:")
request_text = st.text_area("2. 粘贴原始 HTTP 请求 (Raw):", height=200)

if st.button("🚀 执行更新"):
    if not image_url or not request_text:
        st.error("请确保图片链接和请求文本都已提供！")
    else:
        auth = core.extract_from_request(request_text)
        if not auth['cookies'].get('cookie2'):
            st.error("❌ 解析失败：未找到 cookie2。请检查粘贴的内容是否包含完整的 x-smallstc 行。")
        elif not auth['utdid']:
            st.error("❌ 解析失败：未找到 utdid。")
        else:
            try:
                # 准备签名参数
                token = auth['cookies']['cookie2'].split('_')[0]
                t = str(int(time.time() * 1000))
                data_str = json.dumps({"utdid": auth['utdid'], "profileImageUrl": image_url}, separators=(",", ":"))
                sign = hashlib.md5(f"{token}&{t}&{core.APP_KEY}&{data_str}".encode()).hexdigest()
                
                params = {"appKey": core.APP_KEY, "t": t, "sign": sign, "api": core.API, "dataType": "json"}
                
                # 发送请求 (关键点：将解析出来的 auth['cookies'] 传入)
                res = requests.post(
                    f"{core.BASE_URL}?{urlencode(params)}", 
                    data={"data": data_str},
                    cookies=auth['cookies'], 
                    verify=False
                )
                st.json(res.json())
                if "SUCCESS" in str(res.json().get("ret", "")):
                    st.success("头像更新成功！")
            except Exception as e:
                st.error(f"执行出错: {e}")
