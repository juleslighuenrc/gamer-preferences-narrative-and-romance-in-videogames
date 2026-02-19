$ErrorActionPreference = "Stop"

$gh = "C:\Program Files\GitHub CLI\gh.exe"
$git = "C:\Users\julia\AppData\Local\Microsoft\WinGet\Packages\Git.MinGit_Microsoft.Winget.Source_8wekyb3d8bbwe\cmd\git.exe"

$repoSlug = "gamer-preferences-narrative-and-romance-in-videogames"
$repoDescription = "Gamer Preferences: Narrative and Romance in Videogames"

Set-Location "$PSScriptRoot"

& $gh auth status | Out-Null

$currentRemote = (& $git remote) -contains "origin"
if ($currentRemote) {
    & $git remote remove origin
}

& $gh repo create $repoSlug --private --source . --remote origin --push --description $repoDescription
Write-Host "Repository created and pushed: $repoSlug" -ForegroundColor Green
