import hashlib
import time
import requests
import json

class XianyuClient:
    def __init__(self, auth_info):
        self.auth = auth_info
        self.session = requests.Session()
        self.app_key = "12574478"
        self.base_url = "https://acs.m.goofish.com/h5/mtop.idle.wx.user.profile.update/1.0/"

    def get_sign(self, token, t, data_str):
        return hashlib.md5(f"{token}&{t}&{self.app_key}&{data_str}".encode()).hexdigest()

    def update_avatar(self, image_url):
        utdid = self.auth.get("utdid")
        data_json = {"utdid": utdid, "profileImageUrl": image_url}
        data_str = json.dumps(data_json, separators=(",", ":"))
        
        # 初始 Token 从 auth 提取
        cookie2 = self.auth["cookies"].get("cookie2", "")
        token = cookie2.split('_')[0]
        
        for attempt in range(2):  # 自动重试 2 次
            t = str(int(time.time() * 1000))
            sign = self.get_sign(token, t, data_str)
            params = {"appKey": self.app_key, "t": t, "sign": sign, "api": "mtop.idle.wx.user.profile.update", "dataType": "json"}
            
            res = self.session.post(
                f"{self.base_url}?{requests.utils.urlencode(params)}",
                data={"data": data_str},
                cookies=self.auth["cookies"],
                verify=False
            )
            
            res_data = res.json()
            # 检查是否有新 Token
            new_tk = res.cookies.get('_m_h5_tk')
            if new_tk:
                token = new_tk.split('_')[0]
                self.auth["cookies"]["cookie2"] = new_tk
            
            if "SUCCESS" in str(res_data.get("ret", "")):
                return {"status": "success", "data": res_data}
            
            time.sleep(1) # 稍作停顿再重试
        return {"status": "fail", "data": res_data}
