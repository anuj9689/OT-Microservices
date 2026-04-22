@Library('jenkins-shared-library@main') _

import org.example.DeploymentManager
import org.example.NotificationManager

pipeline {
    agent any

    parameters {
        choice(
            name: 'SERVICE',
            choices: ['attendance', 'employee', 'salary', 'frontend', 'notification'],
            description: 'Which microservice to deploy'
        )
        string(
            name: 'VERSION',
            defaultValue: '1.0.0',
            description: 'Semver version e.g. 1.0.0'
        )
        choice(
            name: 'ENVIRONMENT',
            choices: ['dev', 'staging', 'prod'],
            description: 'Target environment'
        )
        string(
            name: 'RECIPIENTS',
            defaultValue: 'YOUR_EMAIL@gmail.com',
            description: 'Email recipients comma separated'
        )
    }

    environment {
        JOB_NAME     = "${env.JOB_NAME}"
        BUILD_NUMBER = "${env.BUILD_NUMBER}"
        BUILD_URL    = "${env.BUILD_URL}"
        BRANCH_NAME  = "${env.GIT_BRANCH ?: 'master'}"
    }

    stages {

        // ── STAGE 1: NOTIFY START ──────────────────────────────
        stage('Notify Start') {
            steps {
                script {
                    def notifier = new NotificationManager(this)
                    def details  = getBuildDetails(this)

                    notifier.notifyAll('STARTED', details)
                }
            }
        }

        // ── STAGE 2: VALIDATE ──────────────────────────────────
        stage('Validate') {
            steps {
                script {
                    def manager = new DeploymentManager(this)
                    manager.validateConfig(
                        params.SERVICE,
                        params.ENVIRONMENT,
                        params.VERSION
                    )
                }
            }
        }

        // ── STAGE 3: DEPLOY TO DEV ─────────────────────────────
        stage('Deploy to Dev') {
            when {
                expression { return params.ENVIRONMENT == 'dev' }
            }
            steps {
                script {
                    new DeploymentManager(this).deploy(
                        params.SERVICE,
                        'dev',
                        params.VERSION
                    )
                }
            }
        }

        // ── STAGE 4: DEPLOY TO STAGING ─────────────────────────
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
                        params.SERVICE,
                        'staging',
                        params.VERSION
                    )
                }
            }
        }

        // ── STAGE 5: APPROVAL FOR PROD ─────────────────────────
        stage('Approval for Prod') {
            when {
                expression { return params.ENVIRONMENT == 'prod' }
            }
            steps {
                script {
                    // Approval se pehle notify karo
                    def notifier = new NotificationManager(this)
                    def details  = getBuildDetails(this)
                    details.changes = "Waiting for PROD approval"

                    notifier.sendSlack('UNSTABLE', details)
                    notifier.sendEmail('UNSTABLE', details)
                }

                timeout(time: 30, unit: 'MINUTES') {
                    input(
                        message: 'Deploy to PRODUCTION?',
                        ok: 'Yes, Deploy'
                    )
                }
            }
        }

        // ── STAGE 6: DEPLOY TO PROD ────────────────────────────
        stage('Deploy to Prod') {
            when {
                expression { return params.ENVIRONMENT == 'prod' }
            }
            steps {
                script {
                    new DeploymentManager(this).deploy(
                        params.SERVICE,
                        'prod',
                        params.VERSION
                    )
                }
            }
        }
    }

    // ── POST BLOCKS ───────────────────────────────────────────
    post {

        // Hamesha chalega — success ho ya failure
        always {
            script {
                echo "Pipeline finished — sending final notification"
            }
        }

        // Sirf success pe
        success {
            script {
                def notifier = new NotificationManager(this)
                def details  = getBuildDetails(this)

                // Master/main branch pe extra notification
                if (env.BRANCH_NAME == 'master' ||
                    env.BRANCH_NAME == 'main') {
                    details.changes = details.changes +
                        " | MASTER BRANCH DEPLOY"
                }

                notifier.notifyAll('SUCCESS', details)
            }
        }

        // Sirf failure pe
        failure {
            script {
                def notifier = new NotificationManager(this)
                def details  = getBuildDetails(this)

                // Rollback trigger karo
                try {
                    new DeploymentManager(this).rollback(
                        params.SERVICE,
                        params.ENVIRONMENT
                    )
                    details.changes = details.changes +
                        " | AUTO-ROLLBACK TRIGGERED"
                } catch (Exception e) {
                    details.changes = details.changes +
                        " | ROLLBACK FAILED: ${e.message}"
                }

                notifier.notifyAll('FAILURE', details)
            }
        }

        // Unstable build pe (test failures)
        unstable {
            script {
                def notifier = new NotificationManager(this)
                def details  = getBuildDetails(this)
                details.changes = details.changes +
                    " | BUILD UNSTABLE - CHECK TESTS"

                notifier.notifyAll('UNSTABLE', details)
            }
        }

        // Cleanup
        cleanup {
            cleanWs()
        }
    }
}

// ── HELPER FUNCTION — BUILD DETAILS ───────────────────────────
def getBuildDetails(def ctx) {
    // Git changes lo
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
        jobName    : ctx.env.JOB_NAME      ?: 'Unknown Job',
        buildNumber: ctx.env.BUILD_NUMBER  ?: '0',
        buildUrl   : ctx.env.BUILD_URL     ?: 'http://localhost:8080',
        branch     : ctx.env.GIT_BRANCH    ?: 'master',
        service    : ctx.params.SERVICE    ?: 'unknown',
        version    : ctx.params.VERSION    ?: '0.0.0',
        environment: ctx.params.ENVIRONMENT ?: 'unknown',
        duration   : ctx.currentBuild.durationString ?: 'N/A',
        changes    : changes,
        recipients : ctx.params.RECIPIENTS ?: 'YOUR_EMAIL@gmail.com'
    ]
}