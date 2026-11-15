package store

// currentVersion is the note file format. Bump it, and teach migrate the step, when Note changes.
const currentVersion = 1

// migrate upgrades every note in dir to currentVersion. Version 1 is the first format, so there's
// nothing to upgrade yet.
func migrate(dir string) error {
	_ = dir
	return nil
}
