#!/usr/bin/env python3
"""
Ollama API Proxy: WSL → Windows
Forward WSL's localhost:PORT to the Ollama service running on Windows.
Auto-discovers the Windows host IP from WSL's default gateway.

Usage:
    python3 wsl-ollama-proxy.py              # Default: listen on :11434
    python3 wsl-ollama-proxy.py 11434        # Custom local port
    python3 wsl-ollama-proxy.py 11434 8080   # Custom local + remote port
"""
import http.server
import http.client
import sys
import subprocess


def get_windows_ip():
    """Get the Windows host IP from WSL's default gateway."""
    try:
        result = subprocess.run(
            ["ip", "route", "show", "default"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip().split()[2]
    except Exception:
        print("ERROR: Could not determine Windows IP. Is this WSL2?", file=sys.stderr)
        sys.exit(1)


LOCAL_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 11434
REMOTE_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else LOCAL_PORT
WINDOWS_IP = get_windows_ip()
TARGET = (WINDOWS_IP, REMOTE_PORT)


class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            conn = http.client.HTTPConnection(*TARGET, timeout=10)
            conn.request("GET", self.path)
            resp = conn.getresponse()
            self.send_response(resp.status)
            for k, v in resp.getheaders():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(resp.read())
        except Exception as e:
            self.send_error(502, f"Proxy error: {e}")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            conn = http.client.HTTPConnection(*TARGET, timeout=120)
            conn.request("POST", self.path, body, dict(self.headers))
            resp = conn.getresponse()
            self.send_response(resp.status)
            for k, v in resp.getheaders():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(resp.read())
        except Exception as e:
            self.send_error(502, f"Proxy: {e}")

    def log_message(self, format, *args):
        """Suppress default logging to keep output clean."""
        pass


if __name__ == "__main__":
    print(f"Ollama proxy: 127.0.0.1:{LOCAL_PORT} → {WINDOWS_IP}:{REMOTE_PORT}")
    server = http.server.HTTPServer(("0.0.0.0", LOCAL_PORT), ProxyHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nProxy stopped.")
        server.server_close()
