param([string]$In, [string]$OutDocx, [string]$OutPdf)
# Opens the report in Word, updates the table of contents, writes real page numbers into the manual list of tables and list of figures
# (repeated until the numbers stop changing), removes the two "page numbers to be added" notes, saves a docx and exports a PDF.
$w = New-Object -ComObject Word.Application
$w.Visible = $false
$w.DisplayAlerts = 0
try {
  $doc = $w.Documents.Open($In, $false, $false)
  Start-Sleep -Seconds 3
  $doc.Repaginate()
  function Find-Para($doc, $text, $start) {
    for ($i = $start; $i -le $doc.Paragraphs.Count; $i++) { if ($doc.Paragraphs.Item($i).Range.Text.Trim() -eq $text) { return $i } }
    return -1
  }
  # remove the two notes first (they are only placeholders)
  foreach ($note in @("(In Word: right-click the table and choose Update Field to fill the page numbers.)", "[Page numbers to be added once the layout is final.]")) {
    for ($k = 0; $k -lt 3; $k++) {
      $i = Find-Para $doc $note 1
      if ($i -gt 0) { $doc.Paragraphs.Item($i).Range.Delete() | Out-Null }
    }
  }
  $iT = Find-Para $doc "LIST OF TABLES" 1
  $iF = Find-Para $doc "LIST OF FIGURES" 1
  $iAfter = Find-Para $doc "CHAPTER 1: INTRODUCTION" 1
  "list of tables at paragraph $iT, figures at $iF, chapter 1 at $iAfter"
  $width = $doc.PageSetup.PageWidth - $doc.PageSetup.LeftMargin - $doc.PageSetup.RightMargin
  $prev = ""
  for ($pass = 1; $pass -le 4; $pass++) {
    foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
    $doc.Repaginate()
    $iT = Find-Para $doc "LIST OF TABLES" 1
    $iF = Find-Para $doc "LIST OF FIGURES" 1
    $iAfter = Find-Para $doc "CHAPTER 1: INTRODUCTION" 1
    # caption pages: search after the first chapter heading
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
    "pass $pass : list lines changed = $changed, captions found = $($caps.Count)"
    if ($changed -eq 0) { break }
  }
  foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
  $doc.SaveAs2($OutDocx)
  $doc.ExportAsFixedFormat($OutPdf, 17)
  "pages: " + $doc.ComputeStatistics(2)
  $doc.Close($false)
} finally { try { if ($doc) { $doc.Saved = $true; $doc.Close(0) } } catch {}; try { $w.Quit(0) } catch {} }

