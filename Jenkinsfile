@Library('jenkinslibrary') _

pipeline {
    agent any

    stages {
        stage('Git Checkout') {
            steps {
                script {
                    gitCheckout(
                        branch: 'main',
                        url: 'https://github.com/vishal1142/lp.git'
                    )
                }
            }
        }

        stage('Unit Test Maven') {
            steps {
                script {
                    mvnTest()
                }
            }
        }
    }
}       

    post {
        always {
            script {
                echo 'This will always run'
            }
        }
        success {
            script {
                echo 'This will run only if the pipeline is successful'
            }
        }
        failure {
            script {
                echo 'This will run only if the pipeline fails'
            }
        }
    }
}