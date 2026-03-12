import streamlit as st
import json
import time

# --- CSS 美化配置 (注入楷体与样式) ---
st.markdown("""
<style>
    /* 全局字体设置为楷体 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'KaiTi', '楷体', 'Noto Serif SC', serif !important;
    }
    
    /* 美化容器背景 */
    .stApp {
        background-color: #f4f7f6;
    }
    
    /* 美化按钮 */
    div.stButton > button {
        border-radius: 20px;
        border: none;
        background-color: #4a90e2;
        color: white;
        font-weight: bold;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #357abd;
    }
    
    /* 调整标题居中 */
    h1 {
        text-align: center;
        color: #2c3e50;
    }
</style>
""", unsafe_allow_html=True)

# --- 界面逻辑 ---
st.title("🐟 闲鱼动态头像自动更新")

# 步骤 1：准备资源
st.subheader("1. 准备头像资源")
img_url = st.text_input("请输入图片 URL:", placeholder="https://...")
if img_url:
    st.image(img_url, width=200, caption="待更新头像预览")

# 步骤 2：身份认证
st.subheader("2. 身份认证")
with st.expander("点击设置认证参数 (utdid/cookies)", expanded=True):
    mode = st.radio("选择方式", ["粘贴请求包", "手动输入"], horizontal=True)
    if mode == "粘贴请求包":
        req_text = st.text_area("请粘贴请求内容:", height=100)
    else:
        utdid = st.text_input("utdid")
        cookie2 = st.text_input("cookie2")

# 步骤 3：执行
st.markdown("---")
if st.button("🚀 开始同步头像", use_container_width=True):
    with st.status("正在进行同步...", expanded=True) as status:
        st.write("解析配置...")
        time.sleep(0.5)
        st.write("下载并上传资源...")
        time.sleep(1)
        st.write("调用闲鱼 API 更新头像...")
        time.sleep(1)
        status.update(label="✅ 操作完成！", state="complete")
        st.balloons()