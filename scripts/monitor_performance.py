#!/usr/bin/env python3
"""
Performance monitoring script for MJSRecon
"""

import psutil
import time
import os
import sys
from datetime import datetime

def monitor_performance():
    """Monitor system performance during validation"""
    print("🔍 Performance Monitor Started")
    print("=" * 50)
    
    try:
        while True:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            
            # Get Python processes
            python_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    if 'python' in proc.info['name'].lower():
                        python_processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Clear screen (optional)
            os.system('clear' if os.name == 'posix' else 'cls')
            
            # Print current time
            print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
            print("=" * 50)
            
            # System stats
            print(f"🖥️  CPU Usage: {cpu_percent}%")
            print(f"💾 Memory Usage: {memory.percent}% ({memory.used // 1024 // 1024}MB / {memory.total // 1024 // 1024}MB)")
            print(f"🔌 Swap Usage: {psutil.swap_memory().percent}%")
            
            # Python processes
            if python_processes:
                print("\n🐍 Python Processes:")
                for proc in python_processes:
                    print(f"  PID {proc['pid']}: {proc['name']} - CPU: {proc['cpu_percent']}% | RAM: {proc['memory_percent']:.1f}%")
            else:
                print("\n🐍 No Python processes found")
            
            # Network connections
            try:
                connections = psutil.net_connections()
                http_connections = [c for c in connections if c.status == 'ESTABLISHED' and c.raddr and c.raddr.port in [80, 443, 8080]]
                print(f"\n🌐 Active HTTP Connections: {len(http_connections)}")
            except:
                pass
            
            print("\n" + "=" * 50)
            print("Press Ctrl+C to stop monitoring")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n✅ Monitoring stopped")

if __name__ == "__main__":
    monitor_performance() 