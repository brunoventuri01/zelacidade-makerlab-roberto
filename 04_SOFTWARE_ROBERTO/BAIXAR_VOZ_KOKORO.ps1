$ErrorActionPreference = 'Stop'
$destino = Join-Path $PSScriptRoot 'models\kokoro'
New-Item -ItemType Directory -Force -Path $destino | Out-Null

$modelo = Join-Path $destino 'kokoro-v1.0.onnx'
$vozes = Join-Path $destino 'voices-v1.0.bin'

if (-not (Test-Path -LiteralPath $modelo)) {
    Invoke-WebRequest -Uri 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx' -OutFile $modelo
}
if (-not (Test-Path -LiteralPath $vozes)) {
    Invoke-WebRequest -Uri 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin' -OutFile $vozes
}

Write-Host 'Modelo Kokoro e vozes pt-BR instalados.' -ForegroundColor Green
