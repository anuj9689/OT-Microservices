#!/usr/bin/env python3
"""
PDF Report Generator for Test Results
Generates a complete test report in PDF format
"""

from fpdf import FPDF
import xml.etree.ElementTree as ET
import os
import sys
from datetime import datetime


class TestReportPDF(FPDF):

    def header(self):
        self.set_font('Arial', 'B', 16)
        self.set_fill_color(44, 62, 80)
        self.set_text_color(255, 255, 255)
        self.cell(0, 15, 'OT-Microservices Test Report', 0, 1, 'C', True)
        self.set_text_color(0, 0, 0)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()} | Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 0, 'C')

    def section_title(self, title, color=(52, 152, 219)):
        self.set_font('Arial', 'B', 13)
        self.set_fill_color(*color)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, title, 0, 1, 'L', True)
        self.set_text_color(0, 0, 0)
        self.ln(3)

    def info_row(self, label, value, bg=False):
        self.set_font('Arial', 'B', 10)
        if bg:
            self.set_fill_color(240, 240, 240)
        self.cell(70, 8, label, 1, 0, 'L', bg)
        self.set_font('Arial', '', 10)
        self.cell(0, 8, str(value), 1, 1, 'L', bg)

    def test_row(self, name, status, time_taken):
        if status == 'PASSED':
            self.set_fill_color(212, 237, 218)
            status_color = (40, 167, 69)
        elif status == 'FAILED':
            self.set_fill_color(248, 215, 218)
            status_color = (220, 53, 69)
        else:
            self.set_fill_color(255, 243, 205)
            status_color = (255, 193, 7)

        self.set_font('Arial', '', 9)
        self.cell(120, 7, name[:60], 1, 0, 'L', True)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(*status_color)
        self.cell(30, 7, status, 1, 0, 'C', True)
        self.set_text_color(0, 0, 0)
        self.set_font('Arial', '', 9)
        self.cell(0, 7, f"{time_taken}s", 1, 1, 'C', True)


def parse_junit_xml(xml_path):
    """Parse JUnit XML report"""
    results = {
        'total': 0, 'passed': 0,
        'failed': 0, 'skipped': 0,
        'time': 0, 'tests': []
    }

    if not os.path.exists(xml_path):
        return results

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        suites = root.findall('.//testsuite')
        for suite in suites:
            results['total']   += int(suite.get('tests',    0))
            results['failed']  += int(suite.get('failures', 0))
            results['skipped'] += int(suite.get('skipped',  0))
            results['time']    += float(suite.get('time',   0))

            for case in suite.findall('testcase'):
                name   = case.get('name', 'Unknown')
                time_t = round(float(case.get('time', 0)), 3)

                if case.find('failure') is not None:
                    status = 'FAILED'
                elif case.find('skipped') is not None:
                    status = 'SKIPPED'
                else:
                    status = 'PASSED'

                results['tests'].append({
                    'name': name, 'status': status, 'time': time_t
                })

        results['passed'] = (results['total']
                             - results['failed']
                             - results['skipped'])

    except Exception as e:
        print(f"Warning: Could not parse XML: {e}")

    return results


def parse_coverage_xml(xml_path):
    """Parse coverage XML report"""
    coverage = {'line_rate': 0, 'branch_rate': 0, 'timestamp': 'N/A'}

    if not os.path.exists(xml_path):
        return coverage

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        rate = float(root.get('line-rate', 0)) * 100
        branch = float(root.get('branch-rate', 0)) * 100
        coverage['line_rate']   = round(rate, 2)
        coverage['branch_rate'] = round(branch, 2)
    except Exception as e:
        print(f"Warning: Could not parse coverage: {e}")

    return coverage


def generate_pdf_report(
    junit_xml   = 'tests/reports/junit-results.xml',
    coverage_xml= 'tests/reports/coverage.xml',
    output_pdf  = 'tests/reports/test-report.pdf',
    build_info  = None
):
    """Generate complete PDF report"""

    if build_info is None:
        build_info = {
            'job_name'    : os.getenv('JOB_NAME',     'OT-Microservices'),
            'build_number': os.getenv('BUILD_NUMBER', '1'),
            'branch'      : os.getenv('GIT_BRANCH',   'master'),
            'service'     : os.getenv('SERVICE',      'attendance'),
            'environment' : os.getenv('ENVIRONMENT',  'staging'),
            'build_url'   : os.getenv('BUILD_URL',    'http://localhost:8080'),
        }

    # Parse results
    results  = parse_junit_xml(junit_xml)
    coverage = parse_coverage_xml(coverage_xml)

    # Create PDF
    pdf = TestReportPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ── Section 1: Build Info ─────────────────────────────────
    pdf.section_title('Build Information', (44, 62, 80))
    pdf.info_row('Job Name',     build_info['job_name'],     True)
    pdf.info_row('Build Number', build_info['build_number'], False)
    pdf.info_row('Branch',       build_info['branch'],       True)
    pdf.info_row('Service',      build_info['service'],      False)
    pdf.info_row('Environment',  build_info['environment'],  True)
    pdf.info_row('Generated',    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), False)
    pdf.ln(8)

    # ── Section 2: Test Summary ───────────────────────────────
    pdf.section_title('Test Summary', (39, 174, 96))

    pass_rate = 0
    if results['total'] > 0:
        pass_rate = round(results['passed'] / results['total'] * 100, 1)

    pdf.info_row('Total Tests',  results['total'],   True)
    pdf.info_row('Passed',       results['passed'],  False)
    pdf.info_row('Failed',       results['failed'],  True)
    pdf.info_row('Skipped',      results['skipped'], False)
    pdf.info_row('Pass Rate',    f"{pass_rate}%",    True)
    pdf.info_row('Total Time',   f"{round(results['time'], 2)}s", False)
    pdf.ln(8)

    # ── Section 3: Code Coverage ──────────────────────────────
    pdf.section_title('Code Coverage', (142, 68, 173))

    threshold = 80
    line_cov  = coverage['line_rate']
    cov_status = 'PASSED' if line_cov >= threshold else 'FAILED'

    pdf.info_row('Line Coverage',   f"{line_cov}%",            True)
    pdf.info_row('Branch Coverage', f"{coverage['branch_rate']}%", False)
    pdf.info_row('Threshold',       f"{threshold}%",           True)
    pdf.info_row('Coverage Status', cov_status,                False)
    pdf.ln(8)

    # ── Section 4: Test Details ───────────────────────────────
    pdf.section_title('Test Details', (52, 152, 219))

    # Table header
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(44, 62, 80)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(120, 8, 'Test Name',   1, 0, 'C', True)
    pdf.cell(30,  8, 'Status',      1, 0, 'C', True)
    pdf.cell(0,   8, 'Time (s)',    1, 1, 'C', True)
    pdf.set_text_color(0, 0, 0)

    # Test rows
    for i, test in enumerate(results['tests']):
        pdf.test_row(
            test['name'],
            test['status'],
            test['time']
        )

    pdf.ln(8)

    # ── Section 5: Overall Status ─────────────────────────────
    overall = 'PASSED'
    if results['failed'] > 0 or line_cov < threshold:
        overall = 'FAILED'

    if overall == 'PASSED':
        pdf.set_fill_color(212, 237, 218)
        pdf.set_text_color(40, 167, 69)
    else:
        pdf.set_fill_color(248, 215, 218)
        pdf.set_text_color(220, 53, 69)

    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 15, f'Overall Result: {overall}', 1, 1, 'C', True)
    pdf.set_text_color(0, 0, 0)

    # Save PDF
    os.makedirs(os.path.dirname(output_pdf), exist_ok=True)
    pdf.output(output_pdf)
    print(f"PDF report generated: {output_pdf}")

    return output_pdf


if __name__ == '__main__':
    generate_pdf_report()