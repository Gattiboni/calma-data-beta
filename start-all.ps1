
# Abre backend em uma nova janela do PowerShell
Start-Process powershell.exe -ArgumentList '-NoExit', '-Command', 'Set-ExecutionPolicy -Scope Process Bypass -Force; .\scripts\start-backend.ps1'

# Abre frontend em outra nova janela do PowerShell
Start-Process powershell.exe -ArgumentList '-NoExit', '-Command', 'Set-ExecutionPolicy -Scope Process Bypass -Force; .\scripts\start-frontend.ps1'