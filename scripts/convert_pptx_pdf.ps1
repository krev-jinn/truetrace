$pptxPath = (Resolve-Path "docs\TrueTrace_Final_Review_Presentation.pptx").Path
$pdfPath = [System.IO.Path]::ChangeExtension($pptxPath, ".pdf")

try {
    $ppt = New-Object -ComObject PowerPoint.Application
    $pres = $ppt.Presentations.Open($pptxPath, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
    # 32 is ppSaveAsPDF
    $pres.SaveAs($pdfPath, 32)
    $pres.Close()
    $ppt.Quit()
    Write-Host "SUCCESS: Exported PPTX to PDF at $pdfPath"
} catch {
    Write-Host "PowerPoint COM note: $_"
}
