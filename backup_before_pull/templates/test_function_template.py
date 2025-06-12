
def test_$function_name$():
    """Test the $http_method$ $endpoint_path$ endpoint"""
    with TestClient(app) as client:
        response = client.$http_method_lower$("$full_url$")
    assert response.status_code == 200
    # Add more specific assertions here based on expected response
    assert "message" in response.json()
