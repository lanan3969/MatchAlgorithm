"""查找占用串口的进程"""
import subprocess
import re

def find_processes_using_com_port():
    """使用 handle.exe 或 PowerShell 查找占用 COM 口的进程"""
    
    print("\n" + "=" * 80)
    print("正在查找占用串口的进程...")
    print("=" * 80)
    
    try:
        # 方法1: 使用 PowerShell Get-Process 和 WMI
        print("\n【方法1】通过 WMI 查找串口占用进程...")
        
        # 查找所有可能相关的进程
        ps_command = """
        Get-Process | Where-Object {
            $_.ProcessName -match 'python|arduino|serial|putty|terminal|com|unity'
        } | Select-Object Id, ProcessName, Path | Format-List
        """
        
        result = subprocess.run(
            ['powershell', '-Command', ps_command],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.stdout:
            print(result.stdout)
        
        # 方法2: 列出所有 Python 进程
        print("\n【方法2】所有 Python 进程:")
        ps_python = "Get-Process python* -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, Path, StartTime | Format-Table"
        result = subprocess.run(
            ['powershell', '-Command', ps_python],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.stdout:
            print(result.stdout)
        else:
            print("  未找到 Python 进程")
        
        # 方法3: 检查设备管理器中的串口信息
        print("\n【方法3】串口设备详细信息:")
        wmic_command = 'wmic path Win32_SerialPort get Caption,DeviceID,Status'
        result = subprocess.run(
            wmic_command,
            capture_output=True,
            text=True,
            shell=True,
            timeout=5
        )
        
        if result.stdout:
            print(result.stdout)
        
    except subprocess.TimeoutExpired:
        print("⚠ 命令执行超时")
    except Exception as e:
        print(f"⚠ 执行出错: {e}")
    
    print("\n" + "=" * 80)
    print("提示：")
    print("=" * 80)
    print("1. 如果看到多个 Python 进程，可能是之前的程序没有正确退出")
    print("2. 使用任务管理器手动结束相关进程")
    print("3. 或运行下面的命令强制关闭所有 Python 进程（注意会关闭所有Python）：")
    print("   taskkill /F /IM python.exe")
    print("=" * 80)

if __name__ == "__main__":
    find_processes_using_com_port()


