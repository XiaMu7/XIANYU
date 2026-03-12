#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import json
import mimetypes
import time
import sys
import re
import urllib.parse
from pathlib import Path
from urllib.parse import urlparse, urlencode, parse_qs
import os
import base64
from typing import Optional, Tuple, Dict, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 禁用SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API = "mtop.idle.wx.user.profile.update"
APP_KEY = "12574478"
BASE_URL = "https://acs.m.goofish.com/h5/mtop.idle.wx.user.profile.update/1.0/"
UPLOAD_URL = "https://stream-upload.goofish.com/api/upload.api"

# 会话对象，用于保持cookie，全局禁用SSL验证
session = requests.Session()
session.verify = False  # 全局禁用SSL验证

# 配置重试策略
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

# ===== 初始的 _m_h5_tk（第一次运行后会自动更新）=====
CURRENT_M_H5_TK = "717336018584e9c7c54f266f5db96fca_1772912434028"
# ===============================================


def create_session_with_retries() -> requests.Session:
    """创建支持重试的会话"""
    session = requests.Session()
    session.verify = False  # 禁用SSL验证
    retry = Retry(
        total=3,
        read=3,
        connect=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def check_url_accessibility(url: str, timeout: int = 10) -> Tuple[bool, int, str]:
    """
    快速检查URL的可访问性
    
    Returns:
        Tuple[bool, int, str]: (是否可访问, 状态码, 状态描述)
    """
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True, verify=False)
        return True, response.status_code, response.reason
    except Exception as e:
        return False, 0, str(e)


def extract_auth_from_url(url: str) -> Dict[str, str]:
    """
    从URL中提取可能的认证信息
    支持格式: https://username:password@example.com/image.jpg
    """
    auth_info = {}
    parsed = urlparse(url)
    
    # 检查URL中是否包含用户名密码
    if parsed.username and parsed.password:
        auth_info['username'] = parsed.username
        auth_info['password'] = parsed.password
        # 生成Basic Auth头
        auth_str = f"{parsed.username}:{parsed.password}"
        auth_info['basic_auth'] = base64.b64encode(auth_str.encode()).decode()
    
    return auth_info


def handle_401_with_auth(url: str, timeout: int = 30) -> Optional[Tuple[bytes, str, str]]:
    """
    专门处理401错误的函数，尝试多种认证方式
    """
    print("\n🔄 检测到401授权错误，尝试使用认证信息...")
    
    parsed_url = urlparse(url)
    file_name = os.path.basename(parsed_url.path)
    if not file_name or '.' not in file_name:
        file_name = f"image_{int(time.time())}.jpg"
    
    # 尝试的认证方式
    auth_attempts = []
    
    # 方式1: 从URL中提取的Basic Auth
    url_auth = extract_auth_from_url(url)
    if url_auth.get('basic_auth'):
        auth_attempts.append({
            'name': 'URL Basic Auth',
            'headers': {
                'Authorization': f"Basic {url_auth['basic_auth']}",
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        })
    
    print("\n是否需要提供访问令牌/认证信息？")
    print("1. 提供Bearer Token")
    print("2. 提供Cookie")
    print("3. 跳过，不使用认证")
    print("4. 尝试其他方式")
    
    choice = input("请选择 (1-4): ").strip()
    
    if choice == "1":
        token = input("请输入Bearer Token: ").strip()
        if token:
            auth_attempts.append({
                'name': 'Bearer Token',
                'headers': {
                    'Authorization': f"Bearer {token}",
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            })
    
    elif choice == "2":
        cookie_str = input("请输入Cookie (key=value; key2=value2): ").strip()
        if cookie_str:
            auth_attempts.append({
                'name': 'Cookie Auth',
                'headers': {
                    'Cookie': cookie_str,
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            })
    
    elif choice == "3":
        print("跳过认证尝试")
        return None
    
    elif choice == "4":
        # 尝试其他常见认证方式
        print("\n尝试其他常见认证方式...")
        
        # 尝试常见的Referer
        common_referers = [
            f"https://{parsed_url.netloc}/",
            "https://www.google.com/",
            "https://www.baidu.com/",
        ]
        
        for referer in common_referers:
            auth_attempts.append({
                'name': f'Referer: {referer}',
                'headers': {
                    'Referer': referer,
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            })
        
        # 尝试添加常见的请求头
        common_headers = [
            {'X-Requested-With': 'XMLHttpRequest'},
            {'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8'},
            {'Origin': f"https://{parsed_url.netloc}"},
        ]
        
        for headers in common_headers:
            auth_attempts.append({
                'name': f'Headers: {headers}',
                'headers': {**headers, 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            })
    
    # 尝试所有认证方式
    download_session = create_session_with_retries()
    
    for attempt in auth_attempts:
        try:
            print(f"\n尝试认证方式: {attempt['name']}")
            
            response = download_session.get(
                url,
                timeout=timeout,
                verify=False,
                headers=attempt['headers'],
                allow_redirects=True
            )
            
            if response.status_code == 200:
                content = response.content
                if len(content) > 0:
                    content_type = response.headers.get('Content-Type', '')
                    mime = content_type.split(';')[0].strip()
                    if not mime or mime == 'application/octet-stream':
                        guessed = mimetypes.guess_type(file_name)[0]
                        mime = guessed or 'image/jpeg'
                    
                    print(f"✅ 认证成功！使用 {attempt['name']}")
                    print(f"   文件大小: {len(content)} bytes")
                    print(f"   MIME类型: {mime}")
                    
                    return content, file_name, mime
            else:
                print(f"   ❌ 失败: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 失败: {str(e)[:100]}")
            continue
    
    return None


def download_image_with_fallback(url: str, timeout: int = 30) -> Tuple[bytes, str, str]:
    """
    下载图片，支持多种URL类型和SSL降级策略，特别处理401授权错误
    
    Returns:
        Tuple[bytes, str, str]: (图片二进制内容, 文件名, MIME类型)
    """
    print(f"\n开始处理图片URL: {url}")
    
    # 首先检查URL是否可访问
    print(f"\n检查URL可访问性...")
    accessible, status_code, reason = check_url_accessibility(url)
    
    if status_code == 401:
        print(f"⚠️ URL返回 401 Authorization Required")
        # 尝试处理401错误
        auth_result = handle_401_with_auth(url, timeout)
        if auth_result:
            return auth_result
    
    # 创建临时会话
    download_session = create_session_with_retries()
    
    # 常见的浏览器User-Agent
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
    ]
    
    # 解析URL
    parsed_url = urlparse(url)
    file_name = os.path.basename(parsed_url.path)
    if not file_name or '.' not in file_name:
        # 如果没有文件名或扩展名，使用时间戳
        file_name = f"image_{int(time.time())}.jpg"
    
    # 尝试不同的下载策略
    strategies = [
        # 策略1：标准验证
        {"verify": True, "headers": {"User-Agent": user_agents[0]}, "name": "标准验证"},
        # 策略2：跳过SSL验证
        {"verify": False, "headers": {"User-Agent": user_agents[0]}, "name": "跳过SSL"},
        # 策略3：移动端UA
        {"verify": False, "headers": {"User-Agent": user_agents[2]}, "name": "移动端UA"},
        # 策略4：添加Referer
        {"verify": False, "headers": {
            "User-Agent": user_agents[0],
            "Referer": f"https://{parsed_url.netloc}/"
        }, "name": "添加Referer"},
        # 策略5：微信内置浏览器UA
        {"verify": False, "headers": {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36 MicroMessenger/7.0.18",
            "Referer": "https://servicewechat.com/"
        }, "name": "微信UA"},
        # 策略6：完整浏览器头
        {"verify": False, "headers": {
            "User-Agent": user_agents[1],
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://www.google.com/",
        }, "name": "完整浏览器头"},
    ]
    
    last_error = None
    for i, strategy in enumerate(strategies, 1):
        try:
            print(f"\n尝试下载策略 {i}/{len(strategies)}: {strategy['name']}")
            
            headers = strategy["headers"].copy()
            
            response = download_session.get(
                url,
                timeout=timeout,
                verify=strategy["verify"],
                headers=headers,
                allow_redirects=True,
                stream=True
            )
            
            if response.status_code == 401:
                print(f"   ⚠️ 返回 401 需要授权，尝试其他策略...")
                continue
                
            response.raise_for_status()
            
            # 检查内容类型
            content_type = response.headers.get('Content-Type', '').lower()
            if content_type and not any(img_type in content_type for img_type in ['image/', 'application/octet-stream']):
                print(f"   ⚠️ 警告: 可能不是图片文件 (Content-Type: {content_type})")
            
            # 读取内容
            content = response.content
            
            if len(content) == 0:
                print(f"   ⚠️ 下载的文件为空")
                continue
            
            # 获取MIME类型
            mime = content_type.split(';')[0].strip()
            if not mime or mime == 'application/octet-stream':
                # 尝试从文件扩展名猜测
                guessed = mimetypes.guess_type(file_name)[0]
                if guessed:
                    mime = guessed
                else:
                    # 默认使用图片类型
                    mime = 'image/jpeg' if file_name.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
            
            print(f"✅ 下载成功 (策略 {i})")
            print(f"   文件大小: {len(content)} bytes")
            print(f"   MIME类型: {mime}")
            print(f"   文件名: {file_name}")
            
            return content, file_name, mime
            
        except requests.exceptions.SSLError as e:
            last_error = e
            print(f"   ❌ SSL错误: {str(e)[:100]}...")
            continue
        except requests.exceptions.HTTPError as e:
            last_error = e
            if hasattr(response, 'status_code') and response.status_code == 401:
                print(f"   ⚠️ 需要授权 (401)")
                # 尝试处理401
                auth_result = handle_401_with_auth(url, timeout)
                if auth_result:
                    return auth_result
            else:
                status_code = response.status_code if hasattr(response, 'status_code') else 'unknown'
                print(f"   ❌ HTTP错误 {status_code}: {str(e)[:100]}")
            continue
        except requests.exceptions.RequestException as e:
            last_error = e
            print(f"   ❌ 请求错误: {str(e)[:100]}...")
            continue
        except Exception as e:
            last_error = e
            print(f"   ❌ 未知错误: {str(e)[:100]}...")
            continue
    
    # 如果所有策略都失败，给用户一个选项
    print("\n" + "=" * 50)
    print("所有自动下载策略都失败了！")
    print("可能的原因：")
    print("1. 图片链接需要特定的访问权限")
    print("2. 链接已失效")
    print("3. 需要登录或认证")
    print("=" * 50)
    
    # 询问用户是否要手动下载
    print("\n是否尝试手动下载？")
    print("1. 提供新的图片URL")
    print("2. 退出程序")
    
    choice = input("请选择 (1-2): ").strip()
    
    if choice == "1":
        new_url = input("请输入新的图片URL: ").strip()
        if new_url:
            return download_image_with_fallback(new_url, timeout)
    
    # 所有策略都失败
    error_msg = f"所有下载策略都失败，最后错误: {last_error}"
    print(f"❌ {error_msg}")
    raise RuntimeError(error_msg)


def extract_from_request(request_text: str) -> dict:
    """从HTTP请求文本中提取所有必要信息"""
    info = {
        "cookies": {},
        "headers": {},
        "params": {},
        "data": {},
        "utdid": None,
        "token": CURRENT_M_H5_TK.split('_')[0] if '_' in CURRENT_M_H5_TK else CURRENT_M_H5_TK,
        "m_h5_tk": CURRENT_M_H5_TK,
    }
    
    lines = request_text.strip().split('\n')
    
    # 解析第一行获取URL参数
    first_line = lines[0]
    url_match = re.search(r'\?(.*?)(?:\s|$)', first_line)
    if url_match:
        params_str = url_match.group(1)
        params = parse_qs(params_str)
        for k, v in params.items():
            info["params"][k] = v[0] if v else ""
    
    # 解析headers
    for line in lines[1:]:
        line = line.strip()
        if not line or line.startswith('{') or line.startswith('h2'):
            continue
            
        if ': ' in line:
            key, value = line.split(': ', 1)
            key_lower = key.lower()
            
            info["headers"][key] = value
            
            # 特殊header处理
            if key_lower == 'x-smallstc':
                try:
                    smallstc = json.loads(value)
                    
                    # 提取cookie字段
                    if 'cookie2' in smallstc:
                        info["cookies"]['cookie2'] = str(smallstc['cookie2'])
                    if 'sgcookie' in smallstc:
                        info["cookies"]['sgcookie'] = str(smallstc['sgcookie'])
                        info["headers"]['sgcookie'] = str(smallstc['sgcookie'])
                    if 'csg' in smallstc:
                        info["cookies"]['csg'] = str(smallstc['csg'])
                    if 'unb' in smallstc:
                        info["cookies"]['unb'] = str(smallstc['unb'])
                    if 'munb' in smallstc:
                        info["cookies"]['munb'] = str(smallstc['munb'])
                    if 'sid' in smallstc:
                        info["cookies"]['sid'] = str(smallstc['sid'])
                        
                except json.JSONDecodeError:
                    pass
    
    # 解析data部分 - 查找最后的数据行
    data_line = None
    for line in reversed(lines):
        if line.strip().startswith('data='):
            data_line = line.strip()
            break
    
    if data_line:
        data_str = data_line[5:]  # 去掉"data="
        # URL解码
        data_str = urllib.parse.unquote(data_str)
        try:
            info["data"] = json.loads(data_str)
            info["utdid"] = info["data"].get("utdid")
            print(f"从data提取的utdid: {info['utdid']}")
        except json.JSONDecodeError:
            # 如果JSON解析失败，尝试正则提取
            utdid_match = re.search(r'utdid[":]+([^"]+)', data_str)
            if utdid_match:
                info["utdid"] = utdid_match.group(1)
                print(f"从data正则提取的utdid: {info['utdid']}")
    
    return info


def get_user_input() -> dict:
    """交互式获取用户输入"""
    print("\n请选择输入方式：")
    print("1. 粘贴完整的HTTP请求（推荐）")
    print("   https://acs.m.goofish.com/h5/mtop.idle.wx.user.profile.update/1.0/2.0/?jsv=2.4.12&...")
    print("2. 手动输入关键信息")
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == "1":
        print("\n请粘贴完整的HTTP请求（包含headers和data）：")
        print("示例请求URL开头:")
        print("https://acs.m.goofish.com/h5/mtop.idle.wx.user.profile.update/1.0/2.0/?jsv=2.4.12&appKey=12574478&...")
        print("（输入完成后，在新行输入 END 并回车结束）")
        
        lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        
        request_text = "\n".join(lines)
        info = extract_from_request(request_text)
        
        print(f"\n使用当前 _m_h5_tk: {CURRENT_M_H5_TK}")
        
        return info
    
    elif choice == "2":
        info = {
            "cookies": {},
            "headers": {},
            "params": {},
            "data": {},
            "utdid": None,
            "token": CURRENT_M_H5_TK.split('_')[0] if '_' in CURRENT_M_H5_TK else CURRENT_M_H5_TK,
            "m_h5_tk": CURRENT_M_H5_TK,
        }
        
        print("\n请输入关键信息：")
        info["utdid"] = input("utdid (从data中获取): ").strip()
        
        if not info["utdid"]:
            print("错误：utdid不能为空")
            sys.exit(1)
        
        print("\n请输入Cookie信息（留空可跳过）：")
        cookie2 = input("cookie2: ").strip()
        if cookie2:
            info["cookies"]["cookie2"] = cookie2
        
        sgcookie = input("sgcookie: ").strip()
        if sgcookie:
            info["cookies"]["sgcookie"] = sgcookie
            info["headers"]["sgcookie"] = sgcookie
        
        csg = input("csg: ").strip()
        if csg:
            info["cookies"]["csg"] = csg
        
        unb = input("unb: ").strip()
        if unb:
            info["cookies"]["unb"] = unb
        
        munb = input("munb: ").strip()
        if munb:
            info["cookies"]["munb"] = munb
        
        print("\n请输入Header信息（留空可跳过）：")
        bx_umidtoken = input("bx-umidtoken: ").strip()
        if bx_umidtoken:
            info["headers"]["bx-umidtoken"] = bx_umidtoken
        
        x_ticid = input("x-ticid: ").strip()
        if x_ticid:
            info["headers"]["x-ticid"] = x_ticid
        
        mini_janus = input("mini-janus: ").strip()
        if mini_janus:
            info["headers"]["mini-janus"] = mini_janus
        
        bx_ua = input("bx-ua: ").strip()
        if bx_ua:
            info["headers"]["bx-ua"] = bx_ua
        
        return info
    
    else:
        print("无效选择")
        sys.exit(1)


def calc_sign(token: str, t: str, app_key: str, data_str: str) -> str:
    raw = f"{token}&{t}&{app_key}&{data_str}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def update_avatar(image_url: str, auth_info: dict, retry_count: int = 0) -> dict:
    global CURRENT_M_H5_TK
    
    # 构建cookies
    cookies = auth_info.get("cookies", {}).copy()
    
    # 使用当前的 _m_h5_tk
    m_h5_tk = CURRENT_M_H5_TK
    token = m_h5_tk.split('_')[0] if '_' in m_h5_tk else m_h5_tk
    
    # 添加到cookies
    cookies["_m_h5_tk"] = m_h5_tk
    cookies["_m_h5_tk_enc"] = "927a61b5898abf557861458d0ea06b6f"
    
    # 获取utdid
    utdid = auth_info.get("utdid")
    if not utdid:
        raise ValueError("Missing utdid")

    data_obj = {
        "utdid": utdid,
        "platform": "mac",
        "miniAppVersion": "9.9.9",
        "profileCode": "avatar",
        "profileImageUrl": image_url,
    }
    data_str = json.dumps(data_obj, separators=(",", ":"), ensure_ascii=False)

    t = str(int(time.time() * 1000))
    sign = calc_sign(token, t, APP_KEY, data_str)

    params = {
        "jsv": "2.4.12",
        "appKey": APP_KEY,
        "t": t,
        "sign": sign,
        "v": "1.0",
        "type": "originaljson",
        "accountSite": "xianyu",
        "dataType": "json",
        "timeout": "20000",
        "api": API,
        "_bx-m": "1",
    }

    # 合并headers
    headers = {
        "User-Agent": auth_info.get("headers", {}).get("user-agent", 
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/126.0.0.0"
        ),
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "Referer": "https://servicewechat.com/wx9882f2a891880616/74/page-frame.html",
    }
    
    # 添加原始请求中的特殊headers
    special_headers = ["bx-umidtoken", "x-ticid", "x-tap", "mini-janus", "sgcookie", "bx-ua"]
    for h in special_headers:
        if h in auth_info.get("headers", {}):
            headers[h] = auth_info["headers"][h]

    print(f"\n发送请求到: {BASE_URL}")
    print(f"使用的token: {token}")
    print(f"使用的_m_h5_tk: {m_h5_tk}")

    # 使用session发送请求
    response = session.post(
        f"{BASE_URL}?{urlencode(params)}",
        headers=headers,
        cookies=cookies,
        data={"data": data_str},
        timeout=20,
        verify=False  # 确保禁用SSL验证
    )
    
    print(f"响应状态码: {response.status_code}")
    
    # 自动提取新的 _m_h5_tk 并更新
    token_updated = False
    if '_m_h5_tk' in response.cookies:
        new_m_h5_tk = response.cookies['_m_h5_tk']
        if new_m_h5_tk != CURRENT_M_H5_TK:
            print(f"发现新的 _m_h5_tk: {new_m_h5_tk}")
            print(f"自动更新当前token")
            CURRENT_M_H5_TK = new_m_h5_tk
            # 更新到auth_info
            auth_info['m_h5_tk'] = new_m_h5_tk
            auth_info['token'] = new_m_h5_tk.split('_')[0] if '_' in new_m_h5_tk else new_m_h5_tk
            token_updated = True
    
    result = response.json()
    
    # 如果返回非法令牌且没有重试过，并且token被更新了，则自动重试一次
    if result.get("ret") and "FAIL_SYS_TOKEN_ILLEGAL" in str(result["ret"]) and retry_count == 0 and token_updated:
        print("\n🔄 检测到新token，自动重试一次...")
        time.sleep(1)  # 等待1秒后重试
        return update_avatar(image_url, auth_info, retry_count=1)
    
    return result


def upload_bytes(file_name: str, file_bytes: bytes, mime: str, auth_info: dict) -> str:
    global CURRENT_M_H5_TK
    
    cookies = auth_info.get("cookies", {}).copy()
    
    # 使用最新的 _m_h5_tk
    cookies["_m_h5_tk"] = CURRENT_M_H5_TK
    
    files = {
        "file": (file_name, file_bytes, mime),
    }
    data = {
        "content-type": "multipart/form-data",
        "appkey": "fleamarket",
        "bizCode": "fleamarket",
        "floderId": "0",
        "name": "fileFromAlbum",
    }
    params = {
        "floderId": "0",
        "appkey": "fleamarket",
        "_input_charset": "utf-8",
    }
    
    headers = {
        "User-Agent": auth_info.get("headers", {}).get("user-agent",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/126.0.0.0"
        ),
        "Accept": "*/*",
        "Referer": "https://servicewechat.com/wx9882f2a891880616/74/page-frame.html",
    }
    
    # 添加必要的headers
    for h in ["bx-umidtoken", "x-ticid", "mini-janus", "sgcookie"]:
        if h in auth_info.get("headers", {}):
            headers[h] = auth_info["headers"][h]

    print(f"上传文件到: {UPLOAD_URL}")
    
    # 修改：添加 verify=False 禁用SSL验证
    response = session.post(
        UPLOAD_URL,
        params=params,
        headers=headers,
        cookies=cookies,
        data=data,
        files=files,
        timeout=30,
        verify=False  # 禁用SSL验证
    )
    response.raise_for_status()
    body = response.json()
    if not body.get("success"):
        raise RuntimeError(f"Upload failed: {body}")
    image_url = body.get("object", {}).get("url")
    if not image_url:
        raise RuntimeError(f"Upload response missing object.url: {body}")
    return image_url


def upload_from_url(file_url: str, auth_info: dict) -> str:
    """
    从URL下载图片并上传到闲鱼
    
    支持多种URL类型，自动处理SSL证书验证失败的问题
    """
    print(f"\n开始处理图片URL: {file_url}")
    
    try:
        # 使用改进的下载函数，支持SSL降级和401处理
        content, file_name, mime = download_image_with_fallback(file_url)
        
        # 上传到闲鱼
        print("\n开始上传到闲鱼服务器...")
        final_url = upload_bytes(file_name, content, mime, auth_info)
        print(f"✅ 上传成功！")
        print(f"   最终URL: {final_url}")
        
        return final_url
        
    except Exception as e:
        print(f"❌ 图片处理失败: {e}")
        raise


def main():
    print("=" * 50)
    print("闲鱼头像自动更新工具 (增强版)")
    print("=" * 50)
    
    # 先让用户输入图片URL
    print("\n" + "-" * 50)
    print("第一步：请输入要设置为头像的图片URL")
    print("支持各种格式：gif, jpg, png, webp 等")
    print("例如：https://example.com/image.gif")
    print("提示：可使用 https://www.superbed.cn/ 图床获取图片链接")
    image_url = input("图片URL: ").strip()
    
    if not image_url:
        print("错误：图片URL不能为空")
        sys.exit(1)
    
    # 检查URL格式
    if not image_url.startswith(('http://', 'https://')):
        print("警告：URL格式可能不正确，请确保以 http:// 或 https:// 开头")
    
    # 再获取认证信息
    print("\n" + "-" * 50)
    print("第二步：请提供认证信息")
    auth_info = get_user_input()
    
    # 验证必要信息
    if not auth_info.get("utdid"):
        print("\n错误：未能提取到utdid")
        print("请尝试手动输入模式（选项2）")
        sys.exit(1)
    
    print("\n" + "-" * 50)
    print("开始处理头像更新...")
    
    try:
        # 下载并上传图片
        final_url = upload_from_url(image_url, auth_info)
        
        # 更新头像
        print("\n" + "-" * 50)
        print("更新头像信息...")
        result = update_avatar(final_url, auth_info)
        
        print("\n" + "=" * 50)
        print("处理结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if result.get("ret") and "SUCCESS" in str(result["ret"]):
            print("\n✅ 头像更新成功！")
        else:
            print("\n⚠️ 头像更新可能失败，请检查返回信息")
            
    except requests.exceptions.SSLError as e:
        print(f"\n❌ SSL证书错误: {e}")
        print("提示：程序已自动尝试多种下载策略，如果仍然失败，请检查URL是否有效")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 网络请求错误: {e}")
        print("提示：请检查网络连接和URL有效性")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()