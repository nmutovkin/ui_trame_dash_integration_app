#!/usr/bin/env python3
"""
VTK WebGL Visualization Launcher
===============================
Convenient launcher for starting VTK server and WebGL client.
"""
import sys
import time
import subprocess
import signal
import threading
from pathlib import Path

class VTKWebGLLauncher:
    def __init__(self, vtk_host="localhost", vtk_port=8080, client_host="0.0.0.0", client_port=8052):
        self.vtk_host = vtk_host
        self.vtk_port = vtk_port
        self.vtk_ws_port = vtk_port + 1
        self.client_host = client_host
        self.client_port = client_port
        
        self.vtk_process = None
        self.client_process = None
        
    def start_vtk_server(self):
        """Start VTK geometry server"""
        print(f"🚀 Starting VTK Server on {self.vtk_host}:{self.vtk_port}")
        
        cmd = [
            sys.executable, "vtk_geometry_server.py",
            self.vtk_host, str(self.vtk_port), str(self.vtk_ws_port)
        ]
        
        self.vtk_process = subprocess.Popen(cmd)
        print(f"✅ VTK Server started (PID: {self.vtk_process.pid})")
        
    def start_client(self):
        """Start WebGL client"""
        print(f"🎮 Starting WebGL Client on {self.client_host}:{self.client_port}")
        
        cmd = [
            sys.executable, "webgl_vtk_client.py",
            self.vtk_host, str(self.vtk_port), 
            self.client_host, str(self.client_port)
        ]
        
        self.client_process = subprocess.Popen(cmd)
        print(f"✅ WebGL Client started (PID: {self.client_process.pid})")
        
    def wait_for_vtk_server(self, timeout=10):
        """Wait for VTK server to be ready"""
        import socket
        
        print("🔄 Waiting for VTK server to be ready...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((self.vtk_host, self.vtk_port))
                sock.close()
                
                if result == 0:
                    print("✅ VTK server is ready!")
                    return True
                    
            except Exception:
                pass
                
            time.sleep(0.5)
            
        print("❌ VTK server failed to start within timeout")
        return False
        
    def stop_servers(self):
        """Stop both servers"""
        print("\n🛑 Stopping servers...")
        
        if self.client_process:
            print("🔄 Stopping WebGL client...")
            self.client_process.terminate()
            try:
                self.client_process.wait(timeout=5)
                print("✅ WebGL client stopped")
            except subprocess.TimeoutExpired:
                self.client_process.kill()
                print("⚠️ WebGL client force-killed")
                
        if self.vtk_process:
            print("🔄 Stopping VTK server...")
            self.vtk_process.terminate()
            try:
                self.vtk_process.wait(timeout=5)
                print("✅ VTK server stopped")
            except subprocess.TimeoutExpired:
                self.vtk_process.kill()
                print("⚠️ VTK server force-killed")
                
    def run(self):
        """Start both servers and wait"""
        print("🚀 VTK WebGL Visualization Launcher")
        print("=" * 50)
        
        # Check if files exist
        vtk_server_path = Path("vtk_geometry_server.py")
        client_path = Path("webgl_vtk_client.py")
        
        if not vtk_server_path.exists():
            print("❌ vtk_geometry_server.py not found!")
            return False
            
        if not client_path.exists():
            print("❌ webgl_vtk_client.py not found!")
            return False
        
        try:
            # Start VTK server
            self.start_vtk_server()
            
            # Wait for VTK server to be ready
            if not self.wait_for_vtk_server():
                self.stop_servers()
                return False
            
            # Start WebGL client
            time.sleep(2)  # Give VTK server time to fully initialize
            self.start_client()
            
            print("\n" + "=" * 50)
            print("🎉 Both servers are running!")
            print(f"📍 VTK Server:    http://{self.vtk_host}:{self.vtk_port}")
            print(f"🎮 WebGL Client:  http://{self.client_host}:{self.client_port}")
            print(f"🔌 WebSocket:     ws://{self.vtk_host}:{self.vtk_ws_port}")
            print("=" * 50)
            print("🎯 Open browser to: http://localhost:8052")
            print("⚠️  Press Ctrl+C to stop both servers")
            print("=" * 50)
            
            # Wait for processes
            while True:
                # Check if processes are still running
                if self.vtk_process.poll() is not None:
                    print("❌ VTK server has stopped unexpectedly")
                    break
                    
                if self.client_process.poll() is not None:
                    print("❌ WebGL client has stopped unexpectedly")
                    break
                    
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Received interrupt signal")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.stop_servers()
            
        return True

def main():
    """Main launcher function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="VTK WebGL Visualization Launcher")
    parser.add_argument("--vtk-host", default="localhost", help="VTK server host")
    parser.add_argument("--vtk-port", type=int, default=8080, help="VTK server port")
    parser.add_argument("--client-host", default="0.0.0.0", help="WebGL client host")
    parser.add_argument("--client-port", type=int, default=8052, help="WebGL client port")
    
    args = parser.parse_args()
    
    launcher = VTKWebGLLauncher(
        vtk_host=args.vtk_host,
        vtk_port=args.vtk_port,
        client_host=args.client_host,
        client_port=args.client_port
    )
    
    success = launcher.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 