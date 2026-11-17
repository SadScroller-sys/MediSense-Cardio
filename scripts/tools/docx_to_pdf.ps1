param([string]$In, [string]$Out)
$w = New-Object -ComObject Word.Application
$w.Visible = $false
try {
  $d = $w.Documents.Open($In, $false, $true)
  $d.ExportAsFixedFormat($Out, 17)
  "pages: " + $d.ComputeStatistics(2)
  $d.Close($false)
} finally { $w.Quit() }
