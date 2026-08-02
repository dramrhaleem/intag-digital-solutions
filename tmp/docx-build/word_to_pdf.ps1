param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath,
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'
$word = $null
$document = $null

try {
    $resolvedInput = (Resolve-Path -LiteralPath $InputPath).Path
    $resolvedOutput = [System.IO.Path]::GetFullPath($OutputPath)
    $outputDirectory = [System.IO.Path]::GetDirectoryName($resolvedOutput)
    [System.IO.Directory]::CreateDirectory($outputDirectory) | Out-Null

    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($resolvedInput, $false, $true)

    $document.Fields.Update() | Out-Null
    foreach ($section in $document.Sections) {
        foreach ($header in $section.Headers) {
            if ($header.Exists) { $header.Range.Fields.Update() | Out-Null }
        }
        foreach ($footer in $section.Footers) {
            if ($footer.Exists) { $footer.Range.Fields.Update() | Out-Null }
        }
    }

    # 17 = wdExportFormatPDF. Optimize for print and include document structure tags.
    $document.ExportAsFixedFormat(
        $resolvedOutput,
        17,
        $false,
        0,
        0,
        1,
        1,
        0,
        $true,
        $true,
        1,
        $true,
        $true,
        $false
    )
}
finally {
    if ($document -ne $null) {
        $document.Close(0)
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($document)
    }
    if ($word -ne $null) {
        $word.Quit()
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($word)
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
