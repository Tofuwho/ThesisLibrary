import sys
import os

def update_env(new_ip):
    env_path = '.env'
    if not os.path.exists(env_path):
        print(f"Error: {env_path} not found.")
        return

    with open(env_path, 'r') as f:
        lines = f.readlines()

    updated = False
    new_lines = []
    
    # Clean the list: keep localhost, 127.0.0.1, and the NEW current IP.
    # Remove other stale LAN IPs.
    defaults = ['localhost', '127.0.0.1']
    if new_ip not in defaults:
        new_hosts = defaults + [new_ip]
    else:
        new_hosts = defaults
        
    for line in lines:
        if line.startswith('ALLOWED_HOSTS='):
            print(f"Syncing .env: ALLOWED_HOSTS set to {', '.join(new_hosts)}")
            new_lines.append(f"ALLOWED_HOSTS={','.join(new_hosts)}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        # If ALLOWED_HOSTS wasn't found, append it
        new_lines.append(f"\nALLOWED_HOSTS={','.join(new_hosts)}\n")
        print(f"Created ALLOWED_HOSTS in .env with {new_ip}")

    with open(env_path, 'w') as f:
        f.writelines(new_lines)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        update_env(sys.argv[1])
    else:
        print("Usage: python update_env_ip.py <ip>")
