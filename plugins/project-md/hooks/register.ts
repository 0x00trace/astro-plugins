import type { EngineInterface, Register } from 'claude-code'

// The text placed above PROJECT.md's contents. It tells Claude what the file is and asks Claude to
// point out requests that conflict with the project's scope, as the old CLAUDE.md import line did.
export const LEAD = "PROJECT.md provides context for the project. It defines the project's purpose, goals, and any other information that helps Claude understand the project. If a request conflicts with the project's non-goals or constraints, point this out before starting work."

// Returns the path of PROJECT.md at the root of the session's git repo, or in the session's folder
// when the session is not in a repo. Returns undefined when the file does not exist.
async function projectFile($: EngineInterface) {
  const root = (await $.session.repo())?.root ?? (await $.session.root())
  const path = `${root.replace(/[\\/]+$/, '')}/PROJECT.md`
  return (await $.fs.exists(path)) ? path : undefined
}

export const register: Register = on => {
  // Adds PROJECT.md to the instruction files in the first message's context, in the same way that
  // a CLAUDE.md importing it would. Claude Code reads the file again after a compaction or /clear.
  // This hook runs once per conversation, not on every turn.
  on('prompt.context', async ($, e, next) => {
    const path = await projectFile($)
    if (path === undefined) return next(e)
    const below = await next(e)
    const files = below.instructionFiles ?? e.instructionFiles
    // Leave the context unchanged in two cases: the instruction files are unknown, which means a
    // hook further down rewrote the CLAUDE.md text, or a CLAUDE.md already imports PROJECT.md.
    if (files === undefined || files.some(file => file.path === path)) return below
    const text = await $.fs.read(path).catch(() => undefined)
    if (typeof text !== 'string' || text.trim() === '') return below
    return { ...below, instructionFiles: [...files, { path, kind: 'project' as const, content: `${LEAD}\n\n${text.trim()}` }] }
  })
}
