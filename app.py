import streamlit as st
import xianyu_core as core
import time
import hashlib
import json

st.set_page_config(page_title="闲鱼头像自动更新", layout="wide")
st.title("🐟 闲鱼头像更新助手")

# 1. 步骤：设置图片
image_url = st.text_input("1. 输入新图片URL:")
if image_url: st.image(image_url, width=150)

# 2. 步骤：粘贴请求
request_text = st.text_area("2. 粘贴完整请求文本:", height=150)

if st.button("🚀 执行头像更新"):
    if not image_url or not request_text:
        st.error("请完整填写信息")
    else:
        with st.spinner("处理中..."):
            try:
                # 解析
                auth = core.extract_from_request(request_text)
                utdid = auth["utdid"]
                cookies = auth["cookies"]
                
                # 签名与更新头像逻辑直接内嵌在这里
                token = cookies.get('cookie2', '').split('_')[0]
                t = str(int(time.time() * 1000))
                data_str = json.dumps({"utdid": utdid, "profileImageUrl": image_url}, separators=(",", ":"))
                sign = hashlib.md5(f"{token}&{t}&{core.APP_KEY}&{data_str}".encode()).hexdigest()
                
                params = {"appKey": core.APP_KEY, "t": t, "sign": sign, "api": core.API, "dataType": "json"}
                
                # 发送
                res = core.call_api(f"{core.BASE_URL}?{core.urlencode(params)}", {"data": data_str}, cookies)
                st.json(res.json())
                st.success("操作完成！")
            except Exception as e:
                st.error(f"发生错误: {str(e)}")
