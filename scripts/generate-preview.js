#!/usr/bin/env node
/**
 * ISOTTO Sport - Preview Image Generator
 * Generates personalization preview PNGs using Puppeteer.
 *
 * Usage:
 *   node scripts/generate-preview.js --data '{"product_name":"ROLY Bahrain","color":"white","size":"L","name_text":"ROSSI","number_text":"10","text_color":"navy","font_name":"Impact","placement":"back"}' --output /tmp/preview.png
 *
 * Or via stdin JSON:
 *   echo '{"product_name":"ROLY Bahrain",...}' | node scripts/generate-preview.js --output /tmp/preview.png
 *
 * "20 players, 20 names, 20 numbers. Perfect every time."
 */
const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

// Color name -> hex mapping
const COLOR_MAP = {
    white: '#FFFFFF', black: '#1a1a1a', navy: '#001f3f', red: '#e74c3c',
    grey: '#7f8c8d', royal_blue: '#2980b9', dark_green: '#27ae60',
    yellow: '#f1c40f', orange: '#e67e22', burgundy: '#8e2252',
};

const TEXT_COLOR_MAP = {
    white: '#FFFFFF', black: '#1a1a1a', navy: '#001f3f', red: '#e74c3c',
    gold: '#D4AF37', silver: '#C0C0C0', grey: '#7f8c8d',
};

function generateHTML(data) {
    const bgColor = COLOR_MAP[data.color] || '#FFFFFF';
    const textColor = TEXT_COLOR_MAP[data.text_color] || '#001f3f';
    const fontName = data.font_name || 'Impact';
    const placement = data.placement || 'back';
    const isLight = ['white', '#FFFFFF', '#fff'].includes(bgColor) ||
                    ['yellow', '#f1c40f', '#F1C40F'].includes(bgColor);
    const outlineColor = isLight ? '#e0e0e0' : 'transparent';

    // Garment shape SVG
    const garmentSVG = `
        <svg viewBox="0 0 300 380" xmlns="http://www.w3.org/2000/svg" style="width:300px;height:380px;">
            <!-- Garment body -->
            <path d="M75,0 L60,40 L20,30 L0,80 L40,95 L40,380 L260,380 L260,95 L300,80 L280,30 L240,40 L225,0 Z"
                  fill="${bgColor}" stroke="${outlineColor}" stroke-width="2"/>
            <!-- Collar -->
            <path d="M75,0 Q105,35 150,40 Q195,35 225,0"
                  fill="none" stroke="${isLight ? '#ccc' : 'rgba(255,255,255,0.2)'}" stroke-width="2"/>
        </svg>
    `;

    // Text positioning based on placement
    let textTop, label;
    switch (placement) {
        case 'front':
            textTop = '120px';
            label = 'FRONT';
            break;
        case 'left_sleeve':
            textTop = '85px';
            label = 'L.SLEEVE';
            break;
        case 'right_sleeve':
            textTop = '85px';
            label = 'R.SLEEVE';
            break;
        case 'back':
        default:
            textTop = '120px';
            label = 'BACK';
            break;
    }

    return `<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Impact&display=swap');
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
        width: 400px; height: 500px;
        background: #f3f4f6;
        font-family: 'Inter', Arial, sans-serif;
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 10px;
    }
    .garment-container {
        position: relative;
        width: 300px;
        height: 380px;
    }
    .personalization {
        position: absolute;
        left: 50%;
        transform: translateX(-50%);
        text-align: center;
        top: ${textTop};
    }
    .player-name {
        font-family: '${fontName}', Impact, sans-serif;
        font-size: 28px;
        color: ${textColor};
        letter-spacing: 3px;
        text-transform: uppercase;
    }
    .player-number {
        font-family: '${fontName}', Impact, sans-serif;
        font-size: 72px;
        color: ${textColor};
        line-height: 1;
        margin-top: 4px;
    }
    .custom-text {
        font-family: '${fontName}', Impact, sans-serif;
        font-size: 16px;
        color: ${textColor};
        margin-top: 6px;
    }
    .info-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 300px;
        margin-top: 8px;
        padding: 6px 12px;
        background: white;
        border-radius: 6px;
        font-size: 11px;
        color: #6b7280;
        border: 1px solid #e5e7eb;
    }
    .info-bar .product { font-weight: 600; color: #374151; }
    .info-bar .size-badge {
        background: #2563eb;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 12px;
    }
    .placement-label {
        position: absolute;
        top: 6px;
        right: 6px;
        background: rgba(0,0,0,0.5);
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 1px;
    }
</style>
</head>
<body>
    <div class="garment-container">
        ${garmentSVG}
        <div class="placement-label">${label}</div>
        <div class="personalization">
            ${data.name_text ? `<div class="player-name">${escapeHtml(data.name_text)}</div>` : ''}
            ${data.number_text ? `<div class="player-number">${escapeHtml(data.number_text)}</div>` : ''}
            ${data.custom_text ? `<div class="custom-text">${escapeHtml(data.custom_text)}</div>` : ''}
        </div>
    </div>
    <div class="info-bar">
        <span class="product">${escapeHtml(data.product_name || 'Custom Item')}</span>
        <span>${escapeHtml(data.color || '')}</span>
        <span class="size-badge">${escapeHtml(data.size || '-')}</span>
    </div>
</body></html>`;
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

async function main() {
    const args = process.argv.slice(2);
    let dataStr = '';
    let outputPath = '/tmp/isotto-preview.png';

    // Parse args
    for (let i = 0; i < args.length; i++) {
        if (args[i] === '--data' && args[i + 1]) {
            dataStr = args[++i];
        } else if (args[i] === '--output' && args[i + 1]) {
            outputPath = args[++i];
        }
    }

    // Read from stdin if no --data
    if (!dataStr) {
        dataStr = fs.readFileSync(0, 'utf8').trim();
    }

    if (!dataStr) {
        console.error('Usage: node generate-preview.js --data \'{"product_name":"..."}\'  --output path.png');
        process.exit(1);
    }

    const data = JSON.parse(dataStr);
    const html = generateHTML(data);

    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 400, height: 500 });
    await page.setContent(html, { waitUntil: 'networkidle0' });
    await page.screenshot({
        path: outputPath,
        type: 'png',
        clip: { x: 0, y: 0, width: 400, height: 500 },
    });

    await browser.close();

    console.log(JSON.stringify({ status: 'ok', output: outputPath }));
}

main().catch(err => {
    console.error(JSON.stringify({ status: 'error', message: err.message }));
    process.exit(1);
});
