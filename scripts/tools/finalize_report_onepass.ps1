param([string]$In, [string]$OutPdf)
# One-pass version of finalize_report.ps1 for a report that is already finished (no placeholder notes to remove): updates the table of contents, writes the real page number of every caption into the manual
# list of tables and list of figures ONCE, saves the docx in place and exports a PDF. The full script hung in its second pass on this document.
$w = New-Object -ComObject Word.Application
$w.Visible = $false
$w.DisplayAlerts = 0
try {
  $doc = $w.Documents.Open($In, $false, $false)
  Start-Sleep -Seconds 3
  foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
  $doc.Repaginate()
  function Find-Para($doc, $text, $start) {
    for ($i = $start; $i -le $doc.Paragraphs.Count; $i++) { if (("" + $doc.Paragraphs.Item($i).Range.Text).Trim() -eq $text) { return $i } }
    return -1
  }
  $iT = Find-Para $doc "LIST OF TABLES" 1
  $iF = Find-Para $doc "LIST OF FIGURES" 1
  $iAfter = Find-Para $doc "CHAPTER 1: INTRODUCTION" 1
  "list of tables at $iT, figures at $iF, chapter 1 at $iAfter"
  if ($iT -lt 1 -or $iF -lt 1 -or $iAfter -lt 1) { throw "headings not found" }
  $width = $doc.PageSetup.PageWidth - $doc.PageSetup.LeftMargin - $doc.PageSetup.RightMargin
  $caps = @{}
  for ($i = $iAfter; $i -le $doc.Paragraphs.Count; $i++) {
    $p = $doc.Paragraphs.Item($i)
    $t = ("" + $p.Range.Text).Trim()
    if ($t -match '^(Table|Figure) ([0-9A-Z]+\.[0-9]+):') {
      $key = $Matches[1] + " " + $Matches[2]
      if (-not $caps.ContainsKey($key)) { $caps[$key] = $p.Range.Information(3) }
    }
  }
  $changed = 0
  foreach ($range in @(@(($iT + 1), ($iF - 1)), @(($iF + 1), ($iAfter - 1)))) {
    for ($i = $range[0]; $i -le $range[1]; $i++) {
      $p = $doc.Paragraphs.Item($i)
      $t = ("" + $p.Range.Text).Trim()
      $t = ($t -split "`t")[0]
      if ($t -match '^(Table|Figure) ([0-9A-Z]+\.[0-9]+):') {
        $key = $Matches[1] + " " + $Matches[2]
        if ($caps.ContainsKey($key)) {
          $new = $t + "`t" + $caps[$key]
          $r = $p.Range
          $r.MoveEnd(1, -1) | Out-Null
          if ($r.Text -ne $new) { $r.Text = $new; $changed++ }
          $p.TabStops.ClearAll()
          $p.TabStops.Add($width, 2, 1) | Out-Null
        }
      }
    }
  }
  "captions found = $($caps.Count), list lines changed = $changed"
  foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
  $doc.Save()
  $doc.ExportAsFixedFormat($OutPdf, 17)
  "pages: " + $doc.ComputeStatistics(2)
  $doc.Close($false)
} finally { try { if ($doc) { $doc.Saved = $true; $doc.Close(0) } } catch {}; try { $w.Quit(0) } catch {} }
