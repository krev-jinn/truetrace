$docPath = (Resolve-Path "docs\TrueTrace_Final_Project_Report.docx").Path
$pdfPath = [System.IO.Path]::ChangeExtension($docPath, ".pdf")

try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $doc = $word.Documents.Open($docPath)
    # 2 is wdStatisticPages
    $pages = $doc.ComputeStatistics(2)
    Write-Host "Total Pages: $pages"
    # 17 is wdFormatPDF
    $doc.SaveAs($pdfPath, 17)
    Write-Host "Saved PDF to $pdfPath"
    $doc.Close($false)
    $word.Quit()
} catch {
    Write-Host "Error during Word execution: $_"
}
