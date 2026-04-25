@Library('jenkins-shared-library@main') _

import org.example.DeploymentManager
import org.example.NotificationManager
import org.example.TestManager

pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timestamps()
    }

    parameters {
        choice(
            name: 'SERVICE',
            choices: ['attendance', 'employee', 'salary', 'frontend'],
            description: 'Which microservice to deploy'
        )
        string(
            name: 'VERSION',
            defaultValue: '1.0.0',
            description: 'Semver version e.g. 1.0.0'
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
    }

    environment {
        BRANCH_NAME = "${env.GIT_BRANCH ?: 'master'}"
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
                    milestone(1)
                    new DeploymentManager(this).validateConfig(
                        params.SERVICE,
                        'dev',
                        params.VERSION
                    )
                }
            }
        }

        // ── STAGE 3: INSTALL TEST DEPENDENCIES ────────────────
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
                            new TestManager(this)
                                .runIntegrationTests(params.SERVICE, '')
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
                    new TestManager(this)
                        .runE2ETests(params.SERVICE, '')
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

        // ── STAGE 6: GENERATE PDF REPORT ───────────────────────
        stage('Generate PDF Report') {
            steps {
                script {
                    new TestManager(this)
                        .generatePDFReport(params.SERVICE)
                }
            }
        }

        // ── STAGE 7: PUBLISH RESULTS ───────────────────────────
        stage('Publish Results') {
            steps {
                script {
                    new TestManager(this)
                        .publishResults(params.SERVICE)
                }
            }
        }

        // ══════════════════════════════════════════════════════
        // DEV — FULLY AUTOMATIC (no approval)
        // Canary strategy use hoti hai dev pe
        // ══════════════════════════════════════════════════════
        stage('Deploy to Dev') {
            steps {
                script {
                    milestone(2)
                    echo "=== AUTO DEPLOY TO DEV — NO APPROVAL NEEDED ==="

                    new DeploymentManager(this).deploy(
                        params.SERVICE, 'dev', params.VERSION
                    )
                }
            }
            post {
                success {
                    script {
                        echo "Running health check on dev..."
                        def healthy = performHealthCheck(
                            params.SERVICE, 'dev'
                        )
                        if (!healthy) {
                            echo "Dev health check FAILED — rolling back"
                            new DeploymentManager(this)
                                .rollback(params.SERVICE, 'dev')
                        } else {
                            echo "Dev health check PASSED"
                        }
                    }
                }
            }
        }

        // ══════════════════════════════════════════════════════
        // STAGING — MANUAL APPROVAL + Blue-Green
        // ══════════════════════════════════════════════════════
        stage('Approval for Staging') {
            steps {
                script {
                    // Notify approval pending
                    def details = getBuildDetails(this)
                    details.changes = details.changes +
                        " | STAGING APPROVAL PENDING"
                    new NotificationManager(this)
                        .notifyAll('UNSTABLE', details)

                    echo "Waiting for staging approval..."
                }

                timeout(time: 30, unit: 'MINUTES') {
                    input(
                        message: "Deploy ${params.SERVICE} v${params.VERSION} to STAGING?",
                        ok: 'Yes — Deploy to Staging'
                    )
                }
            }
        }

        stage('Deploy to Staging') {
            steps {
                script {
                    milestone(3)
                    echo "=== BLUE-GREEN DEPLOY TO STAGING ==="

                    new DeploymentManager(this).deploy(
                        params.SERVICE, 'staging', params.VERSION
                    )
                }
            }
            post {
                success {
                    script {
                        echo "Running health check on staging..."
                        def healthy = performHealthCheck(
                            params.SERVICE, 'staging'
                        )
                        if (!healthy) {
                            echo "Staging health check FAILED — rolling back"
                            new DeploymentManager(this)
                                .rollback(params.SERVICE, 'staging')
                            error "Staging health check failed — rolled back"
                        } else {
                            echo "Staging health check PASSED"
                        }
                    }
                }
            }
        }

        // ══════════════════════════════════════════════════════
        // PRODUCTION — MANUAL APPROVAL + Blue-Green
        // ══════════════════════════════════════════════════════
        stage('Approval for Prod') {
            steps {
                script {
                    def details = getBuildDetails(this)
                    details.changes = details.changes +
                        " | PROD APPROVAL PENDING"
                    new NotificationManager(this)
                        .notifyAll('UNSTABLE', details)

                    echo "Waiting for production approval..."
                }

                timeout(time: 60, unit: 'MINUTES') {
                    input(
                        message: "Deploy ${params.SERVICE} v${params.VERSION} to PRODUCTION?",
                        ok: 'APPROVE PRODUCTION DEPLOY'
                    )
                }
            }
        }

        stage('Deploy to Prod') {
            steps {
                script {
                    milestone(4)
                    echo "=== BLUE-GREEN DEPLOY TO PRODUCTION ==="

                    new DeploymentManager(this).deploy(
                        params.SERVICE, 'prod', params.VERSION
                    )
                }
            }
            post {
                success {
                    script {
                        echo "Running health check on prod..."
                        def healthy = performHealthCheck(
                            params.SERVICE, 'prod'
                        )
                        if (!healthy) {
                            echo "PROD health check FAILED — AUTO ROLLBACK"
                            new DeploymentManager(this)
                                .rollback(params.SERVICE, 'prod')

                            def details = getBuildDetails(this)
                            details.changes = details.changes +
                                " | PROD HEALTH FAILED — ROLLBACK DONE"
                            new NotificationManager(this)
                                .notifyAll('FAILURE', details)

                            error "Prod health check failed — rolled back"
                        } else {
                            echo "Prod health check PASSED"
                        }
                    }
                }
            }
        }
    }

    // ── POST BLOCKS ───────────────────────────────────────────
    post {

        always {
            script {
                try {
                    new TestManager(this).publishResults(params.SERVICE)
                } catch (Exception e) {
                    echo "Publish warning: ${e.message}"
                }
            }
        }

        success {
            script {
                def details = getBuildDetails(this)
                details.changes = details.changes +
                    " | ALL ENVIRONMENTS DEPLOYED SUCCESSFULLY"
                new NotificationManager(this).notifyAll('SUCCESS', details)
            }
        }

        failure {
            script {
                def details = getBuildDetails(this)
                try {
                    new DeploymentManager(this)
                        .rollback(params.SERVICE, 'prod')
                    new DeploymentManager(this)
                        .rollback(params.SERVICE, 'staging')
                    details.changes = details.changes +
                        " | FAILED — AUTO ROLLBACK DONE"
                } catch (Exception e) {
                    details.changes = details.changes +
                        " | FAILED — ROLLBACK ERROR: ${e.message}"
                }
                new NotificationManager(this).notifyAll('FAILURE', details)
            }
        }

        unstable {
            script {
                def details = getBuildDetails(this)
                details.changes = details.changes +
                    " | BUILD UNSTABLE"
                new NotificationManager(this).notifyAll('UNSTABLE', details)
            }
        }

        cleanup {
            cleanWs()
        }
    }
}

// ── HEALTH CHECK FUNCTION ─────────────────────────────────────
def performHealthCheck(String service, String environment) {
    echo "=== HEALTH CHECK: ${service} on ${environment} ==="

    try {
        // Step 1 — pods running hain check karo
        def runningPods = sh(
            script: """
                kubectl get pods -n ${environment} \
                    -l app=${service} \
                    --field-selector=status.phase=Running \
                    --no-headers 2>/dev/null | wc -l
            """,
            returnStdout: true
        ).trim()

        echo "Running pods: ${runningPods}"

        if (runningPods.toInteger() == 0) {
            echo "No running pods found"
            return false
        }

        // Step 2 — ClusterIP lo
        def clusterIP = sh(
            script: """
                kubectl get svc ${service} -n ${environment} \
                    -o jsonpath='{.spec.clusterIP}' 2>/dev/null \
                    || echo ''
            """,
            returnStdout: true
        ).trim()

        if (!clusterIP || clusterIP == '') {
            echo "Service ClusterIP not found — skipping HTTP check"
            return true
        }

        echo "Service ClusterIP: ${clusterIP}"

        // Step 3 — HTTP health check with retry
        for (int attempt = 1; attempt <= 5; attempt++) {
            echo "HTTP health check attempt ${attempt}/5..."

            def httpStatus = sh(
                script: """
                    curl -s -o /dev/null \
                        -w "%{http_code}" \
                        --connect-timeout 5 \
                        --max-time 10 \
                        http://${clusterIP}/${service}/healthz \
                        2>/dev/null || echo "000"
                """,
                returnStdout: true
            ).trim()

            echo "HTTP Status: ${httpStatus}"

            if (httpStatus == '200') {
                echo "Health check PASSED on attempt ${attempt}"
                return true
            }

            if (attempt < 5) {
                echo "Retrying in 10 seconds..."
                sleep(10)
            }
        }

        echo "Health check FAILED after 5 attempts"
        return false

    } catch (Exception e) {
        echo "Health check error: ${e.message}"
        return false
    }
}

// ── BUILD DETAILS HELPER ──────────────────────────────────────
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
        branch      : ctx.env.GIT_BRANCH     ?: 'master',
        service     : service,
        version     : ctx.params.VERSION     ?: '0.0.0',
        environment : 'dev → staging → prod',
        duration    : ctx.currentBuild.durationString ?: 'N/A',
        changes     : changes,
        recipients  : ctx.params.RECIPIENTS  ?: 'YOUR_EMAIL@gmail.com'
    ]
}