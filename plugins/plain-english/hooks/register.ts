import type { EngineInterface, Register } from 'claude-code'
import { figures, refusal, textFiles, writesText } from './literal-words'

// The output style's file, so the main conversation and the subagents read the same text.
export const STYLE = 'output-styles/plain-english.md'

// The style's instructions: the file less the frontmatter Claude Code reads its settings from.
export function instructions(file: string) {
  return file.replace(/^---\r?\n[\s\S]*?\r?\n---[ \t]*(\r?\n|$)/, '').trim()
}

async function read($: EngineInterface) {
  return instructions(await $.fs.read(`${$.plugin.root}/${STYLE}`))
}

export const register: Register = on => {
  // The output style reaches the main conversation and forks, which inherit its system prompt.
  // Every other subagent runs on a system prompt of its own, without the style, so it gets the same
  // instructions as SubagentStart context instead. An agent-team teammate gets them twice: it is
  // sent its lead's system prompt, style included, and SubagentStart can't tell it apart, since it
  // names a teammate by the name it was given. If the hook fails, Claude Code skips it and the
  // subagent starts without them.
  on('classic.SubagentStart', async ($, e, next) => {
    const below = await next(e)
    if (e.agent_type === 'fork') return below
    const style = await read($).catch(() => undefined)
    if (!style) return below
    return { ...below, additionalContext: [...(below.additionalContext ?? []), style] }
  })

  // A commit message, pull request or issue stays in a project's history, where other people read
  // it. A Bash command that writes one with a figure of speech is refused, with the literal words to
  // write, so Claude rewrites the text and runs the command again. The text is the command itself,
  // heredocs included, and each file the command reads its message or body from. If the check
  // fails, the command runs as it would without the plugin.
  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    if (!writesText(e.command)) return next(e)
    const texts = [e.command]
    for (const path of textFiles(e.command)) {
      const full = path.startsWith('/') ? path : `${await $.session.cwd()}/${path}`
      const text = await $.fs.read(full).catch(() => undefined)
      if (text !== undefined) texts.push(text)
    }
    const found = figures(texts.join('\n'))
    return found.size ? { deny: refusal(found) } : next(e)
  }).catch(($, e, next) => next(e))
}
