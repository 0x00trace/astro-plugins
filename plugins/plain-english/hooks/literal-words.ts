// Figures of speech in commit messages and GitHub text: the words, what to write in their place,
// and which commands write such text. register.ts refuses a Bash command whose text uses one.

// A figure of speech and the literal words to write in its place. Each pattern matches whole words,
// in any case. When only part of a match is the figure, the group named `w` holds that part.
export type Rule = readonly [pattern: RegExp, literal: string]

const PASS_FAIL = '"the tests pass" or "the tests fail", and name the check'

export const RULES: readonly Rule[] = [
  [/\b(land|lands|landed|landing)\b(?! page)/, '"merge" or "is merged" for a pull request; "is written to", "reaches" or "arrives" for data'],
  [/\b(shipped|shipping|(?:to|can|will|and|then|before|after|not|we|let's)\s+ship)\b/, '"release", "include" or "is included in"'],
  [/\b(ci|checks?|tests?|builds?|pipeline|suite)\b[^.\n]{0,20}\b(?<w>green|red)\b/, PASS_FAIL],
  [/\b(?<w>green|red)\s+(ci|checks?|builds?|runs?)\b/, PASS_FAIL],
  [/\b(fix|change|result|claim|finding|assumption|reasoning|theory|argument|conclusion|plan)\s+(still\s+)?(holds|held|stands|stood)\b/, '"is still correct" or "still works", and say which test shows it'],
  [/\b(pr|pull request|fix|patch|branch|review|comment)\s+(is|are)\s+up\b/, '"is posted" or "is open"'],
  [/\b(program|process|script|tests?|loop|requests?|retry|command|server|client|runner|job|github|ci|build)\s+(gives?|gave|giving)\s+up\b/, '"stops", "fails" or "returns an error"'],
  [/\bunblock(s|ed|ing)?\b/, '"lets ... start" or "is needed before ..."'],
  [/\blong shot\b/, '"unlikely"'],
  [/\blow[- ]hanging fruit\b/, '"the easiest changes"'],
  [/\bheavy lifting\b/, '"most of the work"'],
  [/\bmoving parts\b/, '"parts" or "components", and name them'],
  [/\bunder the hood\b/, '"inside" or "in the implementation"'],
  [/\brabbit hole\b/, '"a long investigation"'],
  [/\bsilver bullet\b/, '"a complete fix"'],
  [/\bsmoking gun\b/, '"the evidence" or "the cause"'],
  [/\bred herring\b/, '"unrelated" or "not the cause"'],
  [/\bpunt(s|ed|ing)?\b/, '"postpone" or "leave for later"'],
  [/\bfor free\b/, '"with no extra work" or "with no extra cost"'],
  [/\bin the weeds\b/, '"in detail"'],
  [/\b(rock-solid|bulletproof|battle-tested|robust|seamless(ly)?(?! loops?)|elegant(ly)?)\b/, 'a literal description of what the code does, or nothing'],
]

// Commands whose text other people read: commit and tag messages, and pull request, issue, review,
// comment and release text. `gh api` counts only when it sends fields or a body.
const WRITES_TEXT = [
  /\bgit\b(\s+-[cC]\s+\S+)*\s+(commit|tag)\b/,
  /\bgh\s+(pr\s+(create|edit|comment|review)|issue\s+(create|edit|comment)|release\s+(create|edit))\b/,
  /\bgh\s+api\b.*\s(-f|-F|--field|--raw-field|--input|-X\s*(POST|PATCH|PUT)|--method\s*(POST|PATCH|PUT))\b/s,
]

export function writesText(command: string) {
  return WRITES_TEXT.some(pattern => pattern.test(command))
}

// The command's words as the shell splits them, quotes removed. Shell operators split words too.
// It needs only to find flags and their values, so it doesn't expand anything.
export function words(command: string) {
  const out: string[] = []
  let word = ''
  let started = false
  let quote = ''
  for (let i = 0; i < command.length; i++) {
    const c = command.charAt(i)
    if (quote === "'") {
      if (c === "'") quote = ''
      else word += c
    } else if (quote === '"') {
      if (c === '"') quote = ''
      else if (c === '\\' && '"\\$`'.includes(command.charAt(i + 1))) word += command.charAt(++i)
      else word += c
    } else if (c === "'" || c === '"') {
      quote = c
      started = true
    } else if (c === '\\' && i + 1 < command.length) {
      word += command.charAt(++i)
      started = true
    } else if (/\s/.test(c) || ';&|<>()'.includes(c)) {
      if (started) out.push(word)
      word = ''
      started = false
    } else {
      word += c
      started = true
    }
  }
  if (started) out.push(word)
  return out
}

const FILE_FLAGS = new Set(['-F', '--file', '--body-file', '--notes-file'])

// The files a command reads its message or body from: `-F`, `--file`, `--body-file` and
// `--notes-file`, and a field given as `name=@file`. A `-` is standard input, whose text is
// already in the command when it comes from a heredoc.
export function textFiles(command: string) {
  const all = words(command)
  const files: string[] = []
  all.forEach((word, i) => {
    const value = all[i + 1]
    if (FILE_FLAGS.has(word) && value !== undefined) files.push(value)
    const [, , long] = word.match(/^(--file|--body-file|--notes-file)=(.+)$/) ?? []
    if (long) files.push(long)
    const [, field] = word.match(/^[\w.-]+=@(.+)$/) ?? []
    if (field) files.push(field)
  })
  return files.filter(file => file !== '-' && !/^[\w.-]+=@/.test(file))
}

// The text with code taken out: fenced blocks, inline code (also with the backticks escaped, as
// in a shell's double quotes), and paths and URLs, which are names.
export function prose(text: string) {
  return text
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/\\`[^`\n]*?\\`/g, ' ')
    .replace(/`[^`\n]*`/g, ' ')
    .replace(/\S*[/\\]\S*/g, ' ')
}

// Each figure of speech in the text, in the order found, with the literal words to write.
export function figures(text: string) {
  const found = new Map<string, string>()
  const plain = prose(text)
  for (const [pattern, literal] of RULES) {
    for (const match of plain.matchAll(new RegExp(pattern.source, 'gi'))) {
      const word = (match.groups?.w ?? match[0]).toLowerCase()
      if (!found.has(word)) found.set(word, literal)
    }
  }
  return found
}

// What Claude reads when a command is refused: each figure and its literal words.
export function refusal(found: ReadonlyMap<string, string>) {
  const lines = [...found].map(([word, literal]) => `- "${word}": write ${literal}`)
  return [
    'This commit message or GitHub text uses figures of speech. Rewrite it in literal words, then run the command again:',
    ...lines,
    'If a word is the literal name of a thing, or you are quoting the word itself, put it in backticks.',
  ].join('\n')
}
