#!/usr/bin/env node
/**
 * SOP to PDF Generator
 * HelixNet Standard Operating Procedure - Professional PDF Output
 *
 * Usage:
 *   node sop-to-pdf.js input.html output.pdf "Document Title" "SOP-001"
 *
 * Features:
 *   - Header on every page: Document title + HelixNet branding
 *   - Footer on every page: Page X of Y + Revision + Confidential
 *   - Proper page breaks (no mid-sentence cuts)
 *   - Professional A4 output
 */

const path = require('path');
const fs = require('fs');

// Resolve puppeteer from helixnet root
const helixnetRoot = path.resolve(__dirname, '..');
const puppeteer = require(path.join(helixnetRoot, 'node_modules', 'puppeteer'));

async function generatePDF(inputHtml, outputPdf, docTitle, docId) {
    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();

    // Read HTML file
    const htmlPath = path.resolve(inputHtml);
    const htmlContent = fs.readFileSync(htmlPath, 'utf8');

    // Load the HTML
    await page.setContent(htmlContent, {
        waitUntil: 'networkidle0'
    });

    // Generate PDF with headers and footers
    await page.pdf({
        path: outputPdf,
        format: 'A4',
        margin: {
            top: '25mm',
            bottom: '25mm',
            left: '15mm',
            right: '15mm'
        },
        displayHeaderFooter: true,
        headerTemplate: `
            <div style="width: 100%; font-size: 9px; font-family: Arial, sans-serif; padding: 0 15mm; display: flex; justify-content: space-between; color: #666;">
                <div style="font-weight: bold; color: #C0392B;">HelixNet</div>
                <div>${docTitle || 'Standard Operating Procedure'}</div>
                <div style="font-weight: bold; color: #2C3E50;">${docId || 'SOP'}</div>
            </div>
        `,
        footerTemplate: `
            <div style="width: 100%; font-size: 8px; font-family: Arial, sans-serif; padding: 0 15mm; display: flex; justify-content: space-between; color: #666; border-top: 1px solid #ddd; padding-top: 5px;">
                <div>Confidential - Internal Use Only</div>
                <div>Page <span class="pageNumber"></span> of <span class="totalPages"></span></div>
                <div>Rev 1.0 | January 2026</div>
            </div>
        `,
        printBackground: true
    });

    await browser.close();

    console.log(`✓ Generated: ${outputPdf}`);
    console.log(`  Title: ${docTitle}`);
    console.log(`  ID: ${docId}`);
}

// CLI
const args = process.argv.slice(2);

if (args.length < 2) {
    console.log(`
HelixNet SOP to PDF Generator

Usage:
  node sop-to-pdf.js <input.html> <output.pdf> [title] [doc-id]

Examples:
  node sop-to-pdf.js SOP-001.html SOP-001.pdf "Postcard Print Workflow" "SOP-001"
  node sop-to-pdf.js index.html output.pdf

Features:
  - Header on every page (HelixNet + Title + Doc ID)
  - Footer on every page (Page X of Y + Rev + Confidential)
  - A4 format with proper margins
  - Professional print quality
`);
    process.exit(1);
}

const [inputHtml, outputPdf, docTitle, docId] = args;

generatePDF(inputHtml, outputPdf, docTitle || 'Standard Operating Procedure', docId || 'SOP')
    .catch(err => {
        console.error('Error:', err.message);
        process.exit(1);
    });
