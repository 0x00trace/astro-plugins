package store

import "testing"

func TestAdd(t *testing.T) {
	t.Setenv("NOTES_DIR", t.TempDir())
	s, err := Open()
	if err != nil {
		t.Fatal(err)
	}
	if err := s.Add("Buy milk"); err != nil {
		t.Fatal(err)
	}
	notes, err := s.List()
	if err != nil {
		t.Fatal(err)
	}
	if len(notes) != 1 || notes[0].Text != "Buy milk" {
		t.Fatalf("got %+v", notes)
	}
}
