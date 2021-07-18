npx prettier --write "./**/*.yml"
command -v yapf3 >/dev/null 2>&1 && alias yapf=yapf3
yapf --recursive --in-place .
