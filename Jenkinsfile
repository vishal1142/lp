pipeline {
    agent any

    stages {
        stage('Git Checkout') {
            steps {
                script {
                    // Custom shared library call to checkout Git repo
                    gitCheckout(
                        branch: 'main',
                        url: 'https://github.com/vishal1142/lp.git'
                    )
                }
            }
        }
    }
}
