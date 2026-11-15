package main

import (
	"fmt"
	"os"

	"example.com/notes/internal/store"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: notes add <text> | notes list")
		os.Exit(2)
	}
	s, err := store.Open()
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	switch os.Args[1] {
	case "add":
		err = s.Add(os.Args[2])
	case "list":
		var notes []store.Note
		notes, err = s.List()
		for _, n := range notes {
			fmt.Println(n.Text)
		}
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
