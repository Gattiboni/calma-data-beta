import requests
import sys
import json
from datetime import datetime

class CalmaDataAPITester:
    def __init__(self, base_url="/api"):
        # Use the public endpoint from frontend/.env
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, params=None, expected_keys=None):
        """Run a single API test"""
        # Construct full URL - using relative path since we're testing via public endpoint
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(f"http://localhost:8001{url}", params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(f"http://localhost:8001{url}", json=params, timeout=10)

            print(f"   Status Code: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                
                # Check response structure if expected_keys provided
                if expected_keys:
                    try:
                        json_data = response.json()
                        missing_keys = [key for key in expected_keys if key not in json_data]
                        if missing_keys:
                            print(f"⚠️  Warning: Missing expected keys: {missing_keys}")
                            success = False
                        else:
                            print(f"✅ All expected keys present: {expected_keys}")
                    except Exception as e:
                        print(f"⚠️  Warning: Could not parse JSON response: {e}")
                        success = False
                        
                return success, response.json() if success else {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append(f"{name}: Expected {expected_status}, got {response.status_code}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append(f"{name}: {str(e)}")
            return False, {}

    def test_health_integrations(self):
        """Test health endpoint and verify integrations"""
        success, response = self.run_test(
            "Health Check with Integrations",
            "GET", 
            "health",
            200,
            expected_keys=["status", "integrations"]
        )
        if success:
            integrations = response.get("integrations", {})
            ga4_status = integrations.get("ga4", False)
            google_ads_status = integrations.get("google_ads", False)
            
            print(f"✅ Health endpoint returns status: {response.get('status')}")
            print(f"📊 Integration Status:")
            print(f"   - GA4: {ga4_status}")
            print(f"   - Google Ads: {google_ads_status}")
            
            if ga4_status and google_ads_status:
                print("✅ Both GA4 and Google Ads integrations are active")
                return True
            else:
                print("❌ One or both integrations are not active")
                self.failed_tests.append("Health Check: GA4 or Google Ads integration not active")
                return False
        else:
            print("❌ Health endpoint failed")
            return False

    def test_kpis_real_data(self):
        """Test KPIs endpoint with real integration data"""
        params = {"start": "2025-08-01", "end": "2025-08-07"}
        expected_keys = ["receita", "reservas", "diarias", "clicks", "impressoes", "cpc", "custo"]
        
        success, response = self.run_test(
            "KPIs Endpoint (Real Data)",
            "GET",
            "kpis",
            200,
            params=params,
            expected_keys=expected_keys
        )
        
        if success:
            print(f"📊 Complete KPI Response JSON:")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            
            # Check for real data (non-zero values from integrations)
            receita = response.get('receita', 0)
            reservas = response.get('reservas', 0)
            diarias = response.get('diarias', 0)
            clicks = response.get('clicks', 0)
            impressoes = response.get('impressoes', 0)
            cpc = response.get('cpc', 0)
            custo = response.get('custo', 0)
            
            print(f"✅ KPI values:")
            print(f"   - Receita (GA4): R$ {receita}")
            print(f"   - Reservas (GA4): {reservas}")
            print(f"   - Diárias (GA4): {diarias}")
            print(f"   - Clicks (Google Ads): {clicks}")
            print(f"   - Impressões (Google Ads): {impressoes}")
            print(f"   - CPC (Google Ads): R$ {cpc}")
            print(f"   - Custo (Google Ads): R$ {custo}")
            
            # Validate that we have real data (not just mock data)
            has_real_ga4_data = receita > 0 or reservas > 0 or diarias > 0
            has_real_ads_data = clicks > 0 and impressoes > 0 and custo > 0
            
            if has_real_ga4_data:
                print("✅ GA4 data appears to be real (non-zero values)")
            else:
                print("⚠️  GA4 data may be mock/zero values")
                
            if has_real_ads_data:
                print("✅ Google Ads data appears to be real (non-zero values)")
            else:
                print("⚠️  Google Ads data may be mock/zero values")
                
            return True
        return False

    def test_acquisition_by_channel(self):
        """Test acquisition by channel endpoint"""
        params = {"metric": "users", "start": "2025-08-01", "end": "2025-08-07"}
        expected_keys = ["metric", "points"]
        
        success, response = self.run_test(
            "Acquisition by Channel",
            "GET",
            "acquisition-by-channel", 
            200,
            params=params,
            expected_keys=expected_keys
        )
        
        if success:
            points = response.get("points", [])
            print(f"✅ Acquisition data: metric={response.get('metric')}, points_count={len(points)}")
            if points and len(points) > 0:
                print(f"   Sample point: {points[0]}")
            return True
        return False

    def test_revenue_by_uh(self):
        """Test revenue by UH endpoint"""
        params = {"start": "2025-08-01", "end": "2025-08-07"}
        expected_keys = ["points"]
        
        success, response = self.run_test(
            "Revenue by UH",
            "GET",
            "revenue-by-uh",
            200,
            params=params,
            expected_keys=expected_keys
        )
        
        if success:
            points = response.get("points", [])
            print(f"✅ Revenue UH data: points_count={len(points)}")
            return True
        return False

    def test_sales_uh_stacked(self):
        """Test sales UH stacked endpoint"""
        params = {"start": "2025-08-01", "end": "2025-08-07"}
        expected_keys = ["series_labels", "points"]
        
        success, response = self.run_test(
            "Sales UH Stacked",
            "GET",
            "sales-uh-stacked",
            200,
            params=params,
            expected_keys=expected_keys
        )
        
        if success:
            series_labels = response.get("series_labels", [])
            points = response.get("points", [])
            print(f"✅ Sales UH data: series_labels={series_labels}, points_count={len(points)}")
            return True
        return False

    def test_campaign_conversion_heatmap(self):
        """Test campaign conversion heatmap endpoint"""
        params = {"start": "2025-08-01", "end": "2025-08-07"}
        expected_keys = ["cells"]
        
        success, response = self.run_test(
            "Campaign Conversion Heatmap",
            "GET",
            "campaign-conversion-heatmap",
            200,
            params=params,
            expected_keys=expected_keys
        )
        
        if success:
            cells = response.get("cells", [])
            print(f"✅ Heatmap data: cells_count={len(cells)}")
            return True
        return False

    def test_performance_table(self):
        """Test performance table endpoint"""
        params = {"start": "2025-08-01", "end": "2025-08-07"}
        expected_keys = ["rows"]
        
        success, response = self.run_test(
            "Performance Table",
            "GET",
            "performance-table",
            200,
            params=params,
            expected_keys=expected_keys
        )
        
        if success:
            rows = response.get("rows", [])
            print(f"✅ Performance table data: rows_count={len(rows)}")
            if rows and len(rows) > 0:
                print(f"   Sample row: {rows[0].get('name')} - clicks: {rows[0].get('clicks')}")
            return True
        return False

def main():
    print("🚀 Starting Calma Data API Tests...")
    print("=" * 50)
    
    # Setup
    tester = CalmaDataAPITester()
    
    # Run all tests
    test_methods = [
        tester.test_health,
        tester.test_kpis,
        tester.test_acquisition_by_channel,
        tester.test_revenue_by_uh,
        tester.test_sales_uh_stacked,
        tester.test_campaign_conversion_heatmap,
        tester.test_performance_table
    ]
    
    for test_method in test_methods:
        test_method()
    
    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.failed_tests:
        print("\n❌ Failed Tests:")
        for failure in tester.failed_tests:
            print(f"   - {failure}")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())