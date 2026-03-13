# --- 网页界面 ---
st.set_page_config(page_title="闲鱼头像助手", page_icon="🐟")
st.title("🐟 闲鱼头像自动更新")

img_url = st.text_input("请输入图片URL:")
req_text = st.text_area("请粘贴完整的HTTP请求信息:", height=200)

if st.button("🚀 开始同步头像"):
    if not img_url or not req_text:
        st.error("请确保输入内容完整！")
    else:
        with st.status("正在处理...", expanded=True) as status:
            try:
                st.write("正在解析认证信息...")
                auth = extract_from_request(req_text)
                st.write("正在上传图片到闲鱼...")
                final_url = upload_to_xianyu(img_url, auth)
                st.write(f"图片已上传: {final_url}")
                st.write("正在调用API更新头像...")
                res = update_avatar(final_url, auth)
                
                st.json(res)
                if "SUCCESS" in str(res.get("ret", "")):
                    st.success("头像更新成功！")
                    st.balloons()
                else:
                    st.error("更新失败，请检查返回结果")
            except Exception as e:
                st.error(f"发生错误: {str(e)}")
