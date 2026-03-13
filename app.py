import streamlit as st
import xianyu_core as core

st.set_page_config(page_title="闲鱼头像更新工具", page_icon="🐟")
st.title("🐟 闲鱼头像自动更新工具")

# 在侧边栏输入认证信息
with st.sidebar:
    st.subheader("配置信息")
    # 这里存储 session_state 以保持 token 在网页会话中更新
    if 'token' not in st.session_state:
        st.session_state['token'] = "717336018584e9c7c54f266f5db96fca_1772912434028"
    
    st.session_state['token'] = st.text_input("当前 _m_h5_tk", value=st.session_state['token'])
    req_text = st.text_area("粘贴完整 HTTP 请求文本 (用于提取 UTDID/Cookie)", height=150)

# 主界面输入图片
img_url = st.text_input("图片 URL", placeholder="https://example.com/image.jpg")

if st.button("开始执行更新"):
    if not req_text or not img_url:
        st.warning("请确保请求文本和图片URL都已填写")
    else:
        try:
            with st.status("正在执行任务...", expanded=True) as status:
                # 1. 提取认证数据
                auth_info = core.extract_from_request(req_text, st.session_state['token'])
                st.write("✅ 认证信息提取完成")
                
                # 2. 下载并上传
                st.write("正在下载与上传图片...")
                final_url = core.upload_from_url(img_url, auth_info)
                st.write(f"✅ 图片上传成功: {final_url}")
                
                # 3. 更新头像
                st.write("正在提交更新请求...")
                result = core.update_avatar(final_url, auth_info)
                
                status.update(label="任务执行完成!", state="complete")
            
            st.json(result)
            
            if result.get("ret") and "SUCCESS" in str(result["ret"]):
                st.success("🎉 头像更新成功！")
            else:
                st.error("头像更新未成功，请检查接口返回结果。")
                
        except Exception as e:
            st.error(f"处理过程中发生错误: {str(e)}")
