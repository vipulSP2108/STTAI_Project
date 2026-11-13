param([Parameter(ValueFromRemainingArguments=$true)][string[]]$DvcArguments)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$downloads = Join-Path $env:USERPROFILE 'Downloads'
$remotePath = if ($env:STTAI_DVC_REMOTE) { $env:STTAI_DVC_REMOTE } else { Join-Path $downloads 'STTAI_Project_DVC' }
$cachePath = if ($env:STTAI_DVC_CACHE) { $env:STTAI_DVC_CACHE } else { Join-Path $downloads 'STTAI_Project_DVC_Cache' }
New-Item -ItemType Directory -Path $remotePath,$cachePath -Force | Out-Null
docker image inspect sttai-dvc-tools:3.67.1 *> $null
if ($LASTEXITCODE -ne 0) {
    docker build -t sttai-dvc-tools:3.67.1 -f (Join-Path $PSScriptRoot 'Dockerfile.dvc-tools') $projectRoot
    if ($LASTEXITCODE -ne 0) { throw 'DVC helper image build failed' }
}
docker run --rm --mount "type=bind,source=$projectRoot,target=/work" --mount "type=bind,source=$remotePath,target=/dvc_remote" --mount "type=bind,source=$cachePath,target=/dvc_cache" sttai-dvc-tools:3.67.1 @DvcArguments
exit $LASTEXITCODE
