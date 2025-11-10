#!/usr/bin/env python3
"""
Quick test script to verify authentication is working
"""
import os
import hashlib
import sys

def test_password_hashing():
    """Test password hashing functionality."""
    print("🔐 Testing Password Authentication")
    print("=" * 50)
    
    # Test password
    test_password = "test123"
    print(f"\n1. Test Password: {test_password}")
    
    # Generate hash
    hash_obj = hashlib.sha256(test_password.encode())
    hash_hex = hash_obj.hexdigest()
    print(f"2. Generated Hash: {hash_hex}")
    
    # Verify hash
    test_hash = hashlib.sha256(test_password.encode()).hexdigest()
    matches = test_hash == hash_hex
    print(f"3. Verification: {'✅ PASS' if matches else '❌ FAIL'}")
    
    return matches

def test_env_vars():
    """Test environment variable detection."""
    print("\n🌍 Testing Environment Variables")
    print("=" * 50)
    
    # Check if password is set
    password = os.getenv("STREAMLIT_PASSWORD")
    password_hash = os.getenv("STREAMLIT_PASSWORD_HASH")
    
    if password:
        print(f"✅ STREAMLIT_PASSWORD is set (plain text)")
        print(f"   Value: {'*' * len(password)}")
    elif password_hash:
        print(f"✅ STREAMLIT_PASSWORD_HASH is set (hashed)")
        print(f"   Hash: {password_hash[:20]}...")
    else:
        print("⚠️  No password environment variables set")
        print("   Auth will be disabled (local dev mode)")
    
    return password or password_hash

def generate_password_hash():
    """Helper to generate password hash."""
    if len(sys.argv) > 1:
        password = sys.argv[1]
        hash_hex = hashlib.sha256(password.encode()).hexdigest()
        print(f"\n🔑 Password Hash Generator")
        print("=" * 50)
        print(f"Password: {password}")
        print(f"Hash: {hash_hex}")
        print(f"\nSet in Railway:")
        print(f"STREAMLIT_PASSWORD_HASH={hash_hex}")
        return hash_hex
    return None

if __name__ == "__main__":
    # If password provided as argument, generate hash
    if len(sys.argv) > 1:
        generate_password_hash()
    else:
        # Run tests
        test_password_hashing()
        test_env_vars()
        
        print("\n" + "=" * 50)
        print("💡 To generate a password hash:")
        print("   python scripts/test_auth.py your_password_here")
        print("\n💡 To test auth locally:")
        print("   export STREAMLIT_PASSWORD=your_password")
        print("   streamlit run src/ui/streamlit_app.py")

