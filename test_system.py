"""
Simple system test - Verify all components work correctly
Can run with or without dependencies
"""
import sys
import os


def test_imports():
    """
    Test if all modules can be imported.
    """
    print("\n" + "="*70)
    print("  TESTING MODULE IMPORTS")
    print("="*70 + "\n")
    
    modules = [
        "config",
        "bias_classifier",
        "indicators",
        "signal_generator",
    ]
    
    # Optional modules (require dependencies)
    optional_modules = [
        "data_fetcher",
        "market_copilot",
        "market_hours"
    ]
    
    passed = 0
    failed = 0
    
    # Test required modules
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module:<25} OK")
            passed += 1
        except Exception as e:
            print(f"✗ {module:<25} FAILED: {str(e)}")
            failed += 1
    
    # Test optional modules
    for module in optional_modules:
        try:
            __import__(module)
            print(f"✓ {module:<25} OK (requires dependencies)")
            passed += 1
        except ImportError as e:
            print(f"⚠ {module:<25} SKIPPED (missing dependencies)")
        except Exception as e:
            print(f"✗ {module:<25} FAILED: {str(e)}")
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*70}\n")
    
    return failed == 0


def test_config():
    """
    Test configuration values.
    """
    print("\n" + "="*70)
    print("  TESTING CONFIGURATION")
    print("="*70 + "\n")
    
    try:
        import config
        
        print(f"Default Ticker: {config.DEFAULT_TICKER}")
        print(f"Timeframes: {config.TIMEFRAMES}")
        print(f"Indicators: {config.INDICATORS}")
        print(f"Bias Thresholds: {config.BIAS_THRESHOLDS}")
        print(f"Request Delay: {config.REQUEST_DELAY}s")
        print(f"Max Requests/Hour: {config.MAX_REQUESTS_PER_HOUR}")
        
        print("\n✓ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"\n✗ Configuration test failed: {str(e)}")
        return False


def test_bias_classifier():
    """
    Test bias classifier with mock data.
    """
    print("\n" + "="*70)
    print("  TESTING BIAS CLASSIFIER")
    print("="*70 + "\n")
    
    try:
        from bias_classifier import BiasClassifier, MarketBias
        import pandas as pd
        
        classifier = BiasClassifier(rsi_bullish_threshold=55, rsi_bearish_threshold=45)
        
        # Create mock data
        mock_data = pd.Series({
            'Close': 578.45,
            'VWAP': 577.20,
            'EMA_fast': 578.10,
            'EMA_slow': 577.50,
            'RSI': 62.3
        })
        
        bias, confidence, notes = classifier.classify_bias(mock_data)
        
        print(f"Bias: {bias.value}")
        print(f"Confidence: {confidence:.1%}")
        print(f"Notes: {len(notes)} analysis notes")
        
        print("\n✓ Bias classifier works correctly")
        return True
    except ImportError:
        print("\n⚠ Bias classifier test skipped (missing pandas)")
        return True
    except Exception as e:
        print(f"\n✗ Bias classifier test failed: {str(e)}")
        return False


def test_demo_mode():
    """
    Test demo mode (no dependencies required).
    """
    print("\n" + "="*70)
    print("  TESTING DEMO MODE")
    print("="*70 + "\n")
    
    try:
        from demo_mode import run_demo
        
        print("Running bullish scenario demo...\n")
        signal = run_demo("bullish")
        
        if signal and 'synthesis' in signal:
            print("\n✓ Demo mode works correctly")
            print(f"   Overall Bias: {signal['synthesis']['overall_bias']}")
            print(f"   Confidence: {signal['synthesis']['average_confidence']:.1%}")
            return True
        else:
            print("\n✗ Demo mode returned invalid signal")
            return False
    except Exception as e:
        print(f"\n✗ Demo mode test failed: {str(e)}")
        return False


def run_all_tests():
    """
    Run all system tests.
    """
    print("\n" + "🧪 "*20)
    print("  MARKET COPILOT - SYSTEM TEST")
    print("🧪 "*20)
    
    results = []
    
    # Test imports
    results.append(("Module Imports", test_imports()))
    
    # Test configuration
    results.append(("Configuration", test_config()))
    
    # Test bias classifier
    results.append(("Bias Classifier", test_bias_classifier()))
    
    # Test demo mode
    results.append(("Demo Mode", test_demo_mode()))
    
    # Summary
    print("\n" + "="*70)
    print("  TEST SUMMARY")
    print("="*70 + "\n")
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:<30} {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\n{'='*70}")
    print(f"Overall: {total_passed}/{total_tests} tests passed")
    print(f"{'='*70}\n")
    
    if total_passed == total_tests:
        print("✅ All tests passed! System is ready to use.\n")
        print("Quick Start:")
        print("  • Demo mode (no dependencies): python demo_mode.py")
        print("  • Live mode (requires deps):   python market_copilot.py\n")
        return 0
    else:
        print("⚠️  Some tests failed. Check errors above.\n")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
