import streamlit as st
# 请将你的原文件重命名为 xianyu_url.py
import xianyu_url as core 

st.set_page_config(page_title="闲鱼头像助手", page_icon="🐟")
st.title("🐟 闲鱼头像自动更新")

with st.sidebar:
    st.header("1. 认证配置")
    token_input = st.text_input("当前 _m_h5_tk:", value="717336018584e9c7c54f266f5db96fca_1772912434028")
    req_text = st.text_area("粘贴完整的 HTTP 请求:", height=200)

img_url = st.text_input("2. 图片 URL:")

if st.button("🚀 执行更新"):
    if not req_text or not img_url:
        st.error("请补充完整信息！")
    else:
        try:
            with st.spinner("正在处理请求..."):
                # 调用你 xianyu_url.py 中的函数
                # 注意：如果你的函数名或参数在原文件中不同，请根据实际情况微调
                auth_info = core.extract_from_request(req_text)
                auth_info['m_h5_tk'] = token_input
                auth_info['token'] = token_input.split('_')[0]
                
                st.info("正在上传图片...")
                final_url = core.upload_from_url(img_url, auth_info)
                
                st.info("正在更新头像...")
                result = core.update_avatar(final_url, auth_info)
                
                st.success("操作完成！")
                st.json(result)
        except Exception as e:
            st.error(f"出错啦: {str(e)}")
