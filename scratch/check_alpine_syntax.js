const fs = require('fs');
const html = fs.readFileSync('scratch/index.html', 'utf8');

const expressions = [];
const attrRegex = /(?:\s|^)(x-[a-z0-9:-]+|@[a-z0-9.-]+|:[a-z0-9.-]+)="([^"]*)"/gi;
let match;
while ((match = attrRegex.exec(html)) !== null) {
    const attrName = match[1];
    const attrVal = match[2];
    expressions.push({ name: attrName, val: attrVal });
}

for (const expr of expressions) {
    const code = expr.val.trim();
    if (!code) continue;

    let errStatement = null;
    let errExpression = null;

    try {
        new Function(code);
    } catch (e) {
        errStatement = e;
    }

    try {
        new Function('return (' + code + ')');
    } catch (e) {
        errExpression = e;
    }

    if (errStatement && errExpression && errStatement instanceof SyntaxError && errExpression instanceof SyntaxError) {
        // Skip x-transition classes because they are just strings of class names and not javascript,
        // which is expected by Alpine.js for x-transition.enter etc.
        if (expr.name.startsWith('x-transition:')) continue;

        console.log(`\n--- SYNTAX ERROR DETECTED ---`);
        console.log(`Attribute: ${expr.name}`);
        const len = code.length;
        const preview = len > 200 
            ? code.substring(0, 100) + ' ... [TRUNCATED] ... ' + code.substring(len - 100)
            : code;
        console.log(`Value Preview: ${preview}`);
        console.log(`Statement error:  ${errStatement.message}`);
        console.log(`Expression error: ${errExpression.message}`);
    }
}
