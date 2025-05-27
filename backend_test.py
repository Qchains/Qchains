import requests
import sys
import json
import time
import uuid
from datetime import datetime

class FloJsonCollectorTester:
    def __init__(self, base_url="https://778e35d5-2716-4eda-bca9-55b7b35e9e0b.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = f"test-session-{uuid.uuid4()}"
        self.strict_mode = False

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error: {error_data}")
                    return False, error_data
                except:
                    return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        return success

    def test_create_collector(self, session_id=None, strict_mode=None):
        """Test creating a collector"""
        if session_id:
            self.session_id = session_id
        if strict_mode is not None:
            self.strict_mode = strict_mode
            
        success, response = self.run_test(
            "Create Collector",
            "POST",
            "collector/create",
            200,
            data={
                "session_id": self.session_id,
                "strict_mode": self.strict_mode
            }
        )
        return success

    def test_process_llm_response(self, content, strict_mode=None, session_id=None):
        """Test processing an LLM response"""
        test_session = session_id or self.session_id
        test_strict = strict_mode if strict_mode is not None else self.strict_mode
        
        success, response = self.run_test(
            "Process LLM Response",
            "POST",
            "collector/process",
            200,
            data={
                "content": content,
                "session_id": test_session,
                "strict_mode": test_strict
            }
        )
        return success, response

    def test_get_collector_status(self):
        """Test getting collector status"""
        success, response = self.run_test(
            "Get Collector Status",
            "GET",
            f"collector/status/{self.session_id}",
            200
        )
        return success, response

    def test_get_memory_trail(self):
        """Test getting memory trail"""
        success, response = self.run_test(
            "Get Memory Trail",
            "GET",
            f"collector/memory/{self.session_id}",
            200
        )
        return success, response

    def test_peek_latest(self):
        """Test peeking at the latest entry"""
        success, response = self.run_test(
            "Peek Latest Entry",
            "GET",
            f"collector/peek/{self.session_id}",
            200
        )
        return success, response

    def test_pop_latest(self):
        """Test popping the latest entry"""
        success, response = self.run_test(
            "Pop Latest Entry",
            "POST",
            f"collector/pop/{self.session_id}",
            200
        )
        return success, response

    def test_fetch_merged(self):
        """Test fetching merged data"""
        success, response = self.run_test(
            "Fetch Merged Data",
            "GET",
            f"collector/fetch/{self.session_id}",
            200
        )
        return success, response

    def test_create_iterator(self, depth=None):
        """Test creating an iterator"""
        success, response = self.run_test(
            "Create Iterator",
            "POST",
            "collector/iterator/create",
            200,
            data={
                "session_id": self.session_id,
                "depth": depth
            }
        )
        return success, response

    def test_iterator_next(self, depth=None):
        """Test getting next batch from iterator"""
        success, response = self.run_test(
            "Iterator Next",
            "POST",
            "collector/iterator/next",
            200,
            data={
                "session_id": self.session_id,
                "depth": depth
            }
        )
        return success, response

    def test_rewind_memory(self, depth=None):
        """Test rewinding memory"""
        success, response = self.run_test(
            "Rewind Memory",
            "POST",
            "collector/rewind",
            200,
            data={
                "session_id": self.session_id,
                "depth": depth
            }
        )
        return success, response

    def test_clear_collector(self):
        """Test clearing collector"""
        success, response = self.run_test(
            "Clear Collector",
            "DELETE",
            f"collector/clear/{self.session_id}",
            200
        )
        return success

    def test_delete_collector(self):
        """Test deleting collector"""
        success, response = self.run_test(
            "Delete Collector",
            "DELETE",
            f"collector/delete/{self.session_id}",
            200
        )
        return success

    def test_list_sessions(self):
        """Test listing active sessions"""
        success, response = self.run_test(
            "List Sessions",
            "GET",
            "collector/sessions",
            200
        )
        return success, response

    def test_strict_mode_enforcement(self):
        """Test strict mode enforcement"""
        # Create a collector with strict mode
        strict_session_id = f"strict-test-{uuid.uuid4()}"
        self.test_create_collector(session_id=strict_session_id, strict_mode=True)
        
        # Try to process a response without JSON in strict mode
        print("\n🔍 Testing Strict Mode Enforcement...")
        success, response = self.test_process_llm_response(
            "This is a response without any JSON content.",
            strict_mode=True,
            session_id=strict_session_id
        )
        
        # In strict mode, this should fail
        if not success and response.get('detail', '').startswith('JSON response expected'):
            print("✅ Strict mode correctly enforced")
            self.tests_passed += 1
            return True
        else:
            print("❌ Strict mode not enforced correctly")
            return False

    def test_json_extraction_with_comments(self):
        """Test JSON extraction with comments"""
        test_content = """
        Here's the analysis: 
        
        {
          "task": "demo",
          "status": "active"
        } // Comment here
        
        Additional data: 
        
        {
          "priority": "high",
          "timeout": 300
        }
        
        /* Multi-line comment
           with nested content
           that should be ignored */
        """
        
        success, response = self.test_process_llm_response(test_content)
        
        if success:
            extracted_json = response.get('extracted_json', {})
            expected_keys = ["task", "status", "priority", "timeout"]
            
            all_keys_present = all(key in extracted_json for key in expected_keys)
            if all_keys_present:
                print("✅ JSON correctly extracted with comments stripped")
                return True
            else:
                print(f"❌ Not all expected keys found. Found: {list(extracted_json.keys())}")
                return False
        return False

    def test_memory_operations(self):
        """Test memory operations (peek, pop, fetch)"""
        # Add multiple entries
        self.test_process_llm_response('{"entry1": "value1"}')
        self.test_process_llm_response('{"entry2": "value2"}')
        
        # Test peek
        success, peek_response = self.test_peek_latest()
        if not success or 'entry2' not in json.dumps(peek_response):
            print("❌ Peek operation failed")
            return False
            
        # Test fetch (should merge all entries)
        success, fetch_response = self.test_fetch_merged()
        if not success:
            print("❌ Fetch operation failed")
            return False
            
        merged_data = fetch_response.get('merged_data', {})
        if 'entry1' not in merged_data or 'entry2' not in merged_data:
            print("❌ Fetch did not correctly merge entries")
            return False
            
        # Test pop
        success, pop_response = self.test_pop_latest()
        if not success or 'entry2' not in json.dumps(pop_response):
            print("❌ Pop operation failed")
            return False
            
        # Peek again - should now show entry1
        success, peek_response = self.test_peek_latest()
        if not success or 'entry1' not in json.dumps(peek_response):
            print("❌ Pop did not correctly remove the latest entry")
            return False
            
        print("✅ Memory operations working correctly")
        return True

    def test_session_persistence(self):
        """Test session persistence across operations"""
        # Create a new session
        persistent_session = f"persistent-test-{uuid.uuid4()}"
        self.test_create_collector(session_id=persistent_session)
        
        # Add data
        self.test_process_llm_response('{"persistent": "data"}', session_id=persistent_session)
        
        # Check sessions list
        success, sessions_response = self.test_list_sessions()
        if not success:
            print("❌ Failed to list sessions")
            return False
            
        # Verify our session exists
        session_found = False
        for session in sessions_response.get('active_sessions', []):
            if session.get('session_id') == persistent_session:
                session_found = True
                break
                
        if not session_found:
            print("❌ Session persistence failed")
            return False
            
        print("✅ Session persistence working correctly")
        return True

    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        # Test non-existent session
        print("\n🔍 Testing Error Handling - Non-existent Session...")
        success, response = self.run_test(
            "Access Non-existent Session",
            "GET",
            f"collector/status/non-existent-{uuid.uuid4()}",
            404
        )
        
        if success:
            print("❌ Should have failed with 404")
            return False
            
        # Test empty session ID
        print("\n🔍 Testing Error Handling - Empty Session ID...")
        success, response = self.run_test(
            "Create Collector with Empty Session ID",
            "POST",
            "collector/create",
            400,  # Expecting bad request
            data={"session_id": "", "strict_mode": False}
        )
        
        if success:
            print("❌ Should have failed with 400")
            return False
            
        print("✅ Error handling working correctly")
        return True

def main():
    # Setup
    tester = FloJsonCollectorTester()
    
    print("=" * 50)
    print("🧪 STARTING FLOJSONCOLLECTOR API TESTS")
    print("=" * 50)
    
    # Basic API tests
    tester.test_root_endpoint()
    
    # Create collector and test basic operations
    tester.test_create_collector()
    tester.test_get_collector_status()
    
    # Test JSON extraction with comments
    tester.test_json_extraction_with_comments()
    
    # Test memory operations
    tester.test_memory_operations()
    
    # Test memory trail
    tester.test_get_memory_trail()
    
    # Test advanced features
    tester.test_create_iterator()
    tester.test_iterator_next()
    tester.test_rewind_memory()
    
    # Test session management
    tester.test_session_persistence()
    tester.test_list_sessions()
    
    # Test error handling
    tester.test_error_handling()
    
    # Test strict mode
    tester.test_strict_mode_enforcement()
    
    # Clean up
    tester.test_clear_collector()
    tester.test_delete_collector()
    
    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print("=" * 50)
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
