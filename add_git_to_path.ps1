# 将Git添加到系统PATH环境变量的PowerShell脚本
# 需要以管理员身份运行

$gitPath = "C:\Program Files\Git\cmd"
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

if ($currentPath -notlike "*$gitPath*") {
    [Environment]::SetEnvironmentVariable("Path", "$currentPath;$gitPath", "User")
    Write-Host "Git路径已添加到用户环境变量PATH中" -ForegroundColor Green
    Write-Host "请重启PowerShell或VS Code使更改生效" -ForegroundColor Yellow
} else {
    Write-Host "Git路径已存在于环境变量中" -ForegroundColor Green
}

