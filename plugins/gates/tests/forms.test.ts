import type { On } from 'claude-code'
import { expect, test } from 'claude-code/testing'

// Nothing sits beneath the plugin: this hook stands for the engine running the command.
function engine(on: On) {
  on('tool.call', () => ({ result: {} }))
}

// Other ways of writing what a gate refuses (#70), with the start of the reason it's refused
// with, and the near misses beside them that must still run (null). Each runs as its own test,
// so a miss names itself.
const FORMS: [string, string | null][] = [
  // Only a bracket in the pgrep -f or grep pattern itself keeps the pattern off the shell.
  ['[ -n "$(pgrep -f godot)" ] && kill $(pgrep -f godot)', 'This kills its own shell'],
  ['[[ -n $(pgrep -f godot) ]] && kill $(pgrep -f godot)', 'This kills its own shell'],
  ['pids=($(pgrep -f godot)); kill ${pids[0]}', 'This kills its own shell'],
  ['echo "[done]" && kill $(pgrep -f godot)', 'This kills its own shell'],
  ["echo \"[done]\"; ps aux | grep godot | awk '{print $2}' | xargs kill", 'This kills its own shell'],
  ["[ -n \"$(pgrep -f '[g]odot')\" ] && kill $(pgrep -f godot)", 'This kills its own shell'],
  ['kill `pgrep -f godot` "${pids[0]}"', 'This kills its own shell'],
  ["echo \"[done]\" && kill $(pgrep -f '[g]odot')", null],
  ["kill `pgrep -f '[g]odot'` \"${pids[0]}\"", null],
  ["[ -n \"$(pgrep -f '[g]odot')\" ] && kill $(pgrep -f '[g]odot')", null],
  ["ps aux | grep '[g]odot' | awk '{print $2}' | xargs kill", null],

  // A line that ends in a backslash runs on into the next.
  ['kill \\\n  $(pgrep -f godot)', 'This kills its own shell'],
  ["kill \\\n  $(pgrep -f '[g]odot')", null],

  // A command after cd, in a subshell, in backticks or in a quoted script.
  ['(cd /tmp && pkill godot)', 'pkill kills every process'],
  ['sh -c "pkill godot"', 'pkill kills every process'],
  ['out=`pkill godot`', 'pkill kills every process'],
]

for (const [command, reason] of FORMS) {
  test(`${reason === null ? 'runs' : 'refuses'}: ${command.replaceAll('\n', '\\n')}`, async ($, on) => {
    engine(on)
    const ran = await $.tool.call({ tool: 'Bash', command })
    if (reason === null) {
      expect({ command, deny: ran.deny }).toEqual({ command, deny: undefined })
    } else {
      expect({ command, reason: ran.deny?.startsWith(reason) }).toEqual({ command, reason: true })
    }
  })
}
