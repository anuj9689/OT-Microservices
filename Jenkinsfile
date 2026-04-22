@Library('jenkins-shared-library@main') _

import org.example.DeploymentManager

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
    }

    stages {

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

        stage('Deploy to Dev') {
            when {
                expression {
                    return params.ENVIRONMENT == 'dev'
                }
            }
            steps {
                script {
                    def manager = new DeploymentManager(this)
                    manager.deploy(
                        params.SERVICE,
                        'dev',
                        params.VERSION
                    )
                }
            }
        }

        stage('Deploy to Staging') {
            when {
                anyOf {
                    expression { return params.ENVIRONMENT == 'staging' }
                    expression { return params.ENVIRONMENT == 'prod' }
                }
            }
            steps {
                script {
                    def manager = new DeploymentManager(this)
                    manager.deploy(
                        params.SERVICE,
                        'staging',
                        params.VERSION
                    )
                }
            }
        }

        stage('Approval for Prod') {
            when {
                expression {
                    return params.ENVIRONMENT == 'prod'
                }
            }
            steps {
                timeout(time: 30, unit: 'MINUTES') {
                    input(
                        message: 'Deploy to PRODUCTION?',
                        ok: 'Yes, Deploy'
                    )
                }
            }
        }

        stage('Deploy to Prod') {
            when {
                expression {
                    return params.ENVIRONMENT == 'prod'
                }
            }
            steps {
                script {
                    def manager = new DeploymentManager(this)
                    manager.deploy(
                        params.SERVICE,
                        'prod',
                        params.VERSION
                    )
                }
            }
        }
    }

    post {
        success {
            echo "SUCCESS: ${params.SERVICE} v${params.VERSION} deployed to ${params.ENVIRONMENT}"
        }
        failure {
            script {
                echo "FAILED: Triggering rollback for ${params.SERVICE} on ${params.ENVIRONMENT}"
                def manager = new DeploymentManager(this)
                manager.rollback(
                    params.SERVICE,
                    params.ENVIRONMENT
                )
            }
        }
    }
}