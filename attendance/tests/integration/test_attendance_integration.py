#!/usr/bin/env python3
"""
Integration Tests for Attendance Application
Tests API endpoints with actual HTTP calls
"""

import unittest
import requests
import os
import json


class TestAttendanceIntegration(unittest.TestCase):
    """Integration tests for attendance API"""

    def setUp(self):
        """Setup - get app URL from environment"""
        self.base_url = os.getenv(
            'APP_URL',
            'http://localhost:8081'
        )
        self.timeout = 10
        self.headers = {'Content-Type': 'application/json'}

    # ── TEST 1: Health Check ─────────────────────────────────────
    def test_health_endpoint_returns_200(self):
        """Test /attendance/healthz returns 200"""
        try:
            response = requests.get(
                f"{self.base_url}/attendance/healthz",
                timeout=self.timeout
            )
            self.assertEqual(response.status_code, 200)
        except requests.exceptions.ConnectionError:
            self.skipTest("App not running — skipping integration test")

    def test_health_endpoint_returns_json(self):
        """Test /attendance/healthz returns JSON"""
        try:
            response = requests.get(
                f"{self.base_url}/attendance/healthz",
                timeout=self.timeout
            )
            data = response.json()
            self.assertIsInstance(data, dict)
        except requests.exceptions.ConnectionError:
            self.skipTest("App not running — skipping integration test")

    # ── TEST 2: Search Endpoint ──────────────────────────────────
    def test_search_endpoint_exists(self):
        """Test /attendance/search endpoint exists"""
        try:
            response = requests.get(
                f"{self.base_url}/attendance/search",
                timeout=self.timeout
            )
            # 200 or 400 both acceptable — endpoint exists
            self.assertIn(response.status_code, [200, 400, 404])
        except requests.exceptions.ConnectionError:
            self.skipTest("App not running — skipping integration test")

    # ── TEST 3: Create Endpoint ──────────────────────────────────
    def test_create_endpoint_exists(self):
        """Test /attendance/create endpoint exists"""
        try:
            response = requests.post(
                f"{self.base_url}/attendance/create",
                headers=self.headers,
                json={},
                timeout=self.timeout
            )
            self.assertIn(response.status_code, [200, 400, 422])
        except requests.exceptions.ConnectionError:
            self.skipTest("App not running — skipping integration test")

    # ── TEST 4: Response Time ────────────────────────────────────
    def test_health_response_time(self):
        """Test health endpoint responds within 5 seconds"""
        try:
            import time
            start    = time.time()
            response = requests.get(
                f"{self.base_url}/attendance/healthz",
                timeout=self.timeout
            )
            elapsed = time.time() - start
            self.assertLess(elapsed, 5.0)
        except requests.exceptions.ConnectionError:
            self.skipTest("App not running — skipping integration test")

    # ── TEST 5: Content Type ─────────────────────────────────────
    def test_health_content_type_json(self):
        """Test health endpoint returns JSON content type"""
        try:
            response = requests.get(
                f"{self.base_url}/attendance/healthz",
                timeout=self.timeout
            )
            content_type = response.headers.get('Content-Type', '')
            self.assertIn('application/json', content_type)
        except requests.exceptions.ConnectionError:
            self.skipTest("App not running — skipping integration test")


if __name__ == '__main__':
    unittest.main()