@Library('jenkins-shared-library@main') _
import org.example.DeploymentManager

pipeline {
    agent any

    triggers {
        GenericTrigger(
            genericVariables: [
                [key: 'GIT_REF',     value: '$.ref'],
                [key: 'GIT_COMMIT',  value: '$.after'],
                [key: 'SERVICE',     value: '$.repository.name'],
                [key: 'ENVIRONMENT', value: '$.ref',
                 regexpFilter: 'refs/heads/(dev|staging|master)',
                 defaultValue: 'dev']
            ],
            token: 'ot-microservices-token',
            causeString: 'Auto trigger: $GIT_REF',

            // Sirf dev, staging, master branch pe trigger ho
            regexpFilterText:       '$GIT_REF',
            regexpFilterExpression: 'refs/heads/(dev|staging|master)'
        )
    }

    environment {
        // Branch se environment decide hoga automatically
        ENVIRONMENT = "${
            env.GIT_REF?.contains('master') ? 'prod' :
            env.GIT_REF?.contains('staging') ? 'staging' : 'dev'
        }"
        SERVICE = 'attendance'   // ya GitHub repo name se aayega
        VERSION = "${env.GIT_COMMIT?.take(7) ?: '1.0.0'}"
    }

    stages {

        stage('Validate') {
            steps {
                script {
                    echo "Service    : ${env.SERVICE}"
                    echo "Version    : ${env.VERSION}"
                    echo "Environment: ${env.ENVIRONMENT}"

                    new DeploymentManager(this).validateConfig(
                        env.SERVICE,
                        env.ENVIRONMENT,
                        env.VERSION
                    )
                }
            }
        }

        stage('Deploy to Dev') {
            when { expression { env.ENVIRONMENT == 'dev' } }
            steps {
                script {
                    new DeploymentManager(this).deploy(
                        env.SERVICE, 'dev', env.VERSION)
                }
            }
        }

        stage('Deploy to Staging') {
            when {
                anyOf {
                    expression { env.ENVIRONMENT == 'staging' }
                    expression { env.ENVIRONMENT == 'prod' }
                }
            }
            steps {
                script {
                    new DeploymentManager(this).deploy(
                        env.SERVICE, 'staging', env.VERSION)
                }
            }
        }

        stage('Approval for Prod') {
            when { expression { env.ENVIRONMENT == 'prod' } }
            steps {
                timeout(time: 30, unit: 'MINUTES') {
                    input message: "Deploy ${env.SERVICE} v${env.VERSION} to PROD?",
                          ok: 'Yes, Deploy'
                }
            }
        }

        stage('Deploy to Prod') {
            when { expression { env.ENVIRONMENT == 'prod' } }
            steps {
                script {
                    new DeploymentManager(this).deploy(
                        env.SERVICE, 'prod', env.VERSION)
                }
            }
        }
    }

    post {
        failure {
            script {
                echo "Pipeline failed — triggering rollback"
                new DeploymentManager(this).rollback(
                    env.SERVICE, env.ENVIRONMENT)
            }
        }
        success {
            echo "Done: ${env.SERVICE} v${env.VERSION} on ${env.ENVIRONMENT}"
        }
    }
}

addd