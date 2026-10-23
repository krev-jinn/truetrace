param (
    [string]$DocName = "docs\TrueTrace_PPT_Presentation_Content.docx"
)

$docPath = (Resolve-Path $DocName).Path
$pdfPath = [System.IO.Path]::ChangeExtension($docPath, ".pdf")

try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $doc = $word.Documents.Open($docPath)
    $pages = $doc.ComputeStatistics(2)
    Write-Host "Total Pages: $pages"
    $doc.SaveAs($pdfPath, 17)
    Write-Host "Saved PDF to $pdfPath"
    $doc.Close($false)
    $word.Quit()
} catch {
    Write-Host "Error during Word execution: $_"
}
