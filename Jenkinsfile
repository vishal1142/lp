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
    }
}
