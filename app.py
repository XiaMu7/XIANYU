import streamlit as st
import xianyu_url as core

st.set_page_config(page_title="闲鱼头像助手", page_icon="🐟")
st.title("🐟 闲鱼头像自动更新助手")

with st.sidebar:
    st.header("⚙️ 认证信息")
    req_text = st.text_area("粘贴完整 HTTP 请求 (必须含 Cookie):", height=200)

img_url = st.text_input("🖼️ 图片 URL:")

if st.button("🚀 开始执行更新"):
    if not req_text or not img_url:
        st.error("请粘贴完整请求文本和图片链接！")
    else:
        try:
            with st.spinner("正在解析与更新中..."):
                # 1. 自动解析提取
                auth_info = core.extract_from_request(req_text)
                
                if not auth_info.get("m_h5_tk") or not auth_info.get("utdid"):
                    st.error("无法从请求中自动解析 Token 或 UTDID，请检查是否粘贴了完整的原始请求。")
                else:
                    st.success("✅ 解析成功，正在处理...")
                    
                    # 2. 上传图片
                    final_url = core.upload_from_url(img_url, auth_info)
                    
                    # 3. 更新头像
                    result = core.update_avatar(final_url, auth_info)
                    st.json(result)
                    
                    if "SUCCESS" in str(result.get("ret", "")):
                        st.balloons()
                        st.success("🎉 头像更新成功！")
                    else:
                        st.error(f"头像更新失败: {result.get('ret', '未知错误')}")
        except Exception as e:
            st.error(f"发生程序错误: {str(e)}")
