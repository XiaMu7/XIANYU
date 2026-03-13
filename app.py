import streamlit as st
import xianyu_url as core  # 确保你的原文件已重命名为 xianyu_url.py

st.set_page_config(page_title="闲鱼头像助手", page_icon="🐟")
st.title("🐟 闲鱼头像自动更新助手")

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 认证配置")
    token_input = st.text_input("当前 _m_h5_tk (从Cookie获取):", 
                                value="717336018584e9c7c54f266f5db96fca_1772912434028")
    req_text = st.text_area("粘贴完整的 HTTP 请求文本 (含 headers/data):", height=200)

# 主界面
img_url = st.text_input("🖼️ 输入图片 URL:")

if st.button("🚀 开始执行更新"):
    if not req_text or not img_url:
        st.error("请先在左侧粘贴请求文本，并在右侧输入图片链接！")
    else:
        try:
            with st.spinner("正在处理中..."):
                # 1. 提取认证数据
                auth_info = core.extract_from_request(req_text)
                
                # 2. 下载并上传图片
                st.write("正在下载与上传图片至闲鱼服务器...")
                final_url = core.upload_from_url(img_url, auth_info)
                st.success(f"图片上传成功: {final_url}")
                
                # 3. 更新头像
                st.write("正在提交头像更新请求...")
                result = core.update_avatar(final_url, auth_info, token_input)
                
                # 4. 显示结果
                st.json(result)
                
                if "SUCCESS" in str(result.get("ret", "")):
                    st.balloons()
                    st.success("🎉 头像更新成功！")
                else:
                    st.error("头像更新失败，请检查返回结果。")
        except Exception as e:
            st.error(f"发生错误: {str(e)}")
            st.code(e)
