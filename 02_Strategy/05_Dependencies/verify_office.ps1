# 자동 생성(_source/build/template/deps.py, 원천 _source/build/deps.json) — 직접 수정 금지
# TAAS 교통사고 분석 — Windows 확인: 글꼴 · 실제 PowerPoint·Word·Excel로 번들의 Office 파일을 열어 본다(읽기 전용, 파일을 바꾸지 않음).
# 실행: 최상위 install.bat → V(확인만)  또는  이 파일 우클릭 → 'PowerShell에서 실행'
# 결과: 화면 + 같은 폴더 office_verify_report.txt  ·  종료 코드 = 실패 수(0이면 정상)
$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
$Dep = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = (Resolve-Path (Join-Path $Dep '..\..')).Path
$Report = Join-Path $Dep 'office_verify_report.txt'
$lines = New-Object System.Collections.Generic.List[string]
function Say([string]$t, [string]$c = 'Gray') { Write-Host $t -ForegroundColor $c; $lines.Add($t) }
$fail = 0; $skip = 0
Say "Office 파일 확인 — $Root" 'Cyan'
Say ("Windows " + [Environment]::OSVersion.Version + " · " + (Get-Date -Format 'yyyy-MM-dd HH:mm'))

# 1) 글꼴
Say ''; Say '[글꼴]' 'Cyan'
$fontDirs = @("$env:WINDIR\Fonts", "$env:LOCALAPPDATA\Microsoft\Windows\Fonts")
$Fonts = @(
  @{ Name = 'Malgun Gothic(맑은 고딕)'; Need = '필수'; Files = @('malgun.ttf') },
  @{ Name = 'Calibri · Cambria'; Need = '필수'; Files = @('calibri.ttf', 'cambria.ttc') }
)
foreach ($f in $Fonts) {
  $hit = $false
  foreach ($file in $f.Files) { foreach ($dir in $fontDirs) { if (Test-Path (Join-Path $dir $file)) { $hit = $true } } }
  if ($hit) { Say ("  [있음] " + $f.Name) 'Green' }
  elseif ($f.Need -eq '필수') { Say ("  [없음] " + $f.Name + " — 필수(Windows/Office 기본 글꼴: Windows 업데이트 또는 Office 복구로 설치)") 'Red'; $fail++ }
  else { Say ("  [없음] " + $f.Name + " — 선택(다른 글꼴로 대체되어 보임, 내용 영향 없음)") 'Yellow' }
}

# 2) 파일 모으기(.git·_work·node_modules 제외)
$files = Get-ChildItem -Path $Root -Recurse -File -Include *.pptx, *.docx, *.xlsx -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -notlike '~$*' -and $_.FullName -notmatch '\\(\.git|_work|node_modules)\\' }
Say ''; Say ("[Office 열기 시험] " + @($files).Count + "개") 'Cyan'

function Open-With([string]$prog, $group) {
  if (-not $group) { return }
  $app = $null
  try { $app = New-Object -ComObject $prog } catch { Say ("  $prog 없음 — " + @($group).Count + "개 시험 생략(Office 설치 필요)") 'Yellow'; $script:skip += @($group).Count; return }
  try {
    if ($prog -eq 'PowerPoint.Application') { $app.DisplayAlerts = 1 } elseif ($prog -eq 'Word.Application') { $app.Visible = $false; $app.DisplayAlerts = 0 } else { $app.Visible = $false; $app.DisplayAlerts = $false }
  } catch {}
  foreach ($f in $group) {
    $rel = $f.FullName.Substring($Root.Length).TrimStart('\')
    try {
      if ($prog -eq 'PowerPoint.Application') { $doc = $app.Presentations.Open($f.FullName, -1, 0, 0); $info = "슬라이드 " + $doc.Slides.Count; $doc.Close() }
      elseif ($prog -eq 'Word.Application') { $doc = $app.Documents.Open($f.FullName, $false, $true, $false); $info = "쪽 " + $doc.ComputeStatistics(2); $doc.Close(0) }
      else { $doc = $app.Workbooks.Open($f.FullName, 0, $true); $info = "시트 " + $doc.Worksheets.Count; $doc.Close($false) }
      Say ("  [ OK ] " + $rel + " (" + $info + ")") 'Green'
    } catch {
      Say ("  [FAIL] " + $rel + " — " + $_.Exception.Message.Split([Environment]::NewLine)[0]) 'Red'; $script:fail++
    } finally { if ($doc) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($doc); $doc = $null } }
  }
  try { $app.Quit() } catch {}
  [void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)
}
Open-With 'PowerPoint.Application' ($files | Where-Object { $_.Extension -eq '.pptx' })
Open-With 'Word.Application' ($files | Where-Object { $_.Extension -eq '.docx' })
Open-With 'Excel.Application' ($files | Where-Object { $_.Extension -eq '.xlsx' })
[GC]::Collect(); [GC]::WaitForPendingFinalizers()

Say ''
if ($fail -eq 0 -and $skip -eq 0) { Say '결과: 모두 정상 — 글꼴과 모든 파일이 이 PC의 Office에서 열립니다' 'Green' }
elseif ($fail -eq 0) { Say ("결과: 실패 없음, 단 Office가 없어 " + $skip + "개는 열기 시험을 못 했습니다") 'Yellow' } else { Say ("결과: 실패 " + $fail + "건 — 이 보고서를 프로젝트 담당에게 보내 주세요: " + $Report) 'Red' }
[IO.File]::WriteAllLines($Report, $lines, (New-Object Text.UTF8Encoding $true))
exit $fail
