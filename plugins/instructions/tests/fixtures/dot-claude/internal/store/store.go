// Package store keeps notes as one JSON file each under NOTES_DIR.
package store

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

type Note struct {
	Version int       `json:"version"`
	Text    string    `json:"text"`
	Created time.Time `json:"created"`
}

type Store struct{ dir string }

func Open() (*Store, error) {
	dir := os.Getenv("NOTES_DIR")
	if dir == "" {
		home, err := os.UserHomeDir()
		if err != nil {
			return nil, fmt.Errorf("find home: %w", err)
		}
		dir = filepath.Join(home, ".notes")
	}
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return nil, fmt.Errorf("create %s: %w", dir, err)
	}
	return &Store{dir: dir}, migrate(dir)
}

func (s *Store) Add(text string) error {
	n := Note{Version: currentVersion, Text: text, Created: time.Now()}
	data, err := json.Marshal(n)
	if err != nil {
		return fmt.Errorf("encode note: %w", err)
	}
	name := filepath.Join(s.dir, fmt.Sprintf("%d.json", n.Created.UnixNano()))
	if err := os.WriteFile(name, data, 0o644); err != nil {
		return fmt.Errorf("write note: %w", err)
	}
	return nil
}

func (s *Store) List() ([]Note, error) {
	files, err := filepath.Glob(filepath.Join(s.dir, "*.json"))
	if err != nil {
		return nil, fmt.Errorf("list notes: %w", err)
	}
	var notes []Note
	for _, f := range files {
		data, err := os.ReadFile(f)
		if err != nil {
			return nil, fmt.Errorf("read %s: %w", f, err)
		}
		var n Note
		if err := json.Unmarshal(data, &n); err != nil {
			return nil, fmt.Errorf("decode %s: %w", f, err)
		}
		notes = append(notes, n)
	}
	return notes, nil
}
