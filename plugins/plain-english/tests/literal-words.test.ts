import type { On } from 'claude-code'
import { expect, test } from 'claude-code/testing'
import { figures, textFiles, words } from '../hooks/literal-words'

type Setup = {
  // The files the engine can read, by absolute path.
  files?: Record<string, string>
  // The session's directory.
  cwd?: string
}

// An engine with a shell that records each command it runs, and the files in `files`.
function engine(on: On, { files = {}, cwd = '/work' }: Setup = {}) {
  const ran: string[] = []
  on('tool.call', { tool: 'Bash' }, (_, e) => {
    ran.push(e.command)
    return { result: { stdout: '', stderr: '', interrupted: false } }
  })
  on('fs.read', (_, e) => {
    const text = files[String(e.path)]
    if (text === undefined) throw new Error('ENOENT')
    return { value: text }
  })
  on('session.cwd', () => ({ value: cwd }))
  return ran
}

test('a commit message with a figure of speech is refused with the literal words, and git never runs', async ($, on) => {
  const ran = engine(on)
  const result = await $.tool.call({ tool: 'Bash', command: 'git commit -m "fix(gfx): when this lands, the game boots"' })
  expect(result.deny ?? result.text).toContain('"lands": write "merge" or "is merged"')
  expect(ran).toEqual([])
})

test('a literal commit message runs', async ($, on) => {
  const ran = engine(on)
  const command = 'git commit -m "fix(gfx): after #12 is merged, the game boots"'
  const result = await $.tool.call({ tool: 'Bash', command })
  expect(result.deny).toBeUndefined()
  expect(ran).toEqual([command])
})

test('a commit message in a heredoc is checked', async ($, on) => {
  const ran = engine(on)
  const command = "git commit -F - <<'EOF'\nfeat(nv): start the gpu driver\n\nThe fix holds and CI is green.\nEOF"
  const result = await $.tool.call({ tool: 'Bash', command })
  const reason = result.deny ?? result.text
  expect(reason).toContain('"fix holds"')
  expect(reason).toContain('"green"')
  expect(ran).toEqual([])
})

test('a command that writes no commit or GitHub text runs whatever it says', async ($, on) => {
  const ran = engine(on)
  for (const command of ['echo "the write lands nowhere"', 'gh pr view 12 --json body', "gh api repos/o/r/pulls --jq '.[].title'"]) {
    const result = await $.tool.call({ tool: 'Bash', command })
    expect(result.deny).toBeUndefined()
  }
  expect(ran.length).toBe(3)
})

test('a pull request body file is read and checked, a relative path from the session directory', async ($, on) => {
  const ran = engine(on, { files: { '/work/body.md': 'Builds on #4.\n\nAfter #4 lands, rebase this branch.\n' } })
  const result = await $.tool.call({ tool: 'Bash', command: 'gh pr create --title "feat: add a reader" --body-file body.md' })
  expect(result.deny ?? result.text).toContain('"lands"')
  expect(ran).toEqual([])
})

test('an api field read from a file is checked', async ($, on) => {
  const ran = engine(on, { files: { '/tmp/c.md': 'The patch is up for review.' } })
  const result = await $.tool.call({ tool: 'Bash', command: 'gh api repos/o/r/issues/3/comments -F body=@/tmp/c.md' })
  expect(result.deny ?? result.text).toContain('"patch is up"')
  expect(ran).toEqual([])
})

test('a body file that cannot be read leaves the command text to check', async ($, on) => {
  const ran = engine(on)
  const command = 'gh pr create --title "feat: add a reader" --body-file missing.md'
  const result = await $.tool.call({ tool: 'Bash', command })
  expect(result.deny).toBeUndefined()
  expect(ran).toEqual([command])
})

test('figures finds each figure once, by the word that is the figure', () => {
  expect([...figures('When #3 lands, the write lands on index 0.').keys()]).toEqual(['lands'])
  expect([...figures('CI is green and the green build is cached.').keys()]).toEqual(['green'])
  expect([...figures('Ready to ship: the fix still holds.').keys()]).toEqual(['to ship', 'fix still holds'])
})

test('figures leaves literal words, code, paths and quoted names alone', () => {
  for (const text of [
    'feat: redesign the landing page',
    "Measure trips to another pilot's ship far out",
    'feat(music): make seamless loops with a local model',
    'The creature gives up and walks home.',
    'Add the `ship` flag and the `lands` field.',
    'Read files from /home/x/landing/ and https://example.com/shipped',
    'The register holds the address. The buffer is red-black tree ordered.',
  ]) {
    expect([...figures(text).keys()]).toEqual([])
  }
})

test('words splits as the shell does, quotes and escapes removed', () => {
  expect(words(`git commit -m "a \\"b\\" c" -m 'd e' f\\ g&&ls`)).toEqual(['git', 'commit', '-m', 'a "b" c', '-m', 'd e', 'f g', 'ls'])
})

test('textFiles names the files a command reads its message or body from', () => {
  expect(textFiles('git commit -F msg.txt')).toEqual(['msg.txt'])
  expect(textFiles('git commit -F -')).toEqual([])
  expect(textFiles('gh pr edit 3 --body-file=/tmp/b.md')).toEqual(['/tmp/b.md'])
  expect(textFiles('gh api x -F body=@c.md -F title=t')).toEqual(['c.md', 'title=t'])
})
