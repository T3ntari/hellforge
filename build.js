import peggy from 'peggy';
import { readFileSync, writeFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

const grammarPath = resolve(__dirname, 'src/grammar.peggy');
const outputPath = resolve(__dirname, 'src/parser.js');

const grammar = readFileSync(grammarPath, 'utf8');

const parserSource = peggy.generate(grammar, {
  output: 'source',
  format: 'es',
  allowedStartRules: ['HumanStart', 'MachineStart'],
});

writeFileSync(outputPath, parserSource, 'utf8');
console.log('Parser generated successfully at src/parser.js');
