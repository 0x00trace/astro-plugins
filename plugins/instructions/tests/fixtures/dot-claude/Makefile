.PHONY: build test lint

build:
	go build -o bin/notes ./cmd/notes

test:
	go test ./...

lint:
	go vet ./...
	staticcheck ./...
