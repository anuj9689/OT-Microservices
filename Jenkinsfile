@Library('jenkins-shared-library@main') _

import org.example.DeploymentManager
import org.example.NotificationManager
import org.example.TestManager


pipeline {
    agent any

    parameters {
        choice(
            name: 'SERVICE',
            choices: ['attendance', 'employee', 'salary', 'frontend'],
            description: 'Microservice to test and deploy'
        )
        string(
            name: 'VERSION',
            defaultValue: '1.0.0',
            description: 'Version to deploy'
        )
        choice(
            name: 'ENVIRONMENT',
            choices: ['dev', 'staging', 'prod'],
            description: 'Target environment'
        )
        string(
            name: 'RECIPIENTS',
            defaultValue: 'YOUR_EMAIL@gmail.com',
            description: 'Email recipients'
        )
        booleanParam(
            name: 'RUN_E2E',
            defaultValue: true,
            description: 'Run E2E tests?'
        )
        // ── NEW: SonarQube Parameters ─────────────────────────
        booleanParam(
            name: 'RUN_SONAR',
            defaultValue: true,
            description: 'Run SonarQube analysis?'
        )
        string(
            name: 'PR_NUMBER',
            defaultValue: '',
            description: 'PR number (empty for branch build)'
        )
        string(
            name: 'PR_BRANCH',
            defaultValue: '',
            description: 'PR source branch'
        )
        string(
            name: 'TARGET_BRANCH',
            defaultValue: 'master',
            description: 'PR target branch'
        )
    }

    environment {
        BRANCH_NAME = "${env.GIT_BRANCH ?: 'master'}"
        APP_URL     = "http://localhost:8081"
    }

    stages {

        // ── STAGE 1: NOTIFY START ──────────────────────────────
        stage('Notify Start') {
            steps {
                script {
                    new NotificationManager(this)
                        .notifyAll('STARTED', getBuildDetails(this))
                }
            }
        }

        // ── STAGE 2: VALIDATE ──────────────────────────────────
        stage('Validate') {
            steps {
                script {
                    new DeploymentManager(this).validateConfig(
                        params.SERVICE,
                        params.ENVIRONMENT,
                        params.VERSION
                    )
                }
            }
        }

        // ── STAGE 3: INSTALL DEPENDENCIES ─────────────────────
        stage('Install Test Dependencies') {
            steps {
                script {
                    new TestManager(this)
                        .installDependencies(params.SERVICE)
                }
            }
        }

        // ── STAGE 4: PARALLEL TESTS ────────────────────────────
        stage('Run Tests') {
            parallel {

                stage('Unit Tests') {
                    steps {
                        script {
                            new TestManager(this)
                                .runUnitTests(params.SERVICE)
                        }
                    }
                    post {
                        always {
                            junit(
                                testResults      : "${params.SERVICE}/tests/reports/unit-results.xml",
                                allowEmptyResults: true
                            )
                        }
                    }
                }

                stage('Integration Tests') {
                    steps {
                        script {
                            new TestManager(this).runIntegrationTests(
                                params.SERVICE,
                                env.APP_URL
                            )
                        }
                    }
                    post {
                        always {
                            junit(
                                testResults      : "${params.SERVICE}/tests/reports/integration-results.xml",
                                allowEmptyResults: true
                            )
                        }
                    }
                }
            }
        }

        // ── STAGE 5: E2E TESTS ─────────────────────────────────
        stage('E2E Tests') {
            when {
                expression { return params.RUN_E2E == true }
            }
            steps {
                script {
                    new TestManager(this).runE2ETests(
                        params.SERVICE,
                        env.APP_URL
                    )
                }
            }
            post {
                always {
                    junit(
                        testResults      : "${params.SERVICE}/tests/reports/e2e-results.xml",
                        allowEmptyResults: true
                    )
                }
            }
        }

        // ── STAGE 6: COVERAGE CHECK ────────────────────────────
        stage('Coverage Threshold Check') {
            steps {
                script {
                    new TestManager(this)
                        .checkCoverageThreshold(params.SERVICE)
                }
            }
        }

        // ── STAGE 7: GENERATE PDF REPORT ───────────────────────
        stage('Generate PDF Report') {
            steps {
                script {
                    new TestManager(this)
                        .generatePDFReport(params.SERVICE)
                }
            }
        }

        // ── STAGE 8: PUBLISH RESULTS ───────────────────────────
        stage('Publish Test Results') {
            steps {
                script {
                    new TestManager(this)
                        .publishResults(params.SERVICE)
                }
            }
        }

        // ── STAGE 9: SONARQUBE ANALYSIS ── NEW ─────────────────
        stage('SonarQube Analysis') {
            when {
                expression { return params.RUN_SONAR == true }
            }
            steps {
                script {
                    def sonar = new SonarQubeManager(this)

                    // PR build hai ya branch build check karo
                    if (params.PR_NUMBER?.trim()) {

                        // PR Analysis with decoration
                        sonar.runPRAnalysis(
                            params.SERVICE,
                            params.VERSION,
                            [
                                prNumber    : params.PR_NUMBER,
                                prBranch    : params.PR_BRANCH,
                                targetBranch: params.TARGET_BRANCH,
                                repo        : 'anuj9689/OT-Microservices'
                            ]
                        )

                    } else {

                        // Normal branch analysis
                        sonar.runBranchAnalysis(
                            params.SERVICE,
                            params.VERSION,
                            env.BRANCH_NAME
                        )
                    }
                }
            }
        }

        // ── STAGE 10: QUALITY GATE ── NEW ──────────────────────
        stage('Quality Gate') {
            when {
                expression { return params.RUN_SONAR == true }
            }
            steps {
                script {
                    def sonar = new SonarQubeManager(this)

                    // Wait for Quality Gate
                    // Pipeline FAIL hogi agar QG fail hua
                    sonar.waitForQualityGate()

                    // Metrics fetch karo aur log karo
                    def results = sonar.getAnalysisResults('OT-Microservices')
                    echo "SonarQube Metrics: ${results.metrics}"
                }
            }
        }

        // ── STAGE 11: DEPLOY TO DEV ────────────────────────────
        stage('Deploy to Dev') {
            when {
                expression { return params.ENVIRONMENT == 'dev' }
            }
            steps {
                script {
                    new DeploymentManager(this).deploy(
                        params.SERVICE, 'dev', params.VERSION)
                }
            }
        }

        // ── STAGE 12: DEPLOY TO STAGING ────────────────────────
        stage('Deploy to Staging') {
            when {
                anyOf {
                    expression { return params.ENVIRONMENT == 'staging' }
                    expression { return params.ENVIRONMENT == 'prod' }
                }
            }
            steps {
                script {
                    new DeploymentManager(this).deploy(
                        params.SERVICE, 'staging', params.VERSION)
                }
            }
        }

        // ── STAGE 13: PROD APPROVAL ────────────────────────────
        stage('Approval for Prod') {
            when {
                expression { return params.ENVIRONMENT == 'prod' }
            }
            steps {
                script {
                    def details = getBuildDetails(this)
                    details.changes = details.changes +
                        " | WAITING FOR PROD APPROVAL"
                    new NotificationManager(this)
                        .notifyAll('UNSTABLE', details)
                }
                timeout(time: 30, unit: 'MINUTES') {
                    input(
                        message: 'All tests passed. Quality Gate passed. Deploy to PROD?',
                        ok: 'Yes Deploy'
                    )
                }
            }
        }

        // ── STAGE 14: DEPLOY TO PROD ───────────────────────────
        stage('Deploy to Prod') {
            when {
                expression { return params.ENVIRONMENT == 'prod' }
            }
            steps {
                script {
                    new DeploymentManager(this).deploy(
                        params.SERVICE, 'prod', params.VERSION)
                }
            }
        }
    }

    // ── POST BLOCKS ───────────────────────────────────────────
    post {

        always {
            script {
                new TestManager(this)
                    .publishResults(params.SERVICE)
            }
        }

        success {
            script {
                def details = getBuildDetails(this)

                if (env.BRANCH_NAME?.contains('master') ||
                    env.BRANCH_NAME?.contains('main')) {
                    details.changes = details.changes +
                        " | MASTER DEPLOY — QG PASSED"
                } else {
                    details.changes = details.changes +
                        " | ALL TESTS PASSED — QG PASSED"
                }

                new NotificationManager(this).notifyAll('SUCCESS', details)
            }
        }

        failure {
            script {
                def details = getBuildDetails(this)

                try {
                    new DeploymentManager(this).rollback(
                        params.SERVICE,
                        params.ENVIRONMENT
                    )
                    details.changes = details.changes +
                        " | FAILED — AUTO ROLLBACK DONE"
                } catch (Exception e) {
                    details.changes = details.changes +
                        " | FAILED — ROLLBACK ALSO FAILED: ${e.message}"
                }

                new NotificationManager(this).notifyAll('FAILURE', details)
            }
        }

        unstable {
            script {
                def details = getBuildDetails(this)
                details.changes = details.changes +
                    " | UNSTABLE — CHECK SONAR/TESTS"
                new NotificationManager(this).notifyAll('UNSTABLE', details)
            }
        }

        cleanup {
            cleanWs()
        }
    }
}

// ── HELPER ────────────────────────────────────────────────────
def getBuildDetails(def ctx) {
    String changes = 'No changes'
    try {
        changes = ctx.sh(
            script: "git log -1 --pretty=format:'%s by %an'",
            returnStdout: true
        ).trim()
    } catch (Exception e) {
        changes = 'Could not fetch changes'
    }

    String buildUrl = ctx.env.BUILD_URL ?: 'http://localhost:8080'
    String service  = ctx.params.SERVICE ?: 'attendance'

    return [
        jobName     : ctx.env.JOB_NAME       ?: 'Unknown',
        buildNumber : ctx.env.BUILD_NUMBER   ?: '0',
        buildUrl    : buildUrl,
        artifactsUrl: "${buildUrl}artifact/${service}/tests/reports/test-report.pdf",
        testsUrl    : "${buildUrl}testReport/",
        coverageUrl : "${buildUrl}Coverage_20Report/",
        sonarUrl    : "http://localhost:9000/dashboard?id=OT-Microservices", // ← NEW
        branch      : ctx.env.GIT_BRANCH     ?: 'master',
        service     : service,
        version     : ctx.params.VERSION     ?: '0.0.0',
        environment : ctx.params.ENVIRONMENT ?: 'unknown',
        duration    : ctx.currentBuild.durationString ?: 'N/A',
        changes     : changes,
        recipients  : ctx.params.RECIPIENTS  ?: 'YOUR_EMAIL@gmail.com'
    ]
}