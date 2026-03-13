import streamlit as st
import xianyu_core
import json

st.title("🐟 闲鱼头像自动更新 (Pro)")

request_text = st.text_area("粘贴抓包的 Raw 请求:")
image_url = st.text_input("图片URL:")

if st.button("开始更新"):
    # 此处调用之前的解析函数
    auth = xianyu_core.extract_from_request(request_text)
    
    if not auth.get("utdid"):
        st.error("无法解析 UTDID，请检查请求文本")
    else:
        client = xianyu_core.XianyuClient(auth)
        with st.spinner("正在更新..."):
            result = client.update_avatar(image_url)
            
            if result["status"] == "success":
                st.success("头像更新成功！")
                st.json(result["data"])
            else:
                st.error("更新失败，服务器返回：")
                st.json(result["data"])
