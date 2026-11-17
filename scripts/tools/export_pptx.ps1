param([string]$In, [string]$OutPdf, [string]$OutPng)
# Exports a deck with PowerPoint (COM) to a PDF and a PNG of slide 1 (preview). Closes only the PowerPoint instance it started.
$app = New-Object -ComObject PowerPoint.Application
try {
  $pres = $app.Presentations.Open($In, $true, $false, $false)
  if ($OutPdf) { $pres.SaveAs($OutPdf, 32) }
  if ($OutPng) { $pres.Slides.Item(1).Export($OutPng, "PNG", 1500, 2121) }
  "slide size (pt): " + $pres.PageSetup.SlideWidth + " x " + $pres.PageSetup.SlideHeight
  $pres.Close()
} finally { $app.Quit() }
