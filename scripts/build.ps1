param([switch]$Analyze, [string]$ClionRoot)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
$taskClion = if ($ClionRoot) { Join-Path $ClionRoot 'bin' } else { Join-Path $env:LOCALAPPDATA 'Programs/CLion/bin' }
if (-not (Test-Path $taskClion) -and -not $ClionRoot) {
    $taskClion = Join-Path $env:USERPROFILE 'AppData/Local/Programs/CLion/bin'
}
$taskCmake = Join-Path $taskClion 'cmake/win/x64/bin/cmake.exe'
$taskNinja = Join-Path $taskClion 'ninja/win/x64/ninja.exe'
$taskGcc = Join-Path $taskClion 'mingw/bin/gcc.exe'
if (-not (Test-Path $taskCmake)) { throw 'Toolchain CLion non trovata. Usare CMake con la propria toolchain.' }
$env:PATH = "$(Join-Path $taskClion 'mingw/bin');$env:PATH"
Push-Location $taskRoot
try {
    $taskFlags = if ($Analyze) { '-fanalyzer' } else { '' }
    $taskBuild = if ($Analyze) { 'build/analyze' } else { 'build/debug' }
    & $taskCmake -S . -B $taskBuild -G Ninja "-DCMAKE_MAKE_PROGRAM=$taskNinja" "-DCMAKE_C_COMPILER=$taskGcc" -DCMAKE_BUILD_TYPE=Debug "-DCMAKE_C_FLAGS=$taskFlags"
    if ($LASTEXITCODE) { throw 'Configurazione fallita' }
    & $taskCmake --build $taskBuild
    if ($LASTEXITCODE) { throw 'Build fallita' }
    & (Join-Path (Split-Path $taskCmake) 'ctest.exe') --test-dir $taskBuild --output-on-failure
    if ($LASTEXITCODE) { throw 'Test falliti' }
} finally { Pop-Location }
