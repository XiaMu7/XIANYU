import streamlit as st
import xianyu_core as core

st.set_page_config(page_title="闲鱼头像自动更新器", page_icon="🐟")
st.title("🐟 闲鱼头像更新助手")

with st.sidebar:
    st.header("1. 粘贴请求")
    request_text = st.text_area("请粘贴完整的请求文本:", height=250)

image_url = st.text_input("2. 输入新图片链接:")

if st.button("🚀 开始执行更新"):
    if not request_text or not image_url:
        st.warning("请先填入请求文本和图片链接！")
    else:
        with st.spinner("解析并处理中..."):
            auth = core.extract_from_request(request_text)
            if not auth["utdid"] or not auth["m_h5_tk"]:
                st.error("解析失败！未提取到 UTDID 或 Token。")
            else:
                try:
                    result = core.update_avatar(image_url, auth)
                    st.json(result)
                    if "SUCCESS" in str(result):
                        st.success("🎉 头像更新成功！")
                    else:
                        st.error(f"更新请求被服务器拒绝: {result}")
                except Exception as e:
                    st.error(f"程序内部错误: {e}")
