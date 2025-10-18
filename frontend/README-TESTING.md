# Testing Guide

This project includes comprehensive End-to-End (E2E) tests using Playwright to validate the newsletter extraction workflow.

## Prerequisites

1. **Backend must be running** on `http://localhost:9765`
2. **Frontend must be running** on `http://localhost:3456`
3. **Gmail authentication** must be set up (token.json exists)

## Installing Playwright Browsers

First time only, install Playwright browsers:

```bash
npx playwright install
```

This downloads Chromium, Firefox, and WebKit browsers for testing.

## Running Tests

### Run all tests (headless mode)
```bash
npm run test:e2e
```

### Run tests with UI (recommended for debugging)
```bash
npm run test:e2e:ui
```

### Run tests with browser visible
```bash
npm run test:e2e:headed
```

### View test report
```bash
npm run test:report
```

## Test Coverage

The E2E test suite (`e2e/newsletter-extraction.spec.ts`) validates:

### ✅ **Page Structure**
- Header and description are visible
- Extract form is present with timeframe selector
- Extract button is enabled
- Past Extractions section exists

### ✅ **Timeframe Selection**
- All timeframe options (1, 7, 14, 30, 90 days) are available
- Default is 7 days
- Can select different timeframes

### ✅ **Navigation**
- Config button navigates to `/newsletters/config`
- Home button navigates to `/`
- Links work correctly

### ✅ **Extraction Workflow**
1. Click "Extract" button
2. Shows "Extracting..." loading state
3. Shows pipeline progress message
4. Button is disabled during extraction
5. New extraction appears in list after completion
6. Extraction auto-expands to show results

### ✅ **Extraction List**
- Shows all past extractions
- Displays newsletter count and link count
- Can expand extraction to see newsletters
- Can expand newsletter to see article links
- Copy button appears on hover for article URLs
- Refresh button reloads extractions

### ✅ **Error Handling**
- Shows error message if extraction fails
- "Try Again" button appears on error
- Gracefully handles API failures

### ✅ **Persistence**
- Extractions persist across page reloads
- Data is loaded from backend on page load

## Test Architecture

### What We Test

**Frontend:**
- User interface rendering
- Button interactions
- Form submissions
- Loading states
- Error states
- Navigation
- Expandable accordions
- Copy to clipboard functionality

**Integration:**
- Frontend → Backend API communication
- Pipeline execution (Steps 1-4)
- Data persistence
- Real Gmail extraction (if token.json exists)

### What We Don't Test (covered by Python tests)

- URL filtering logic (`tests/test_content_filtering.py`)
- Config management (`tests/test_api.py`)
- Redirect resolution
- Link parsing

## Debugging Tests

### Interactive Mode (Recommended)
```bash
npm run test:e2e:ui
```

This opens Playwright's interactive UI where you can:
- See each test step
- Pause/resume execution
- Inspect elements
- View screenshots
- Debug failures

### Headed Mode (See Browser)
```bash
npm run test:e2e:headed
```

Runs tests with the browser visible so you can watch what's happening.

### Debugging Specific Tests
```bash
npx playwright test --grep "should create extraction"
```

Runs only tests matching the pattern.

## CI/CD Integration

The tests are configured to:
- Run in headless mode on CI
- Take screenshots on failure
- Generate HTML reports
- Retry failed tests 2 times

## Common Issues

### ❌ "Connection refused" errors
**Solution:** Make sure both frontend and backend are running:
```bash
# Terminal 1 - Backend
cd backend
python3.11 -m uvicorn app.main:app --reload --port 9765

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### ❌ "No extractions found" warnings
**Solution:** Run a manual extraction first:
```bash
cd backend/extractors/email
python3.11 pipeline.py --days 1 --max 1
```

### ❌ Timeout errors during extraction
**Solution:** Tests have 2-minute timeout for extraction. If your Gmail has many newsletters, the backend may take longer. You can:
1. Use `--days 1` for faster tests
2. Increase timeout in test config
3. Mock the API for faster test execution

## Writing New Tests

Add new test cases to `e2e/newsletter-extraction.spec.ts`:

```typescript
test('should do something', async ({ page }) => {
  await page.goto('/newsletters');
  // Your test logic here
  await expect(page.locator('...')).toBeVisible();
});
```

## Best Practices

1. **Use data-testid for stable selectors:**
   ```typescript
   // Instead of: page.locator('button:has-text("Extract")')
   // Better: page.locator('[data-testid="extract-button"]')
   ```

2. **Wait for network idle before assertions:**
   ```typescript
   await page.waitForLoadState('networkidle');
   ```

3. **Use timeouts for async operations:**
   ```typescript
   await expect(element).toBeVisible({ timeout: 10000 });
   ```

4. **Clean up test data after tests:**
   ```typescript
   test.afterEach(async () => {
     // Clean up extractions if needed
   });
   ```

## Performance

- Tests run in parallel by default
- Each test is isolated (fresh page context)
- Frontend dev server is reused between tests
- Average test suite runtime: ~2-3 minutes

## Resources

- [Playwright Documentation](https://playwright.dev)
- [Test Best Practices](https://playwright.dev/docs/best-practices)
- [Debugging Guide](https://playwright.dev/docs/debug)
