import json
import re
import urllib.parse

def extract_from_request(request_text: str) -> dict:
    """从请求文本中解析关键凭证"""
    info = {"cookies": {}, "utdid": None}
    text = str(request_text)
    
    # 1. 提取 x-smallstc 中的 cookie2 (这是闲鱼最核心的令牌)
    stc_match = re.search(r'x-smallstc: (\{.*?\})', text)
    if stc_match:
        try:
            stc_json = json.loads(stc_match.group(1))
            cookie2 = stc_json.get('cookie2')
            if cookie2:
                # 闲鱼 API 需要 cookie2 字段，且通常也需要 _m_h5_tk 键
                info["cookies"]['cookie2'] = str(cookie2)
                info["cookies"]['_m_h5_tk'] = str(cookie2).split('_')[0]
                # 额外同步其他关键凭证
                for key in ['sgcookie', 'sid']:
                    if key in stc_json:
                        info["cookies"][key] = str(stc_json[key])
        except Exception as e:
            print(f"解析 x-smallstc 异常: {e}")
            
    # 2. 提取 UTDID (通过 data 字段)
    data_match = re.search(r'data=%7B%22utdid%22%3A%22(.*?)%22', text)
    if data_match:
        info["utdid"] = data_match.group(1)
        
    return info
