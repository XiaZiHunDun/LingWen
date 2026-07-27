// scripts/fix-testid-class-sync.cjs
// Codemod to fix testid-class-sync ESLint warnings across .vue files.
// Fix types:
//   1) data-testid="x" exists but class doesn't contain "x" → add "x" to class
//   2) Interactive element has class "x" matching another testid in same file,
//      but no data-testid="x" → add data-testid="x"

const fs = require('fs')
const path = require('path')
const { execSync } = require('child_process')

// Run ESLint and get structured output
const frontendDir = path.resolve(__dirname, '..')
const eslintOutput = execSync(
  `npx eslint src/ -f json`,
  { cwd: frontendDir, maxBuffer: 10 * 1024 * 1024 },
).toString()

let eslintData
try {
  eslintData = JSON.parse(eslintOutput)
} catch (e) {
  console.error('Failed to parse ESLint output:', e.message)
  process.exit(1)
}

// Collect all warnings grouped by file
const fileWarnings = {}
eslintData.forEach(file => {
  const syncWarnings = file.messages.filter(
    m => m.ruleId === 'custom/testid-class-sync',
  )
  if (syncWarnings.length > 0) {
    fileWarnings[file.filePath] = syncWarnings
  }
})

console.log(`Found ${Object.keys(fileWarnings).length} files with ${Object.values(fileWarnings).reduce((s, m) => s + m.length, 0)} warnings`)

let totalFixed = 0

for (const [filePath, warnings] of Object.entries(fileWarnings)) {
  let content = fs.readFileSync(filePath, 'utf-8')
  let modified = false

  // Type 1: data-testid="x" must have class containing "x"
  for (const w of warnings) {
    if (w.message.includes('必须加 class 镜像')) {
      // Extract the testid from the message
      const match = w.message.match(/data-testid="([^"]+)" 必须加 class 镜像/)
      if (!match) continue
      const testid = match[1]
      const line = w.line

      // Read the specific line
      const lines = content.split('\n')
      if (line > lines.length) continue

      let targetLine = lines[line - 1]

      // Check if class attribute exists on this line
      if (targetLine.includes('class=')) {
        // Add testid to existing class
        targetLine = targetLine.replace(
          /class="([^"]*)"/,
          (match, existing) => {
            const classes = existing.split(/\s+/).filter(Boolean)
            if (!classes.includes(testid)) {
              classes.push(testid)
              modified = true
              return `class="${classes.join(' ')}"`
            }
            return match
          },
        )
        lines[line - 1] = targetLine
      } else {
        // No class attribute - need to find the right spot to insert it
        // Look for data-testid and add class after it
        // Match data-testid="x" (possibly followed by space, >, or other attrs)
        // We need to insert class before the closing > or before the next attribute
        const dtRegex = new RegExp(`data-testid="${escapeRegex(testid)}"`)
        const dtMatch = targetLine.match(dtRegex)
        if (dtMatch) {
          // Insert class after data-testid attribute
          const insertPos = dtMatch.index + dtMatch[0].length
          // Check if next char is > or space
          const after = targetLine.substring(insertPos)
          const classInsert = ` class="${testid}"`
          
          // Handle different scenarios
          if (after.startsWith('>') || after.startsWith('/>')) {
            // Insert before the closing bracket
            targetLine = targetLine.slice(0, insertPos) + classInsert + ' ' + targetLine.slice(insertPos)
          } else {
            // Insert before next attribute or >
            targetLine = targetLine.slice(0, insertPos) + classInsert + targetLine.slice(insertPos)
          }
          lines[line - 1] = targetLine
          modified = true
        }
      }

      if (modified) {
        content = lines.join('\n')
      }
    }
  }

  // Type 2: class must contain "x" (kebab-case mirror testid)
  // This means class exists but doesn't contain the testid token
  for (const w of warnings) {
    if (w.message.includes('class 必须包含')) {
      const match = w.message.match(/class 必须包含 "([^"]+)"/)
      if (!match) continue
      const testid = match[1]
      const line = w.line

      const lines = content.split('\n')
      if (line > lines.length) continue

      let targetLine = lines[line - 1]

      // Find class attribute and add the token
      if (targetLine.includes('class=')) {
        const classMatch = targetLine.match(/class="([^"]*)"/)
        if (classMatch) {
          const classes = classMatch[1].split(/\s+/).filter(Boolean)
          if (!classes.includes(testid)) {
            classes.push(testid)
            targetLine = targetLine.replace(
              /class="[^"]*"/,
              `class="${classes.join(' ')}"`,
            )
            lines[line - 1] = targetLine
            content = lines.join('\n')
            modified = true
          }
        }
      }
    }
  }

  if (modified) {
    fs.writeFileSync(filePath, content, 'utf-8')
    const relPath = path.relative(frontendDir, filePath)
    console.log(`  Fixed: ${relPath}`)
    totalFixed++
  }
}

console.log(`\nFixed ${totalFixed} files.`)

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}
