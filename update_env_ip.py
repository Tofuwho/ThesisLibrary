import sys
import os
import socket

def get_local_ip():
    try:
        # Create a dummy socket to detect the preferred outbound IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        # We connect to a public DNS IP (doesn't send actual packets)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        # Fallback to local hostname if offline
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

def update_env(new_ip):
    env_path = '.env'
    if not os.path.exists(env_path):
        print(f"Error: {env_path} not found.", file=sys.stderr)
        return False

    with open(env_path, 'r') as f:
        lines = f.readlines()

    updated = False
    new_lines = []
    
    defaults = ['localhost', '127.0.0.1']
    if new_ip not in defaults:
        new_hosts = defaults + [new_ip]
    else:
        new_hosts = defaults
        
    for line in lines:
        if line.startswith('ALLOWED_HOSTS='):
            print(f"Syncing .env: ALLOWED_HOSTS set to {', '.join(new_hosts)}", file=sys.stderr)
            new_lines.append(f"ALLOWED_HOSTS={','.join(new_hosts)}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"\nALLOWED_HOSTS={','.join(new_hosts)}\n")
        print(f"Created ALLOWED_HOSTS in .env with {new_ip}", file=sys.stderr)

    with open(env_path, 'w') as f:
        f.writelines(new_lines)
    return True

if __name__ == "__main__":
    # If a valid IP is passed (not placeholder or empty), use it. Otherwise detect.
    if len(sys.argv) > 1 and sys.argv[1].strip() != "" and sys.argv[1] != "%IP%":
        ip = sys.argv[1].strip()
    else:
        ip = get_local_ip()
    
    update_env(ip)
    # Output only the IP to stdout so batch script can capture it if needed
    print(ip)
