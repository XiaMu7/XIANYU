import streamlit as st
import xianyu_core as core

st.set_page_config(page_title="闲鱼头像助手", layout="wide")
st.title("🐟 闲鱼头像更新助手")

# Step 1: 图片输入与预览
st.subheader("1. 图片设置")
image_url = st.text_input("请输入图片链接:")
if image_url:
    st.image(image_url, width=200, caption="预览图")

# Step 2: 粘贴请求
st.subheader("2. 粘贴 HTTP 请求")
request_text = st.text_area("在此粘贴请求文本:", height=150)

# 实时显示解析信息
if request_text:
    auth = core.extract_from_request(request_text)
    st.info(f"解析到 UTDID: {auth.get('utdid')}")
    st.code(f"解析到的 Token(cookie2): {auth.get('m_h5_tk', '无')}")

# 执行按钮
if st.button("🚀 执行更新"):
    if not image_url or not request_text:
        st.error("请确保图片链接和请求文本都已提供！")
    else:
        try:
            res = core.update_avatar(image_url, auth)
            st.json(res)
            if "SUCCESS" in str(res):
                st.success("成功！")
        except Exception as e:
            st.error(f"发生错误: {e}")
