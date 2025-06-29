#!/usr/bin/env python3
"""
Unified VTK XDMF Dash WebGL Application Launcher
===============================================
Simple launcher for the consolidated VTK XDMF visualization app.
"""
import sys
from vtk_dash_app import VTKXDMFDashApp

def main():
    """Launch the unified VTK XDMF Dash application"""
    print("🚀 Launching Unified VTK XDMF Dash WebGL Application")
    print("=" * 60)
    
    # Parse command line arguments
    host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8050
    debug = len(sys.argv) > 3 and sys.argv[3].lower() == 'debug'
    
    print(f"🌐 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🐛 Debug: {debug}")
    print("=" * 60)
    
    # Create and run the unified application
    app = VTKXDMFDashApp(host=host, port=port)
    app.run(debug=debug)

if __name__ == "__main__":
    main() 