#!/usr/bin/env python3
"""
Emergency Classification API Client Test
"""
import requests
import json
import time

# API endpoint
BASE_URL = "https://l63p034w6181jc-8501.proxy.runpod.net"

def test_health():
    """Test if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Server is healthy!")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server unreachable: {e}")
        return False

def classify_text(text):
    """Classify emergency text"""
    try:
        payload = {"text": text}
        response = requests.post(
            f"{BASE_URL}/ask_class",
            json=payload,
            timeout=90,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("category", "unknown")
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return "error"
            
    except Exception as e:
        print(f"❌ Classification failed: {e}")
        return "error"

def run_tests():
    """Run comprehensive tests"""
    print("🧪 Emergency Classification API Test")
    print("=" * 50)
    
    # Health check
    if not test_health():
        print("Server not available. Exiting...")
        return
    
    # Test cases covering all categories
    test_cases = [
        # Child lost
        ("Bacha kho gaya hai", "child_lost"),
        ("Small child is missing", "child_lost"),
        
        # Medical help
        ("Mujhe doctor chahiye", "medical_help"),
        ("Someone needs medical attention", "medical_help"),
        
        # Crowd panic
        ("Log bhag rahe hain", "crowd_panic"),
        ("People are running and shouting", "crowd_panic"),
        
        # Small fire
        ("Yahan aag lagi hai", "small_fire"),
        ("There is smoke in the kitchen", "small_fire"),
        
        # Need interpreter
        ("I need interpreter", "need_interpreter"),
        ("Tourist ko interpreter chahiye", "need_interpreter"),
        
        # Lost item
        ("Mera bag kho gaya", "lost_item"),
        ("My wallet is missing", "lost_item"),
    ]
    
    print(f"\n🚀 Testing {len(test_cases)} emergency scenarios...")
    print(f"{'Emergency Text':<40} | {'Expected':<15} | {'Predicted':<15} | {'Status'}")
    print("-" * 85)
    
    correct = 0
    total = len(test_cases)
    
    for text, expected in test_cases:
        predicted = classify_text(text)
        status = "✅ PASS" if predicted == expected else "❌ FAIL"
        
        if predicted == expected:
            correct += 1
            
        print(f"{text:<40} | {expected:<15} | {predicted:<15} | {status}")
        time.sleep(0.5)  # Small delay between requests
    
    # Results
    accuracy = (correct / total) * 100
    print("-" * 85)
    print(f"📊 RESULTS: {correct}/{total} correct ({accuracy:.1f}% accuracy)")
    
    if accuracy >= 90:
        print("🎉 EXCELLENT! Model is working perfectly!")
    elif accuracy >= 70:
        print("👍 GOOD! Model is working well!")
    else:
        print("⚠️ Model needs improvement")

def interactive_test():
    """Interactive testing mode"""
    print("\n🎯 Interactive Testing Mode")
    print("Enter emergency situations to classify (type 'quit' to exit)")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\nEmergency: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
                
            if not user_input:
                print("Please enter some text")
                continue
                
            print("🔄 Classifying...")
            start_time = time.time()
            
            result = classify_text(user_input)
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            print(f"📋 Category: {result}")
            print(f"⏱️ Response time: {response_time:.0f}ms")
            
        except KeyboardInterrupt:
            break
    
    print("\n👋 Goodbye!")

def quick_test():
    """Quick single test"""
    print("🔥 Quick Test")
    test_text = "Bacha kho gaya hai"
    print(f"Testing: '{test_text}'")
    
    result = classify_text(test_text)
    print(f"Result: {result}")
    
    return result == "child_lost"

if __name__ == "__main__":
    print("Emergency Classification API Client")
    print("=" * 40)
    
    # Choose test mode
    print("\nSelect test mode:")
    print("1. Quick test")
    print("2. Full test suite")
    print("3. Interactive mode")
    
    try:
        choice = input("\nEnter choice (1/2/3): ").strip()
        
        if choice == "1":
            success = quick_test()
            print("✅ Success!" if success else "❌ Failed!")
            
        elif choice == "2":
            run_tests()
            
        elif choice == "3":
            if test_health():
                interactive_test()
            else:
                print("Server not available for interactive mode")
                
        else:
            print("Invalid choice, running quick test...")
            quick_test()
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")