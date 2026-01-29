#!/usr/bin/env node
/**
 * Postcard to PDF Generator
 * Clean output - NO headers, NO footers, NO margins
 * What you see in the HTML is what you get in the PDF.
 *
 * Usage:
 *   node postcard-to-pdf.js input.html output.pdf
 */

const path = require('path');
const fs = require('fs');

const helixnetRoot = path.resolve(__dirname, '..');
const puppeteer = require(path.join(helixnetRoot, 'node_modules', 'puppeteer'));

async function generatePDF(inputHtml, outputPdf) {
    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();

    const htmlPath = path.resolve(inputHtml);
    const fileUrl = 'file://' + htmlPath;

    await page.goto(fileUrl, {
        waitUntil: 'networkidle0'
    });

    await page.pdf({
        path: outputPdf,
        format: 'A4',
        margin: { top: '0', bottom: '0', left: '0', right: '0' },
        displayHeaderFooter: false,
        printBackground: true
    });

    await browser.close();

    console.log(`✓ Generated: ${outputPdf}`);
}

const args = process.argv.slice(2);

if (args.length < 2) {
    console.log(`
UFA Postcard to PDF Generator

Usage:
  node postcard-to-pdf.js <input.html> <output.pdf>

Output: Clean A4, zero margins, no headers/footers.
`);
    process.exit(1);
}

const [inputHtml, outputPdf] = args;

generatePDF(inputHtml, outputPdf)
    .catch(err => {
        console.error('Error:', err.message);
        process.exit(1);
    });
