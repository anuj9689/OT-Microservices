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
        // Unit and Integration run in parallel
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
        // Runs after parallel tests complete
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

        // ── STAGE 9: DEPLOY TO DEV ─────────────────────────────
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

        // ── STAGE 10: DEPLOY TO STAGING ────────────────────────
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

        // ── STAGE 11: PROD APPROVAL ────────────────────────────
        stage('Approval for Prod') {
            when {
                expression { return params.ENVIRONMENT == 'prod' }
            }
            steps {
                timeout(time: 30, unit: 'MINUTES') {
                    input(
                        message: 'All tests passed. Deploy to PROD?',
                        ok: 'Yes Deploy'
                    )
                }
            }
        }

        // ── STAGE 12: DEPLOY TO PROD ───────────────────────────
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
                details.changes = details.changes + " | ALL TESTS PASSED"
                new NotificationManager(this).notifyAll('SUCCESS', details)
            }
        }

        failure {
            script {
                def details = getBuildDetails(this)
                details.changes = details.changes + " | TESTS FAILED"
                new NotificationManager(this).notifyAll('FAILURE', details)
            }
        }

        unstable {
            script {
                def details = getBuildDetails(this)
                details.changes = details.changes + " | BUILD UNSTABLE"
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

    return [
        jobName    : ctx.env.JOB_NAME       ?: 'Unknown',
        buildNumber: ctx.env.BUILD_NUMBER   ?: '0',
        buildUrl   : ctx.env.BUILD_URL      ?: 'http://localhost:8080',
        branch     : ctx.env.GIT_BRANCH     ?: 'master',
        service    : ctx.params.SERVICE     ?: 'unknown',
        version    : ctx.params.VERSION     ?: '0.0.0',
        environment: ctx.params.ENVIRONMENT ?: 'unknown',
        duration   : ctx.currentBuild.durationString ?: 'N/A',
        changes    : changes,
        recipients : ctx.params.RECIPIENTS  ?: 'YOUR_EMAIL@gmail.com'
    ]
}