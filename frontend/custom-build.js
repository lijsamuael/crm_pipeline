import fs from 'fs-extra';
import path from 'path';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';

// Needed for __dirname in ESM
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const crmAppPath = path.resolve(__dirname, '../../crm/frontend');
const sharedOverridePath = path.resolve(__dirname, '../../crm_override/frontend/src_override');
const overrideSrcPath = path.resolve(__dirname, 'src');
const overrideFilesPath = path.resolve(__dirname, './src_override');

console.log('Starting : Copying original CRM src.');
fs.copySync(path.join(crmAppPath, 'src'), overrideSrcPath);
console.log('Completed : Copying original CRM src.');

console.log('Starting : Applying shared overrides from crm_override.');
fs.copySync(sharedOverridePath, overrideSrcPath);
console.log('Completed : Applying shared overrides from crm_override.');

console.log('Starting : Applying pipeline-specific overrides.');
fs.copySync(overrideFilesPath, overrideSrcPath);
console.log('Completed : Applying pipeline-specific overrides.');

execSync('yarn install', { stdio: 'inherit' });

