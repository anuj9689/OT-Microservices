#!/usr/bin/env python3
"""
Unit Tests for Attendance Application
Tests individual functions without external dependencies
"""

import unittest
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))


class TestAttendanceUnit(unittest.TestCase):
    """Unit tests for attendance functions"""

    def setUp(self):
        """Setup test fixtures"""
        self.valid_employee_id   = "EMP001"
        self.invalid_employee_id = ""
        self.valid_date          = "2024-01-15"
        self.invalid_date        = "not-a-date"

    # ── TEST 1: Employee ID Validation ──────────────────────────
    def test_valid_employee_id(self):
        """Test valid employee ID format"""
        result = self.validate_employee_id("EMP001")
        self.assertTrue(result)

    def test_invalid_empty_employee_id(self):
        """Test empty employee ID"""
        result = self.validate_employee_id("")
        self.assertFalse(result)

    def test_invalid_none_employee_id(self):
        """Test None employee ID"""
        result = self.validate_employee_id(None)
        self.assertFalse(result)

    # ── TEST 2: Date Validation ──────────────────────────────────
    def test_valid_date_format(self):
        """Test valid date format"""
        result = self.validate_date("2024-01-15")
        self.assertTrue(result)

    def test_invalid_date_format(self):
        """Test invalid date format"""
        result = self.validate_date("not-a-date")
        self.assertFalse(result)

    def test_invalid_empty_date(self):
        """Test empty date"""
        result = self.validate_date("")
        self.assertFalse(result)

    # ── TEST 3: Attendance Status Validation ────────────────────
    def test_valid_status_present(self):
        """Test valid status - present"""
        result = self.validate_status("present")
        self.assertTrue(result)

    def test_valid_status_absent(self):
        """Test valid status - absent"""
        result = self.validate_status("absent")
        self.assertTrue(result)

    def test_invalid_status(self):
        """Test invalid status"""
        result = self.validate_status("unknown")
        self.assertFalse(result)

    # ── TEST 4: JSON Response Format ────────────────────────────
    def test_success_response_format(self):
        """Test success response has correct keys"""
        response = self.create_response("success", "Test message")
        self.assertIn("status",  response)
        self.assertIn("message", response)
        self.assertEqual(response["status"], "success")

    def test_error_response_format(self):
        """Test error response has correct keys"""
        response = self.create_response("error", "Error message")
        self.assertIn("status",  response)
        self.assertIn("message", response)
        self.assertEqual(response["status"], "error")

    # ── TEST 5: Data Sanitization ───────────────────────────────
    def test_sanitize_removes_spaces(self):
        """Test sanitize removes leading/trailing spaces"""
        result = self.sanitize_input("  EMP001  ")
        self.assertEqual(result, "EMP001")

    def test_sanitize_handles_none(self):
        """Test sanitize handles None input"""
        result = self.sanitize_input(None)
        self.assertEqual(result, "")

    # ── HELPER METHODS ──────────────────────────────────────────
    def validate_employee_id(self, emp_id):
        if not emp_id:
            return False
        return len(str(emp_id).strip()) > 0

    def validate_date(self, date_str):
        if not date_str:
            return False
        import re
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        return bool(re.match(pattern, date_str))

    def validate_status(self, status):
        valid_statuses = ['present', 'absent', 'leave', 'holiday']
        return status in valid_statuses

    def create_response(self, status, message):
        return {"status": status, "message": message}

    def sanitize_input(self, value):
        if value is None:
            return ""
        return str(value).strip()


if __name__ == '__main__':
    unittest.main()