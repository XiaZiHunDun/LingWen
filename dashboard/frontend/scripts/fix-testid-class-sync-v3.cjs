// scripts/fix-testid-class-sync-v3.cjs
// Handles multi-line Vue templates where class and data-testid may be on different lines.

const fs = require('fs')
const path = require('path')
const { execSync } = require('child_process')

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

// Collect all fixes needed
const classMissingToken = [] // {file, testid, line}  class exists but missing token
const driftFixes = [] // {file, testid, line}  class exists but no data-testid

eslintData.forEach(file => {
  file.messages.forEach(m => {
    if (m.ruleId !== 'custom/testid-class-sync') return
    if (m.message.includes('class 必须包含')) {
      const match = m.message.match(/class 必须包含 "([^"]+)"/)
      if (match) classMissingToken.push({ file: file.filePath, testid: match[1], line: m.line })
    } else if (m.message.includes('必加 data-testid')) {
      const match = m.message.match(/data-testid="([^"]+)"/)
      if (match) driftFixes.push({ file: file.filePath, testid: match[1], line: m.line })
    }
  })
})

console.log(`Found ${classMissingToken.length} class-must-contain fixes and ${driftFixes.length} drift fixes`)

// Group by file
const byFile = {}
for (const f of classMissingToken) {
  if (!byFile[f.file]) byFile[f.file] = []
  byFile[f.file].push(f)
}

let totalFixed = 0

for (const [filePath, fileFixes] of Object.entries(byFile)) {
  let content = fs.readFileSync(filePath, 'utf-8')
  let modified = false

  // Sort fixes from bottom to top to preserve line numbers
  fileFixes.sort((a, b) => b.line - a.line)

  for (const fix of fileFixes) {
    const testid = fix.testid
    const lineNum = fix.line
    const lines = content.split('\n')

    // Search for class attribute in a window around the reported line
    // (class might be on the same line or nearby lines)
    const searchStart = Math.max(0, lineNum - 3)
    const searchEnd = Math.min(lines.length - 1, lineNum + 2)
    let foundClass = false

    for (let i = searchStart; i <= searchEnd; i++) {
      const line = lines[i]
      const classMatch = line.match(/class="([^"]*)"/)
      if (classMatch) {
        const existingClasses = classMatch[1].split(/\s+/).filter(Boolean)
        if (!existingClasses.includes(testid)) {
          existingClasses.push(testid)
          lines[i] = line.slice(0, classMatch.index) +
            `class="${existingClasses.join(' ')}"` +
            line.slice(classMatch.index + classMatch[0].length)
          foundClass = true
          modified = true
        }
        break
      }
    }

    if (!foundClass) {
      // No class found nearby - try to add class to the data-testid line itself
      if (lineNum <= lines.length) {
        const line = lines[lineNum - 1]
        const dtMatch = line.match(/data-testid="[^"]*"/)
        if (dtMatch) {
          const insertPos = dtMatch.index + dtMatch[0].length
          lines[lineNum - 1] = line.slice(0, insertPos) + ` class="${testid}"` + line.slice(insertPos)
          modified = true
        }
      }
    }

    if (modified) {
      content = lines.join('\n')
    }
  }

  if (modified) {
    fs.writeFileSync(filePath, content, 'utf-8')
    const relPath = path.relative(frontendDir, filePath)
    console.log(`  Fixed: ${relPath}`)
    totalFixed++
  }
}

// Handle drift fixes
const driftByFile = {}
for (const f of driftFixes) {
  if (!driftByFile[f.file]) driftByFile[f.file] = []
  driftByFile[f.file].push(f)
}

for (const [filePath, fileFixes] of Object.entries(driftByFile)) {
  let content = fs.readFileSync(filePath, 'utf-8')
  let modified = false
  const lines = content.split('\n')

  for (const fix of fileFixes) {
    if (fix.line > lines.length) continue
    const line = lines[fix.line - 1]
    if (!line.includes(`data-testid="${fix.testid}"`)) {
      // Insert data-testid after class attribute
      const classMatch = line.match(/class="[^"]*"/)
      if (classMatch) {
        const insertPos = classMatch.index + classMatch[0].length
        lines[fix.line - 1] = line.slice(0, insertPos) + ` data-testid="${fix.testid}"` + line.slice(insertPos)
        modified = true
      }
    }
  }

  if (modified) {
    content = lines.join('\n')
    fs.writeFileSync(filePath, content, 'utf-8')
    const relPath = path.relative(frontendDir, filePath)
    console.log(`  Fixed drift: ${relPath}`)
    totalFixed++
  }
}

console.log(`\nFixed ${totalFixed} files total.`)
