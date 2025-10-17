#!/bin/bash
# Production test runner for newsletter extraction pipeline

echo "================================================================================"
echo "                   NEWSLETTER PIPELINE TEST SUITE"
echo "================================================================================"
echo ""

# Run tests with coverage
python3.11 -m pytest tests/ -v --tb=short --color=yes

# Store exit code
EXIT_CODE=$?

echo ""
echo "================================================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ ALL TESTS PASSED - Pipeline is production ready!"
else
    echo "❌ TESTS FAILED - Fix issues before deploying to production"
fi
echo "================================================================================"

exit $EXIT_CODE
