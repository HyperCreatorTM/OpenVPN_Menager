import paramiko
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=10)

MONITOR_SCRIPT_CONTENT = r"""
import time
import sys
import os
import json
import re
import subprocess

LOG_FILE = "/var/log/openvpn/status.log"
LIMITS_FILE = "/root/vpn_limits.json"
CHECK_INTERVAL = 60

def parse_size(size_str):
    if not size_str or size_str == "0": return 0
    size_str = size_str.upper()
    units = {"KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
    for unit, factor in units.items():
        if unit in size_str:
            try:
                return float(size_str.replace(unit, "")) * factor
            except:
                return 0
    try:
        return float(size_str)
    except:
        return 0

def get_usage():
    usage = {}
    if not os.path.exists(LOG_FILE):
        return usage
    
    with open(LOG_FILE, "r") as f:
        content = f.read()
    
    for line in content.split("\n"):
        if "," in line and "ROUTING TABLE" not in line and "GLOBAL STATS" not in line and "Common Name" not in line:
            parts = line.split(",")
            if len(parts) >= 4:
                username = parts[0]
                bytes_recv = int(parts[2])
                bytes_sent = int(parts[3])
                total = bytes_recv + bytes_sent
                usage[username] = total
    return usage

def revoke_user(username):
    cmd = f"MENU_OPTION=2 CLIENT={username} ./openvpn-install.sh"
    subprocess.run(cmd, shell=True)
    
    try:
        with open(LIMITS_FILE, "r") as f:
            data = json.load(f)
        if username in data:
            del data[username]
            with open(LIMITS_FILE, "w") as f:
                json.dump(data, f)
    except:
        pass

def main():
    while True:
        try:
            if not os.path.exists(LIMITS_FILE):
                with open(LIMITS_FILE, "w") as f: json.dump({}, f)
                time.sleep(CHECK_INTERVAL)
                continue

            with open(LIMITS_FILE, "r") as f:
                limits = json.load(f)

            current_usage = get_usage()

            for user, limit_str in limits.items():
                limit_bytes = parse_size(limit_str)
                if limit_bytes == 0: continue

                used = current_usage.get(user, 0)
                
                if used > limit_bytes:
                    revoke_user(user)

        except Exception:
            pass
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
"""

def _get_ssh_client(vps_info):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        vps_info["ip"], port=vps_info["port"], 
        username=vps_info["user"], password=vps_info["pass"], timeout=15
    )
    return client

def _install_logic(vps_info):
    commands = [
        "export DEBIAN_FRONTEND=noninteractive && apt-get update -y",
        "export DEBIAN_FRONTEND=noninteractive && apt-get install -y curl wget ca-certificates python3",
        "curl -O https://raw.githubusercontent.com/angristan/openvpn-install/master/openvpn-install.sh",
        "chmod +x openvpn-install.sh",
        "AUTO_INSTALL=y ./openvpn-install.sh"
    ]
    
    full_log = ""
    client = None
    try:
        client = _get_ssh_client(vps_info)
        
        for cmd in commands:
            stdin, stdout, stderr = client.exec_command(cmd)
            stdout.channel.recv_exit_status()
            full_log += stdout.read().decode(errors="ignore") + "\n"
        
        sftp = client.open_sftp()
        with sftp.file("/root/vpn_monitor.py", "w") as f:
            f.write(MONITOR_SCRIPT_CONTENT)
        sftp.close()

        service_content = """[Unit]
Description=VPN Traffic Monitor
After=network.target

[Service]
ExecStart=/usr/bin/python3 /root/vpn_monitor.py
Restart=always
User=root

[Install]
WantedBy=multi-user.target
"""
        client.exec_command(f"echo '{service_content}' > /etc/systemd/system/vpn_monitor.service")
        client.exec_command("systemctl daemon-reload && systemctl enable vpn_monitor && systemctl restart vpn_monitor")
        
        full_log += "\nMonitor servisi kuruldu."
        
        return True, full_log
    except Exception as e:
        return False, str(e)
    finally:
        if client: client.close()

def _add_user_logic(vps_info, username, traffic_limit):
    client = None
    try:
        client = _get_ssh_client(vps_info)
        
        client.exec_command(f"MENU_OPTION=1 CLIENT={username} PASS=1 ./openvpn-install.sh")
        
        update_json_cmd = f"""python3 -c 'import json, os; f="/root/vpn_limits.json"; data=json.load(open(f)) if os.path.exists(f) else {{}}; data["{username}"]="{traffic_limit}"; json.dump(data, open(f, "w"))'"""
        client.exec_command(update_json_cmd)

        stdin, stdout, stderr = client.exec_command(f"cat /root/{username}.ovpn")
        content = stdout.read().decode(errors="ignore")
        
        if "BEGIN PRIVATE KEY" in content:
            return True, "OK", content
        return False, "Dosya oluşmadı", None
    except Exception as e:
        return False, str(e), None
    finally:
        if client: client.close()

def _update_user_logic(vps_info, username, traffic_limit):
    client = None
    try:
        client = _get_ssh_client(vps_info)
        
        update_json_cmd = f"""python3 -c 'import json, os; f="/root/vpn_limits.json"; data=json.load(open(f)) if os.path.exists(f) else {{}}; data["{username}"]="{traffic_limit}"; json.dump(data, open(f, "w"))'"""
        client.exec_command(update_json_cmd)

        stdin, stdout, stderr = client.exec_command(f"cat /root/{username}.ovpn")
        content = stdout.read().decode(errors="ignore")
        
        if "BEGIN PRIVATE KEY" in content:
            return True, "OK", content
        return False, "Dosya okunamadı", None
    except Exception as e:
        return False, str(e), None
    finally:
        if client: client.close()

def _revoke_user_logic(vps_info, username):
    client = None
    try:
        client = _get_ssh_client(vps_info)
        cmd = f"MENU_OPTION=2 CLIENT={username} ./openvpn-install.sh"
        stdin, stdout, stderr = client.exec_command(cmd)
        stdout.channel.recv_exit_status()
        
        update_json_cmd = f"""python3 -c 'import json, os; f="/root/vpn_limits.json"; data=json.load(open(f)) if os.path.exists(f) else {{}}; data.pop("{username}", None); json.dump(data, open(f, "w"))'"""
        client.exec_command(update_json_cmd)
        
        return True, "Deleted"
    except Exception as e:
        return False, str(e)
    finally:
        if client: client.close()

def _uninstall_logic(vps_info):
    client = None
    try:
        client = _get_ssh_client(vps_info)
        client.exec_command("systemctl stop vpn_monitor && systemctl disable vpn_monitor && rm /etc/systemd/system/vpn_monitor.service")
        cmd = "apt-get remove --purge -y openvpn && rm -rf /etc/openvpn && rm -f /root/openvpn-install.sh && rm /root/vpn_monitor.py && rm /root/vpn_limits.json"
        client.exec_command(cmd)
        return True, "Deleted"
    except Exception as e:
        return False, str(e)
    finally:
        if client: client.close()

def _get_online_users_logic(vps_info):
    client = None
    try:
        client = _get_ssh_client(vps_info)
        
        stdin, stdout, stderr = client.exec_command("cat /var/log/openvpn/status.log")
        content = stdout.read().decode(errors="ignore")
        
        online_users = []
        for line in content.split("\n"):
            if "," in line and "ROUTING TABLE" not in line and "GLOBAL STATS" not in line and "Common Name" not in line and "Updated" not in line:
                parts = line.split(",")
                if len(parts) >= 5:
                    username = parts[0]
                    ip = parts[1].split(":")[0] 
                    connected_since = parts[4]
                    online_users.append({"user": username, "ip": ip, "time": connected_since})
                    
        return True, online_users
    except Exception as e:
        return False, str(e)
    finally:
        if client: client.close()

async def install_async(vps):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _install_logic, vps)

async def add_user_async(vps, user, traffic_limit="0"):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _add_user_logic, vps, user, traffic_limit)

async def update_user_async(vps, user, traffic_limit="0"):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _update_user_logic, vps, user, traffic_limit)

async def revoke_user_async(vps, user):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _revoke_user_logic, vps, user)

async def uninstall_async(vps):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _uninstall_logic, vps)

async def get_online_users_async(vps):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _get_online_users_logic, vps)
