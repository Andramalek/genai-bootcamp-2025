$env:PATH = "C:\mingw64\bin;" + $env:PATH
$env:CGO_ENABLED = "1"

go run backend_go/cmd/server/main.go 