// Test script to detect country from TCGPlayer order page
// Run this in browser console on an order page

(function() {
    console.log('=== Country Detection Test ===\n');

    // Test the UPDATED XPath from the script (td[2] contains country code)
    const country_xpath = '/html/body/div[4]/div/div[6]/div[1]/div[1]/table/tbody/tr[8]/td[2]';

    // Convert XPath to element
    const countryElement = document.evaluate(
        country_xpath,
        document,
        null,
        XPathResult.FIRST_ORDERED_NODE_TYPE,
        null
    ).singleNodeValue;

    if (countryElement) {
        const countryCode = countryElement.textContent.trim();
        console.log('✓ Country code found via XPath:');
        console.log(`  Country Code: "${countryCode}"`);
        console.log(`  Is International: ${countryCode.toUpperCase() !== 'US'}`);
    } else {
        console.log('✗ Country element not found via XPath\n');

        // Try to find it manually
        console.log('Searching for shipping address table...\n');

        // Look for all tables
        const tables = document.querySelectorAll('table');
        console.log(`Found ${tables.length} tables on page`);

        // Look for shipping-related content
        tables.forEach((table, idx) => {
            const text = table.textContent.toLowerCase();
            if (text.includes('ship') || text.includes('address') || text.includes('country')) {
                console.log(`\nTable ${idx} might be shipping info:`);
                console.log(table.textContent.substring(0, 200));
            }
        });
    }

    console.log('\n=== End Test ===');
})();
