/**
 * Test script for extracting card price from refund form table
 *
 * Instructions:
 * 1. Navigate to a TCGPlayer order page
 * 2. Click "Partial Refund" on any card to open the refund form
 * 3. Open browser console (F12 → Console tab)
 * 4. Paste this entire script and press Enter
 * 5. The script will show all cards in the table with their prices
 */

(function testPriceExtraction() {
    console.log('='.repeat(80));
    console.log('TCGPlayer Price Extraction Test');
    console.log('='.repeat(80));

    // Find the refund form table
    const table = document.querySelector('form table');

    if (!table) {
        console.error('❌ ERROR: Could not find refund form table');
        console.log('Make sure you:');
        console.log('  1. Are on a TCGPlayer order page');
        console.log('  2. Have clicked "Partial Refund" to open the form');
        return;
    }

    console.log('✓ Found refund form table\n');

    // Check for table header to confirm structure
    const headerRow = table.querySelector('thead tr');
    if (headerRow) {
        const headers = Array.from(headerRow.querySelectorAll('td')).map(td => td.textContent.trim());
        console.log('Table Headers:');
        headers.forEach((header, index) => {
            console.log(`  Column ${index + 1}: "${header}"`);
        });
        console.log('');
    }

    // Find all table rows with card data
    const rows = table.querySelectorAll('tbody tr');

    if (rows.length === 0) {
        console.error('❌ ERROR: No data rows found in table');
        return;
    }

    console.log(`Found ${rows.length} card(s) in table:\n`);

    // Extract data from each row
    rows.forEach((row, index) => {
        console.log(`Card #${index + 1}:`);
        console.log('-'.repeat(60));

        // Column 2: Card Name
        const cardCell = row.querySelector('td:nth-child(2)');
        const cardName = cardCell ? cardCell.textContent.trim() : 'N/A';
        console.log(`  Card Name (col 2): ${cardName}`);

        // Column 5: Cost/Price
        const priceCell = row.querySelector('td:nth-child(5)');
        if (priceCell) {
            const priceText = priceCell.textContent.trim();
            console.log(`  Price Text (col 5): "${priceText}"`);

            // Try to extract price using regex
            const priceMatch = priceText.match(/\$?([0-9]+\.[0-9]{2})/);
            if (priceMatch) {
                const price = parseFloat(priceMatch[1]);
                console.log(`  ✓ Extracted Price: $${price.toFixed(2)}`);
            } else {
                console.log(`  ⚠️  Could not parse price from: "${priceText}"`);
            }
        } else {
            console.log(`  ❌ Price cell (col 5) not found`);
        }

        // Column 9: Quantity input
        const quantityInput = row.querySelector('td:nth-child(9) input');
        if (quantityInput) {
            console.log(`  ✓ Quantity input found (col 9): name="${quantityInput.name}"`);
        } else {
            console.log(`  ⚠️  Quantity input not found (col 9)`);
        }

        console.log('');
    });

    console.log('='.repeat(80));
    console.log('Test Complete!');
    console.log('');
    console.log('Expected results:');
    console.log('  - Should see card name from column 2');
    console.log('  - Should see price text from column 5 (usually like "$1.23")');
    console.log('  - Should see "✓ Extracted Price" with the parsed dollar amount');
    console.log('='.repeat(80));
})();
