import streamlit as st
import xianyu_url as core

st.set_page_config(page_title="闲鱼头像自动更新器", page_icon="🐟", layout="wide")
st.title("🐟 闲鱼头像更新助手")

# 1. 图片设置与预览区
st.header("1. 图片设置")
col1, col2 = st.columns([2, 1])
with col1:
    image_url = st.text_input("请输入新图片 URL (以 http/https 开头):")
with col2:
    if image_url:
        st.image(image_url, width=150, caption="图片预览")
    else:
        st.info("图片预览区")

# 2. 请求信息粘贴区
st.header("2. 粘贴 HTTP 请求")
request_text = st.text_area("请粘贴完整的请求文本 (包含 headers 和 data):", height=200)

# 自动解析并显示 Token
if request_text:
    auth = core.extract_from_request(request_text)
    # 尝试从 cookie2 或 info 中获取 token
    token_display = auth.get("m_h5_tk") or auth.get("cookies", {}).get("cookie2", "未检测到")
    st.success(f"✅ 已解析到 Token/Cookie2: {token_display[:20]}...")
    st.caption("如果 Token 显示为‘未检测到’，请检查请求内容是否完整。")

# 3. 执行更新
if st.button("🚀 开始执行更新"):
    if not request_text or not image_url:
        st.warning("请确保图片链接和请求文本都已填写！")
    else:
        with st.spinner("正在与闲鱼服务器通信..."):
            try:
                # 传入解析出的 auth 字典
                result = core.update_avatar(image_url, auth)
                st.json(result)
                
                if "SUCCESS" in str(result.get("ret", "")):
                    st.success("🎉 头像更新成功！")
                else:
                    st.error(f"更新失败，服务器返回: {result}")
            except Exception as e:
                st.error(f"程序运行出错: {str(e)}")

