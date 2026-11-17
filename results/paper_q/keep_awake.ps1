Add-Type -Namespace W -Name P -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);'
while ($true) { [void][W.P]::SetThreadExecutionState(0x80000001); Start-Sleep 30 }
