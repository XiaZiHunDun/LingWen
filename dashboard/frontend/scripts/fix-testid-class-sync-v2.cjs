// scripts/fix-testid-class-sync-v2.cjs
// More robust version: fixes all "class must contain X" warnings by adding
// the testid token to the existing class attribute on the same element.

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

// Collect "class must contain" warnings
const fixes = [] // {file, testid, line}
const driftFixes = [] // {file, classToken, line}

eslintData.forEach(file => {
  file.messages.forEach(m => {
    if (m.ruleId !== 'custom/testid-class-sync') return
    if (m.message.includes('class 必须包含')) {
      const match = m.message.match(/class 必须包含 "([^"]+)"/)
      if (match) fixes.push({ file: file.filePath, testid: match[1], line: m.line })
    } else if (m.message.includes('必加 data-testid')) {
      const match = m.message.match(/class="([^"]+)" 必加 data-testid="([^"]+)"/)
      if (match) driftFixes.push({ file: file.filePath, classToken: match[1], testid: match[2], line: m.line })
    }
  })
})

console.log(`Found ${fixes} class-must-contain fixes and ${driftFixes} drift fixes`)

// Group fixes by file
const byFile = {}
for (const f of fixes) {
  if (!byFile[f.file]) byFile[f.file] = []
  byFile[f.file].push(f)
}

let totalFixed = 0

for (const [filePath, fileFixes] of Object.entries(byFile)) {
  let content = fs.readFileSync(filePath, 'utf-8')
  let modified = false

  // Process fixes from bottom to top to preserve line numbers
  fileFixes.sort((a, b) => b.line - a.line)

  for (const fix of fileFixes) {
    const testid = fix.testid
    const lineNum = fix.line
    const lines = content.split('\n')
    if (lineNum > lines.length) continue
    let targetLine = lines[lineNum - 1]

    // Check if class attribute exists on this line
    const classRegex = /class="([^"]*)"/g
    let classMatch
    let found = false
    
    while ((classMatch = classRegex.exec(targetLine)) !== null) {
      const existingClasses = classMatch[1].split(/\s+/).filter(Boolean)
      if (!existingClasses.includes(testid)) {
        existingClasses.push(testid)
        targetLine = targetLine.slice(0, classMatch.index) + 
          `class="${existingClasses.join(' ')}"` + 
          targetLine.slice(classMatch.index + classMatch[0].length)
        lines[lineNum - 1] = targetLine
        content = lines.join('\n')
        modified = true
        found = true
        break
      } else {
        // Move past this match
        classRegex.lastIndex = classMatch.index + classMatch[0].length
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

// Handle drift fixes (add data-testid to interactive element with matching class)
for (const fix of driftFixes) {
  const filePath = fix.file
  let content = fs.readFileSync(filePath, 'utf-8')
  const lines = content.split('\n')
  if (fix.line > lines.length) continue
  let targetLine = lines[fix.line - 1]

  // Add data-testid="x" after the class attribute
  const classRegex = /class="[^"]*"/
  const classMatch = targetLine.match(classRegex)
  if (classMatch && !targetLine.includes(`data-testid="${fix.testid}"`)) {
    const insertPos = classMatch.index + classMatch[0].length
    targetLine = targetLine.slice(0, insertPos) + ` data-testid="${fix.testid}"` + targetLine.slice(insertPos)
    lines[fix.line - 1] = targetLine
    content = lines.join('\n')
    fs.writeFileSync(filePath, content, 'utf-8')
    const relPath = path.relative(frontendDir, filePath)
    console.log(`  Fixed drift: ${relPath}`)
    totalFixed++
  }
}

console.log(`\nFixed ${totalFixed} files total.`)
