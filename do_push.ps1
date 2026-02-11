# push from project folder using git -C (no cd needed)
$root = $PSScriptRoot
git -C $root add .
git -C $root commit -m "fix: summary_daily syntax and add User-Agent for Discord webhook"
git -C $root push origin main
