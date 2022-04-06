

$LPT = @{}

# Get Parallel Port objects:
$LPT.ParallelPort = Get-WmiObject Win32_ParallelPort

# Using the Parallel Port objects' PNPDeviceID, get the PNPEntity, which contains
# usefull metadata. Such as, the brand name.
$LPT.PnPEntity = Get-WmiObject Win32_PnPEntity | ?{$_.PNPDeviceID -eq $LPT.ParallelPort.PNPDeviceID}

# Using the PNPDeviceID, get the PNPAllocatedResource:
$LPT.PNPAllocatedResource = Get-WmiObject Win32_PNPAllocatedResource | Where-Object {($_.Dependent -replace '\\+', '\') -Like "*$($LPT.ParallelPort.PNPDeviceID)*"}

# From the PNPAllocatedResource, get the adresses:
$LPT.Address = ($LPT.PNPAllocatedResource.Antecedent | Select-String -Pattern '(?<=StartingAddress=")\d{4,8}').Matches.Value
$LPT.AddressHex = $LPT.Address | ForEach-Object {(‘{0:x}‘ -f [int]$_).ToUpper()}


# Try using a wmi library, like:  https://pypi.org/project/WMI/