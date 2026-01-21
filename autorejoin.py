import time, os, subprocess, requests, psutil, sys, re, json, io, platform, glob
from datetime import datetime
import pyautogui

# ==========================================================
# CẤU HÌNH AUTO UPDATE
# ==========================================================
CURRENT_VERSION = "1.0"
# Link file chứa số version mới nhất (Ví dụ: file .txt trên GitHub/Pastebin)
VERSION_URL = "LINK_RAW_GITHUB_VERSION_TXT_CUA_BAN"
# Link file code python mới nhất (Ví dụ: file .py trên GitHub Raw của bạn)
CODE_URL = "LINK_RAW_GITHUB_CODE_PY_CUA_BAN"
# ==========================================================

def check_for_updates():
    """Kiểm tra và tự động cập nhật tool"""
    # Nếu chưa điền link update thì bỏ qua
    if "LINK_RAW" in VERSION_URL or "LINK_RAW" in CODE_URL:
        return

    print(f"   ☁️  Đang kiểm tra bản cập nhật... (v{CURRENT_VERSION})")
    try:
        # 1. Lấy version online (timeout 5s để không bị treo lâu)
        response = requests.get(VERSION_URL, timeout=5)
        if response.status_code != 200:
            return # Lỗi link hoặc mạng
            
        new_version = response.text.strip()
        
        # 2. So sánh version
        if new_version != CURRENT_VERSION:
            print(f"   🚀  Phát hiện bản mới: v{new_version}")
            print("   📥  Đang tải xuống bản cập nhật...")
            
            # 3. Tải code mới về
            code_response = requests.get(CODE_URL, timeout=10)
            if code_response.status_code == 200:
                new_code = code_response.content
                
                # 4. Ghi đè lên file hiện tại
                script_path = os.path.abspath(__file__)
                with open(script_path, "wb") as f:
                    f.write(new_code)
                    
                print("   ✅  Cập nhật thành công!")
                print("   🔁  Vui lòng khởi động lại tool.")
                print("--------------------------------------------------")
                input("Nhấn Enter để thoát...")
                sys.exit(0)
            else:
                print("   ❌  Lỗi khi tải bản cập nhật.")
        else:
            print(f"   ✅  Bạn đang dùng phiên bản mới nhất.")
            
    except Exception as e:
        print(f"   ⚠️  Lỗi Update (Không ảnh hưởng tool): {e}")

# ==========================================================
# CẤU HÌNH CONFIG FILE
# ==========================================================
def load_config():
    config = {}
    # Xác định đường dẫn file config nằm cùng thư mục với script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.txt")
    
    if not os.path.exists(config_path):
        print(f"-> Chưa thấy file config. Đang tạo mới tại: {config_path}")
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                f.write("# Cấu hình Tool Auto Rejoin Roblox\n")
                f.write("# Điền thông tin vào sau dấu =\n")
                f.write("COOKIE=\n")
                f.write("PLACE_ID=\n")
                f.write("WEBHOOK_URL=\n")
                f.write("# Dán Link Server VIP (SVV) hoặc Code VIP vào dưới\n")
                f.write("VIP_CODE=\n")
            
            print("----------------------------------------------------------------")
            print("ĐÃ TẠO FILE CONFIG.TXT THÀNH CÔNG!")
            print("Vui lòng mở file config.txt và điền đầy đủ thông tin:")
            print(" - COOKIE")
            print(" - PLACE_ID (ID game)")
            print(" - WEBHOOK_URL (Link Webhook Discord)")
            print(" - VIP_CODE (Link Server VIP)")
            print("Sau khi điền xong, hãy lưu file và chạy lại tool.")
            print("----------------------------------------------------------------")
        except Exception as e:
            print(f"Lỗi khi tạo file config: {e}")
            
        input("Nhấn Enter để thoát...")
        sys.exit(1)
    
    with open(config_path, "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.strip().split("=", 1)
                config[key.strip()] = value.strip()
    return config

config = load_config()

COOKIE_CUA_BAN = config.get("COOKIE", "")
VIP_CODE = config.get("VIP_CODE", "")
# Hỗ trợ người dùng paste cả link vip server vào -> Tự lọc lấy code
if "privateServerLinkCode" in VIP_CODE:
    match = re.search(r'privateServerLinkCode=([^&]+)', VIP_CODE)
    if match:
        VIP_CODE = match.group(1)

PLACE_ID = config.get("PLACE_ID", "")
DISCORD_WEBHOOK_URL = config.get("WEBHOOK_URL", "")
IMAGE_FILE = "disconnect_alert.png" 
LOBBY_FILE = "lobby.png"

if not COOKIE_CUA_BAN or not PLACE_ID:
    print("Lỗi: config.txt thiếu COOKIE hoặc PLACE_ID!")
    sys.exit(1)
# ==========================================================

count_rejoin = 0
start_time = datetime.now()

# ... (Giữ nguyên hàm hien_thi_bang và kiem_tra_roblox_treo) ...

def check_roblox_log_status():
    """
    Kiểm tra file log mới nhất của Roblox để xem trạng thái thực tế.
    Trả về: True nếu phát hiện đã Disconnect/Rời game.
    """
    try:
        # Đường dẫn log mặc định của Roblox trên Windows
        log_path = os.path.expandvars(r"%LocalAppData%\Roblox\logs")
        if not os.path.exists(log_path):
            return False
            
        # Lấy danh sách file log, sắp xếp theo thời gian mới nhất (Player_*)
        list_of_files = glob.glob(os.path.join(log_path, '0.*_Player_*.log'))
        if not list_of_files:
            return False
            
        latest_file = max(list_of_files, key=os.path.getmtime)
        
        # Đọc file log (mở chế độ đọc binary để tránh lỗi encoding)
        with open(latest_file, 'rb') as f:
            # Di chuyển con trỏ xuống cuối file để đọc dữ liệu mới nhất
            # Đọc tối đa 5000 bytes cuối
            try:
                f.seek(-5000, 2) 
            except OSError:
                f.seek(0) # Tránh lỗi nếu file quá ngắn
                
            content = f.read().decode('utf-8', errors='ignore')
            
            # Các từ khóa cho thấy đã ngắt kết nối
            disconnect_keywords = [
                "Connection lost",
                "Time to disconnect",
                "Disconnect event received",
                "Client initiated disconnect",
                "Connection closed"
            ]
            
            # Nếu thấy từ khóa disconnect ở cuối log -> Đang ở sảnh
            for kw in disconnect_keywords:
                if kw in content:
                    # Tuy nhiên phải check xem có lệnh join lại sau đó không
                    # Nếu "Connecting to..." xuất hiện SAU "Disconnect" thì là đang join lại
                    last_disconnect = content.rfind(kw)
                    last_connect = content.rfind("Connecting to")
                    
                    if last_disconnect > last_connect:
                        return True # Disconnect là trạng thái cuối cùng
                        
    except Exception as e:
        # print(f"Lỗi đọc log: {e}")
        pass
        
    return False


def get_authenticated_user_id(session):
    """
    Lay User ID tu Cookie hien tai.
    """
    try:
        response = session.get("https://users.roblox.com/v1/users/authenticated", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("id")
        else:
            print(f"⚠️  Loi lay User ID: {response.status_code}")
            return None
    except Exception as e:
        print(f"⚠️  Exception User ID: {e}")
        return None

def check_presence_status(session, user_id):
    """
    Kiem tra trang thai Online/InGame cua user.
    Tra ve: status_code (0=Offline, 1=Online, 2=InGame, 3=Studio)
    """
    try:
        url = "https://presence.roblox.com/v1/presence/users"
        payload = {"userIds": [user_id]}
        response = session.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            user_presences = data.get("userPresences", [])
            if user_presences:
                # 0: Offline, 1: Online, 2: InGame, 3: Studio
                return user_presences[0].get("userPresenceType")
    except Exception:
        pass
    return None


def hien_thi_bang(trang_thai):
    os.system('cls' if os.name == 'nt' else 'clear')
    
    uptime = str(datetime.now() - start_time).split('.')[0]
    
    # Cập nhật Title cửa sổ Console
    if os.name == 'nt':
        os.system(f"title BÌNH YÊU ĐAN THƯ - Uptime: {uptime} - Rejoined: {count_rejoin}")

    # ANSI Colors for Decoration
    CYAN = "\033[96m" 
    MAGENTA = "\033[95m"
    GREEN = "\033[92m" 
    YELLOW = "\033[93m"
    WHITE = "\033[97m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    print(f"{CYAN}{'='*62}{RESET}")
    print(f"{MAGENTA}{BOLD}      ♥  BÌNH YÊU ĐAN THƯ  ♥      {RESET} | {GREEN} Auto Rejoin Ultimate {RESET}")
    print(f"{CYAN}{'='*62}{RESET}")
    print(f"  {YELLOW}⏳ Thời gian chạy :{RESET} {WHITE}{uptime}{RESET}")
    print(f"  {YELLOW}🔄 Đã Rejoin      :{RESET} {WHITE}{count_rejoin} lần{RESET}")
    print(f"  {YELLOW}📢 Trạng thái     :{RESET} {WHITE}{trang_thai}{RESET}")
    print(f"{CYAN}{'='*62}{RESET}")

def  kiem_tra_roblox_treo():
    """Kiểm tra disconnect bằng cách tìm hình ảnh nút bấm trên màn hình"""
    if not os.path.exists(IMAGE_FILE):
        return False # Không có file ảnh thì không check được
    
    try:
        # Tìm hình ảnh trên màn hình, confidence 0.8 là độ chính xác 80%
        # grayscale=True giúp tìm nhanh hơn và đỡ bị sai do màu sắc thay đổi nhẹ
        pos = pyautogui.locateOnScreen(IMAGE_FILE, confidence=0.8, grayscale=True)
        if pos:
            return True # Đã tìm thấy bảng Disconnect
    except Exception as e:
        # Có thể lỗi do chưa cài opencv, nhưng code vẫn chạy tiếp
        pass
        
    return False

def bypass_launch():
    hien_thi_bang("Error detected! Rejoining...")
    
    # 1. Kill process cu truoc
    print("   -> Closing old Roblox...")
    os.system("taskkill /F /IM RobloxPlayerBeta.exe /T >nul 2>&1")
    time.sleep(2)

    global count_rejoin
    clean_cookie = re.sub(r'\s+', '', COOKIE_CUA_BAN)
    session = requests.Session()
    session.cookies.set(".ROBLOSECURITY", clean_cookie, domain="roblox.com")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": f"https://www.roblox.com/games/{PLACE_ID}/",
        "Origin": "https://www.roblox.com",
        "Content-Type": "application/json"
    }
    
    try:
        print("   -> Đang kết nối lấy Authentication Ticket...")
        # Lấy CSRF Token (Thường server trả về 403 kèm token)
        r1 = session.post("https://auth.roblox.com/v1/authentication-ticket", headers=headers, json={}, timeout=15)
        csrf_token = r1.headers.get("x-csrf-token")
        
        if not csrf_token:
            print(f"Warning: x-csrf-token not found (Status: {r1.status_code})")
            # Cookie might be invalid
            print("   -> Retrying in 5s...")
            return False

        headers["x-csrf-token"] = csrf_token
        
        # Thử lại lần 2 với token mới để lấy Ticket thật
        r2 = session.post("https://auth.roblox.com/v1/authentication-ticket", headers=headers, json={}, timeout=15)
        ticket = r2.headers.get("rbx-authentication-ticket")
        
        # Line 182-183 duplicate removed
        if ticket:
            print("   -> Ticket obtained! Preparing to launch...")
            
            # Launch command chuan (URL Protocol)
            launch_cmd = f"roblox-player:1+launchmode:play+gameinfo:{ticket}+launchtime:{int(time.time()*1000)}+placelauncherurl:https%3A%2F%2Fassetgame.roblox.com%2Fgame%2FPlaceLauncher.ashx%3Frequest%3DPlugin%26placeId%3D{PLACE_ID}%26linkCode%3D{VIP_CODE}"
            
            # Dung lenh start cua Windows de kich hoat giao thuc roblox-player
            # Cach nay giong het trinh duyet, on dinh hon goi file exe truc tiep
            os.system(f'start "" "{launch_cmd}"')
            
            global count_rejoin
            count_rejoin += 1
            hien_thi_bang(f"Rejoin Success #{count_rejoin}!")
            return True
        else:
            print(f"Failed to get Ticket. Status: {r2.status_code}")
            if r2.status_code == 401:
                print("   -> Cookie expired or invalid.")
            else:
                print(f"   -> Response: {r2.text[:100]}...")

    except requests.exceptions.Timeout:
        print("Error: Connection Timeout.")
    except requests.exceptions.ConnectionError:
        print("Error: No Internet Connection.")
    except Exception as e:
        print(f"Unknown Error: {e}")
        
    return False

def kiem_tra_o_lobby():
    """Kiểm tra xem có đang kẹt ở màn hình Home/Lobby không"""
    if not os.path.exists(LOBBY_FILE):
        return False # Chưa có ảnh lobby thì bỏ qua
    
    try:
        # Tìm ảnh Home/Lobby
        pos = pyautogui.locateOnScreen(LOBBY_FILE, confidence=0.8, grayscale=True)
        if pos:
            return True # Đang ở sảnh -> Cần Rejoin
    except:
        pass
    return False

def send_screenshot_to_discord():
    """Chụp màn hình và gửi về Discord Webhook (Rich Embed)"""
    try:
        # --- 1. Gather Info ---
        pc_name = platform.node()
        cpu_name = platform.processor()
        logical_cores = psutil.cpu_count(logical=True)
        physical_cores = psutil.cpu_count(logical=False)
        ram = psutil.virtual_memory()
        total_ram_gb = f"{ram.total / (1024**3):.2f} GB"
        ram_percent = ram.percent
        platform_info = platform.platform()
        
        # Count Roblox processes
        roblox_count = 0
        for p in psutil.process_iter(['name']):
            try:
                if p.info['name'] == 'RobloxPlayerBeta.exe':
                    roblox_count += 1
            except: pass

        # --- 2. Screenshot ---
        screenshot = pyautogui.screenshot()
        img_buffer = io.BytesIO()
        screenshot.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # --- 3. Construct Payload (Multipart) ---
        
        # Embed structure
        embed = {
            "title": "🖥️ PC STATUS",
            "description": "**System Information**",
            "color": 3066993, # A nicer Green (0x2ecc71)
            "fields": [
                {"name": "👤 PC Name", "value": f"`{pc_name}`", "inline": True},
                {"name": "🪟 Platform", "value": f"`{platform_info}`", "inline": True},
                {"name": "\u200b", "value": "\u200b", "inline": False}, # Spacer
                {"name": "🧠 CPU", "value": f"`{cpu_name}`", "inline": False},
                {"name": "⚙️ Cores/Threads", "value": f"`{physical_cores} Cores` | `{logical_cores} Threads`", "inline": True},
                {"name": "💾 Total RAM", "value": f"`{total_ram_gb}`", "inline": True},
                
                {"name": "\u200b", "value": "\u200b", "inline": False}, # Spacer
                {"name": "📼 RAM Usage", "value": f"```\n{ram_percent}%\n```", "inline": True},
                {"name": "🎮 Roblox Active", "value": f"```\n{roblox_count} process(es)\n```", "inline": True},
            ],
            "image": {"url": "attachment://screenshot.png"},
            "footer": {"text": f"| https://VuHaiBinh11A1.gg | {datetime.now().strftime('%H:%M - %d/%m/%Y')}", "icon_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Octicons-mark-github.svg/600px-Octicons-mark-github.svg.png"}
        }

        files = {
            'file': ('screenshot.png', img_buffer, 'image/png'),
        }
        
        # 'payload_json' lets us send JSON + Files together
        data = {
            "payload_json": json.dumps({"embeds": [embed]})
        }
        
        requests.post(DISCORD_WEBHOOK_URL, data=data, files=files)
        
        # Debug log to identifying duplicate runs
        masked_url = DISCORD_WEBHOOK_URL[-20:] if len(DISCORD_WEBHOOK_URL) > 20 else "..."
        print(f"✅ Screenshot sent to Webhook (...{masked_url})")
    except Exception as e:
        print(f"Webhook Error: {e}")



def check_key():
    """Yêu cầu nhập Work.ink Token để sử dụng tool"""
    # Fix path handling
    script_dir = os.path.dirname(os.path.abspath(__file__))
    key_file = os.path.join(script_dir, "key.txt")
    
    def check_token_validity(token):
        try:
            # API Request to Work.ink
            url = f"https://work.ink/_api/v2/token/isValid/{token}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) python-requests/2.31.0"
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                 return False, f"Server Error {response.status_code}"
            
            data = response.json()
            if data.get("valid") == True:
                return True, "Valid"
            else:
                reason = data.get("message", "Token không hợp lệ hoặc đã hết hạn.")
                return False, reason
        except Exception as e:
            return False, str(e)

    # --- 1. Kiểm tra Key đã lưu trước ---
    if os.path.exists(key_file):
        print("\n   ⏳ Đang kiểm tra Key đã lưu...")
        try:
            with open(key_file, "r", encoding="utf-8") as f:
                saved_token = f.read().strip()
            
            if saved_token:
                is_valid, msg = check_token_validity(saved_token)
                if is_valid:
                    print(f"   ✅ \033[92mKey đã lưu hợp lệ! ({saved_token[:8]}...)\033[0m")
                    time.sleep(1)
                    return # Key ngon -> Vào luôn
                else:
                    print(f"   ❌ \033[91mKey đã lưu hết hạn hoặc lỗi: {msg}\033[0m")
                    print("   👉 Vui lòng lấy Key mới.")
                    time.sleep(2)
        except Exception as e:
            print(f"   ⚠️  Lỗi đọc key file: {e}")

    # --- 2. Nếu chưa có Key hoặc Key lỗi -> Bắt nhập ---
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"\033[96m{'='*60}\033[0m")
        print(f"\033[93m{'🔒 HỆ THỐNG BẢO MẬT - WORK.INK KEY SYSTEM':^60}\033[0m")
        print(f"\033[96m{'='*60}\033[0m")
        print("\n")
        print("   👉 Link lấy Key mới: https://work.ink/2a0V/ctatool")
        print("   (Copy link và dán vào trình duyệt web)")
        print("\n")
        
        try:
            user_input = input("   🔑 Nhập Token: ").strip()
            
            if not user_input:
                continue
                
            print("   ⏳ Đang kiểm tra Token...")
            is_valid, msg = check_token_validity(user_input)
                
            if is_valid:
                print("\n   ✅ \033[92mToken hợp lệ! Đang truy cập...\033[0m")
                # Save key lai
                try:
                    with open(key_file, "w", encoding="utf-8") as f:
                        f.write(user_input)
                    print("   💾 Đã lưu Key vào máy (key.txt). Lần sau không cần nhập.")
                except Exception as e:
                    print(f"   ⚠️  Lỗi lưu key: {e}")
                    
                time.sleep(1)
                break
            else:
                print(f"\n   ❌ \033[91mLỗi: {msg}\033[0m")
                time.sleep(2)
                    
        except KeyboardInterrupt:
            sys.exit()

def check_multiple_instances():
    """Cảnh báo nếu có nhiều tool đang chạy cùng lúc"""
    current_pid = os.getpid()
    count = 0
    script_name = "roblox_manager" # Tìm theo tên chung
    
    print(f"🔒 Checking for background instances... (Current PID: {current_pid})")
    
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if p.info['pid'] == current_pid:
                continue
                
            if "python" in p.info['name'].lower():
                cmdline = p.info['cmdline']
                if cmdline:
                    cmd_str = " ".join(cmdline).lower()
                    if script_name in cmd_str:
                         print(f"⚠️  PHÁT HIỆN TOOL CHẠY NGẦM (PID: {p.info['pid']})")
                         count += 1
        except:
            pass
            
    if count > 0:
        print(f"⚠️  CẢNH BÁO: Có {count} bản khác của tool đang chạy!")
        print("👉 Điều này gây ra việc gửi 2 Webhook cùng lúc.")
        print("👉 Hãy tắt các cửa sổ CMD/Terminal khác. Kiểm tra Task Manager.")
        print("--------------------------------------------------")
        time.sleep(3)

if __name__ == "__main__":
    if os.name == 'nt':
        os.system("color") # Kích hoạt màu ANSI trên Windows CMD
        
    check_for_updates()
    check_key()
    
    check_multiple_instances()

    # In thong bao khoi dong
    hien_thi_bang("Đang khởi động...")
    print("Dang kiem tra thu vien...")
    try:
        import cv2
        import numpy as np # Import numpy if cv2 is present, just in case
    except ImportError:
        pass

    # Khoi tao session va lay User ID
    clean_cookie = re.sub(r'\s+', '', COOKIE_CUA_BAN)
    main_session = requests.Session()
    main_session.cookies.set(".ROBLOSECURITY", clean_cookie, domain="roblox.com")
    
    current_user_id = get_authenticated_user_id(main_session)
    if not current_user_id:
        print("Failed to get User ID. Check Cookie!")
        print("   Tool will try old mode (Check Process)...")
        time.sleep(3)
        
    # Trigger webhook immediately by setting time to (now - 301)
    last_webhook_time = time.time() - 301 # Trigger ngay lap tuc

    while True:
        try:
            # === WEBHOOK CHECK (Moi 5 phut) ===
            current_time = time.time()
            if current_time - last_webhook_time > 300: # 300s = 5 phut
                send_screenshot_to_discord()
                last_webhook_time = current_time
            # ==================================

            need_rejoin = False
            status_text = "Checking..."
            
            # 1. Tuu tien check Web WEB API neu co User ID
            if current_user_id:
                presence = check_presence_status(main_session, current_user_id)
                # presence: 0=Offline, 1=Online, 2=InGame, 3=Studio
                
                if presence == 2:
                    # Dang trong game -> OK
                    hien_thi_bang("Detected In Game (Web API). Waiting...")
                    time.sleep(8) # Check lai cham hon vi dang on dinh
                    continue
                elif presence is not None:
                    # 0, 1, 3 -> Khong phai InGame -> Can Rejoin
                    hien_thi_bang(f"Web Status: {presence} (Offline/Online). Need Rejoin...")
                    need_rejoin = True
                else:
                    # Loi API -> Fallback sang check process
                    pass
            
            # 2. Neu Web API loi file hoac chua xac dinh, dung logic cu
            if not need_rejoin and not current_user_id:
                 # Kiểm tra xem game có đang chạy không
                is_running = False
                for p in psutil.process_iter(['name', 'cmdline']):
                    try:
                        if p.info['name'] == "RobloxPlayerBeta.exe":
                            cmdline = p.info['cmdline']
                            if cmdline:
                                cmd_str = " ".join(cmdline).lower()
                                if "--app" in cmd_str: continue
                                if "--play" in cmd_str or "roblox-player:" in cmd_str:
                                    is_running = True
                                    break
                    except: pass
                
                if not is_running:
                    hien_thi_bang("Game Closed (Check Process).")
                    need_rejoin = True
                elif kiem_tra_roblox_treo():
                    hien_thi_bang("Disconnect Banner Detected.")
                    need_rejoin = True
            
            # 3. Xu ly Rejoin
            if need_rejoin:
                if bypass_launch():
                    # Rejoin thanh cong -> Cho game load va API cap nhat
                    count_seconds = 45 
                    for i in range(count_seconds, 0, -1):
                        hien_thi_bang(f"Waiting for game load... {i}s")
                        time.sleep(1)
                else:
                    for i in range(20, 0, -1):
                        hien_thi_bang(f"Rejoin failed. Retry in {i}s...")
                        time.sleep(1)
            else:
                # Truong hop Web check fail nhung User ID None chang han
                # Hoac logic fallback
                hien_thi_bang("Monitoring...")
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\nTool stopped.")
            break
        except Exception as e:
            print(f"Error Loop: {e}")
            time.sleep(5)

