#!/usr/bin/env python3
"""
End-to-End Tests for Attendance Application
Tests complete user workflows
"""

import unittest
import requests
import os
import json
import time


class TestAttendanceE2E(unittest.TestCase):
    """E2E tests for complete attendance workflows"""

    def setUp(self):
        self.base_url = os.getenv('APP_URL', 'http://localhost:8081')
        self.timeout  = 15
        self.headers  = {'Content-Type': 'application/json'}

    def _is_app_running(self):
        """Check if app is running"""
        try:
            response = requests.get(
                f"{self.base_url}/attendance/healthz",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

    # ── E2E TEST 1: Full Health Workflow ─────────────────────────
    def test_complete_health_workflow(self):
        """Test complete health check workflow"""
        if not self._is_app_running():
            self.skipTest("App not running")

        # Step 1: Check health
        health = requests.get(
            f"{self.base_url}/attendance/healthz",
            timeout=self.timeout
        )
        self.assertEqual(health.status_code, 200)

        # Step 2: Parse response
        data = health.json()
        self.assertIsInstance(data, dict)

        # Step 3: Verify mysql status key exists
        self.assertIn('mysql', data)

    # ── E2E TEST 2: API Availability Workflow ────────────────────
    def test_all_endpoints_available(self):
        """Test all major endpoints are available"""
        if not self._is_app_running():
            self.skipTest("App not running")

        endpoints = [
            '/attendance/healthz',
            '/attendance/search',
        ]

        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                try:
                    response = requests.get(
                        f"{self.base_url}{endpoint}",
                        timeout=self.timeout
                    )
                    # Any response means endpoint exists
                    self.assertIsNotNone(response.status_code)
                except requests.exceptions.ConnectionError:
                    self.fail(f"Endpoint {endpoint} not reachable")

    # ── E2E TEST 3: Service Stability ───────────────────────────
    def test_service_stability(self):
        """Test service responds consistently"""
        if not self._is_app_running():
            self.skipTest("App not running")

        # Call health 3 times — should always return 200
        for i in range(3):
            response = requests.get(
                f"{self.base_url}/attendance/healthz",
                timeout=self.timeout
            )
            self.assertEqual(
                response.status_code, 200,
                f"Failed on attempt {i+1}"
            )
            time.sleep(1)

    # ── E2E TEST 4: Response Schema ──────────────────────────────
    def test_health_response_schema(self):
        """Test health response has correct schema"""
        if not self._is_app_running():
            self.skipTest("App not running")

        response = requests.get(
            f"{self.base_url}/attendance/healthz",
            timeout=self.timeout
        )

        data = response.json()

        # Schema validation
        required_keys = ['mysql']
        for key in required_keys:
            self.assertIn(
                key, data,
                f"Missing key '{key}' in response"
            )


if __name__ == '__main__':
    unittest.main()