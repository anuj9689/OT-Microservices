@Library('jenkins-shared-library@main') _

import org.example.DeploymentManager

pipeline {
    agent any

    parameters {
        choice(name: 'SERVICE',
               choices: ['attendance','employee','salary','frontend','notification'],
               description: 'Which microservice to deploy')
        string(name: 'VERSION',
               defaultValue: '1.0.0',
               description: 'Semver version e.g. 1.0.0')
        choice(name: 'ENVIRONMENT',
               choices: ['dev','staging','prod'],
               description: 'Target environment')
    }

    stages {

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

        stage('Deploy to Dev') {
            when { expression { params.ENVIRONMENT == 'dev' } }
            steps {
                script {
                    new DeploymentManager(this).deploy(
                        params.SERVICE, 'dev', params.VERSION)
                }
            }
        }

        stage('Deploy to Staging') {
            when {
                anyOf {
                    expression { params.ENVIRONMENT == 'staging' }
                    expression { params.ENVIRONMENT == 'prod' }
                }
            }
            steps {
                script {
                    new DeploymentManager(this).deploy(
                        params.SERVICE, 'staging', params.VERSION)
                }
            }
        }

        stage('Approval for Prod') {
            when { expression { params.ENVIRONMENT == 'prod' } }
            steps {
                timeout(time: 30, unit: 'MINUTES') {
                    input message: "Deploy ${params.SERVICE} v${params.VERSION} to PROD?",
                          ok: 'Yes, Deploy'
                }
            }
        }

        stage('Deploy to Prod') {
            when { expression { params.ENVIRONMENT == 'prod' } }
            steps {
                script {
                    new DeploymentManager(this).deploy(
                        params.SERVICE, 'prod', params.VERSION)
                }
            }
        }
    }

    post {
        failure {
            script {
                echo "Pipeline failed — triggering rollback"
                new DeploymentManager(this).rollback(
                    params.SERVICE, params.ENVIRONMENT)
            }
        }
        success {
            echo "Done: ${params.SERVICE} v${params.VERSION} on ${params.ENVIRONMENT}"
        }
    }
}