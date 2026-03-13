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
        st.error("请确保已粘贴完整请求文本及图片地址！")
    else:
        try:
            with st.spinner("正在处理..."):
                auth_info = core.extract_from_request(req_text)
                # 自动提取 Token
                token = auth_info.get("m_h5_tk")
                
                if not token:
                    st.error("无法从请求中提取到 _m_h5_tk，请检查请求文本！")
                else:
                    st.write(f"✅ 已提取 Token: {token[:10]}...")
                    
                    # 上传图片
                    final_url = core.upload_from_url(img_url, auth_info)
                    st.success("图片上传成功")
                    
                    # 更新头像
                    result = core.update_avatar(final_url, auth_info, token)
                    st.json(result)
                    
                    if "SUCCESS" in str(result.get("ret", "")):
                        st.balloons()
                        st.success("🎉 头像更新成功！")
                    else:
                        st.error("更新失败，请检查请求文本是否过期。")
        except Exception as e:
            st.error(f"发生错误: {str(e)}")
